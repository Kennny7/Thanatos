# Thanatos\shared\deepseek_planner.py
import json
import logging
from typing import List, Dict, Any, Optional

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageToolCall

from .settings import Settings
from .constants import DEFAULT_MAX_RETRIES, DEFAULT_RETRY_DELAY
from .utils import retry_async
from .logging_setup import ensure_logging

ensure_logging()

logger = logging.getLogger(__name__)


class DeepSeekPlanner:
    """
    Async planner that uses an OpenAI-compatible API to decide between
    responding directly or calling a tool.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ):
        """
        Initialize the planner.

        Args:
            settings: Pre-configured Settings object. If None, loaded from env.
            max_retries: Maximum number of retry attempts on API/parsing errors.
            retry_delay: Base delay between retries in seconds.
        """
        logger.debug("Initializing DeepSeekPlanner")

        resolved_settings = settings or Settings.load()

        # Store settings for capability checks (NEW)
        self.settings = resolved_settings

        # Validate cloud API key
        if (not resolved_settings.is_local) and not resolved_settings.api_key:
            logger.critical("Missing API key for cloud provider")
            raise ValueError(
                "API key required for cloud provider. "
                "Set DEEPSEEK_API_KEY or pass explicitly."
            )

        # OpenAI-compatible client
        self.client = AsyncOpenAI(
            api_key=resolved_settings.api_key,
            base_url=resolved_settings.base_url,
        )

        self.model = resolved_settings.model
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        logger.info(
            "DeepSeekPlanner initialised | model=%s | base_url=%s | retries=%d",
            self.model,
            resolved_settings.base_url,
            self.max_retries
        )

    async def plan(
        self,
        history: List[Dict[str, str]],
        tools_schema: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a plan: either respond directly or call a tool.

        Returns:
            Dict with keys:
                - 'action': 'respond' | 'tool_call'
                - 'text' (if respond)
                - 'tool_name', 'args' (if tool_call)
        """
        logger.debug(
            "Planning started | history_len=%d | tools_available=%d",
            len(history),
            len(tools_schema)
        )

        async def _make_request():
            logger.debug(
                "Sending request to LLM | model=%s | supports_tools=%s",
                self.model,
                self.settings.supports_tools
            )

            # Build request dynamically based on capability (NEW)
            kwargs = {
                "model": self.model,
                "messages": history,
                "temperature": 0.0,  # deterministic planning
            }

            if self.settings.supports_tools:
                kwargs["tools"] = tools_schema
                logger.debug("Attaching tools to request")
            else:
                logger.debug("Skipping tools (model does not support tools)")

            response = await self.client.chat.completions.create(**kwargs)

            logger.debug("Received response from LLM")
            return response

        try:
            response = await retry_async(
                _make_request,
                max_retries=self.max_retries,
                delay=self.retry_delay,
                exceptions=(Exception,)
            )
        except Exception:
            logger.exception("LLM request failed after retries")
            raise

        message = response.choices[0].message

        if message.tool_calls:
            tool_call: ChatCompletionMessageToolCall = message.tool_calls[0]
            tool_name = tool_call.function.name

            logger.info("LLM decided to call tool | tool_name=%s", tool_name)

            try:
                args = await self._parse_tool_arguments(tool_call.function.arguments)
            except Exception:
                logger.exception("Tool argument parsing failed | tool_name=%s", tool_name)
                raise

            logger.debug(
                "Tool call parsed successfully | tool_name=%s | args_keys=%s",
                tool_name,
                list(args.keys()) if isinstance(args, dict) else "non-dict"
            )

            return {
                "action": "tool_call",
                "tool_name": tool_name,
                "args": args
            }
        else:
            response_text = message.content or ""

            logger.info("LLM returned direct response | length=%d", len(response_text))
            logger.debug("Response preview: %s", response_text[:200])

            return {
                "action": "respond",
                "text": response_text
            }

    async def _parse_tool_arguments(self, arguments_str: str) -> Dict[str, Any]:
        """Parse JSON arguments with retry on malformed JSON."""
        logger.debug("Parsing tool arguments")

        async def _parse():
            return json.loads(arguments_str)

        try:
            parsed = await retry_async(
                _parse,
                max_retries=self.max_retries,
                delay=self.retry_delay,
                exceptions=(json.JSONDecodeError,)
            )

            logger.debug("Tool arguments parsed successfully")
            return parsed

        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse tool arguments after retries | raw=%s",
                arguments_str
            )
            raise ValueError(f"Invalid JSON in tool arguments: {arguments_str}") from e