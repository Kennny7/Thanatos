# Thanatos/services/llm_brain/deepseek_planner.py

import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Literal, Union

import openai
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from config.settings import app_config

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Type aliases for clarity
# --------------------------------------------------------------------------- #
ToolSchema = List[Dict[str, Any]]           # list of tool definitions
History = List[ChatCompletionMessageParam]  # conversation history

PlanOutput = Dict[str, Any]                 # {'action': 'tool_call', ...} or {'action': 'respond', ...}
# --------------------------------------------------------------------------- #

class DeepSeekPlanner:
    """
    LLM‑based planner that decides whether to call an external tool or
    respond directly to the user.

    Uses the DeepSeek API via the OpenAI SDK, with automatic retries for
    transient errors and malformed JSON in tool‑call arguments.
    """

    def __init__(
        self,
        model: str = app_config.deepseek_chat_model,
        api_key: Optional[str] = None,
        base_url: str = app_config.deepseek_api_base_url,
        max_retries: int = app_config.llm_max_retries,
    ) -> None:
        """
        Parameters
        ----------
        model : str
            DeepSeek model identifier (default ``"deepseek-chat"``).
        api_key : str or None
            API key. If ``None``, reads from environment variable
            ``DEEPSEEK_API_KEY``.
        base_url : str
            Base URL for the API endpoint.
        max_retries : int
            Maximum number of retries for JSON‑parsing failures when
            extracting tool‑call arguments.
        """
        self.model = model
        self.base_url = base_url
        self.max_retries = max_retries

        # Resolve API key – prefer explicit, then env var
        resolved_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not resolved_key:
            raise ValueError(
                "DeepSeek API key not provided. Set DEEPSEEK_API_KEY "
                "environment variable or pass api_key explicitly."
            )

        # Async client (reuse for all requests)
        self._client = AsyncOpenAI(
            api_key=resolved_key,
            base_url=self.base_url,
        )

    async def plan(
        self,
        history: History,
        tools_schema: ToolSchema,
    ) -> PlanOutput:
        """
        Send the conversation history and tool definitions to the LLM,
        parse the response and return a structured decision.

        Parameters
        ----------
        history : list of message dicts
            The full conversation history, including system, user,
            assistant, and tool messages. Must follow OpenAI chat format.
        tools_schema : list of tool definition dicts
            Available tools in OpenAI function‑calling format, e.g.
            ``[{"type": "function", "function": {...}}, ...]``.

        Returns
        -------
        dict
            Either ``{'action': 'tool_call', 'tool_name': ..., 'args': ...}``
            or ``{'action': 'respond', 'text': ...}``.
        """
        # Convert the generic schema into typed ToolParam objects
        tools: List[ChatCompletionToolParam] = [
            ChatCompletionToolParam(**tool) for tool in tools_schema
        ]

        # Inner function that performs a single API call + parsing attempt.
        # Wrapped with tenacity for retry on specific failures.
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(
                (json.JSONDecodeError, openai.APIError, openai.APITimeoutError)
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )
        async def _make_request() -> PlanOutput:
            try:
                response = await self._client.chat.completions.create(
                    model=self.model,
                    messages=history,
                    tools=tools,
                    # We want the LLM to either return a tool_call or a
                    # plain content message; never do parallel tool calls.
                    tool_choice="auto",
                    temperature=0.0,  # deterministic planning
                )
            except (openai.APIError, openai.APITimeoutError) as exc:
                logger.warning("OpenAI API error: %s. Retrying...", exc)
                raise  # triggers tenacity retry
            except Exception as exc:
                logger.exception("Unexpected error during API call.")
                # Let the caller decide how to handle
                raise RuntimeError("Planner API call failed") from exc

            choice = response.choices[0]
            message = choice.message

            # If a tool call is requested, parse its arguments
            if message.tool_calls:
                # DeepSeek (like OpenAI) returns a list of tool_calls;
                # we take the first one.
                tool_call = message.tool_calls[0]
                tool_name = tool_call.function.name

                # The arguments come as a JSON string – try to parse
                raw_args = tool_call.function.arguments
                try:
                    parsed_args = json.loads(raw_args)
                except json.JSONDecodeError as exc:
                    logger.warning(
                        "Failed to parse tool-call arguments: %s",
                        raw_args,
                    )
                    raise  # triggers tenacity retry

                return {
                    "action": "tool_call",
                    "tool_name": tool_name,
                    "args": parsed_args,
                }

            # Otherwise treat as a plain text response
            if message.content:
                return {
                    "action": "respond",
                    "text": message.content,
                }

            # Fallback: no content and no tool_calls – very rare
            logger.warning("Received empty message from LLM.")
            return {
                "action": "respond",
                "text": "",
            }

        # Execute the retry‑decorated function
        try:
            return await _make_request()
        except Exception as exc:
            logger.error("All retries exhausted. Planner failed.")
            raise RuntimeError(
                "DeepSeekPlanner failed after multiple retries"
            ) from exc