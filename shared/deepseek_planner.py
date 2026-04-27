# Thanatos/shared/deepseek_planner.py

import os
import json
import logging
from typing import List, Dict, Any, Optional

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageToolCall

from .constants import (
    DEEPSEEK_API_BASE_URL,
    DEEPSEEK_CHAT_MODEL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_DELAY,
    DEFAULT_PROVIDER,
    DEEPSEEK_API_KEY
)
from .utils import retry_async

logger = logging.getLogger(__name__)


class DeepSeekPlanner:
    """
    Async planner that uses DeepSeek API to decide between responding directly
    or calling a tool based on conversation history and available tools.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        provider: Optional[str] = None
    ):
        """
        Initialize the planner.

        Args:
            api_key: DeepSeek API key. If None, reads from env DEEPSEEK_API_KEY.
            base_url: API base URL.
            model: Model name to use.
            max_retries: Maximum number of retry attempts on API/parsing errors.
            retry_delay: Base delay between retries in seconds.
        """
        # Resolve defaults first
        provider = provider or DEFAULT_PROVIDER
        base_url = base_url or DEEPSEEK_API_BASE_URL
        model = model or DEEPSEEK_CHAT_MODEL

        # Store provider state
        self.is_local = provider in ["ollama", "local-llm"]
        self.provider = provider

        # Auth logic
        if self.is_local:
            self.api_key = "ollama"  # dummy
        else:
            self.api_key = api_key or DEEPSEEK_API_KEY
            if not self.api_key:
                raise ValueError(
                    "API key required for cloud provider. "
                    "Set DEEPSEEK_API_KEY or pass explicitly."
                )

        # OpenAI-compatible client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url
        )

        # Config
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def plan(
        self,
        history: List[Dict[str, str]],
        tools_schema: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a plan: either respond directly or call a tool.

        Args:
            history: List of message dicts with 'role' and 'content'.
            tools_schema: List of tool definitions in OpenAI function calling format.

        Returns:
            Dict with keys:
                - 'action': 'respond' or 'tool_call'
                - If 'respond': 'text' contains the response.
                - If 'tool_call': 'tool_name' and 'args' (dict).
        """
        async def _make_request():
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=history,
                tools=tools_schema,
                temperature=0.0,  # deterministic planning
            )
            return response

        # Retry the API call on any exception (network, timeout, etc.)
        response = await retry_async(
            _make_request,
            max_retries=self.max_retries,
            delay=self.retry_delay,
            exceptions=(Exception,)
        )

        message = response.choices[0].message

        # Check for tool calls
        if message.tool_calls:
            tool_call: ChatCompletionMessageToolCall = message.tool_calls[0]
            tool_name = tool_call.function.name

            # Parse arguments JSON with retry logic if parsing fails
            args = await self._parse_tool_arguments(tool_call.function.arguments)

            return {
                "action": "tool_call",
                "tool_name": tool_name,
                "args": args
            }
        else:
            # Plain text response
            return {
                "action": "respond",
                "text": message.content or ""
            }

    async def _parse_tool_arguments(self, arguments_str: str) -> Dict[str, Any]:
        """
        Parse the JSON arguments string from the tool call.
        Includes retry logic for malformed JSON by re-fetching (optional).
        In a real scenario, you might want to re-prompt the model.
        Here we simply retry parsing; if it fails after retries, we raise.
        """
        async def _parse():
            return json.loads(arguments_str)

        try:
            return await retry_async(
                _parse,
                max_retries=self.max_retries,
                delay=self.retry_delay,
                exceptions=(json.JSONDecodeError,)
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tool arguments after retries: {arguments_str}")
            raise ValueError(f"Invalid JSON in tool arguments: {arguments_str}") from e