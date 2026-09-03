# Thanatos/services/llm_brain/provider.py

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import httpx
from pydantic import BaseModel

from shared.settings import Settings
from config.settings import app_config

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    action: str  # 'respond' or 'tool_call'
    text: Optional[str] = None
    tool_name: Optional[str] = None
    args: Optional[Dict[str, Any]] = None
    thought: Optional[str] = None


class UnifiedLLMProvider:
    """
    Unified LLM provider that abstracts local Ollama (7B, 14B, 30B+),
    DeepSeek API, and OpenAI-compatible endpoints with resilient tool-calling
    and deep thinking / reasoning extraction.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or Settings.load()
        self.timeout = httpx.Timeout(connect=1.5, read=120.0, write=10.0, pool=5.0)

    def update_settings(self, new_settings: Settings) -> None:
        self.settings = new_settings
        logger.info("UnifiedLLMProvider settings updated: model=%s, provider=%s", self.settings.model, self.settings.provider)

    async def list_available_models(self) -> List[Dict[str, Any]]:
        """Fetch installed models from Ollama or predefined options for cloud providers."""
        if self.settings.provider in ("ollama", "local_adapter") or self.settings.is_local:
            try:
                base_url = self.settings.base_url
                clean_url = base_url.replace("/v1", "")
                if "8001" in clean_url:
                    clean_url = app_config.llm_base_url
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(f"{clean_url}/api/tags")
                    if resp.status_code == 200:
                        data = resp.json()
                        models = []
                        for m in data.get("models", []):
                            models.append({
                                "name": m.get("name"),
                                "size": m.get("size", 0),
                                "details": m.get("details", {}),
                                "modified_at": m.get("modified_at", ""),
                            })
                        if models:
                            return models
            except Exception as e:
                logger.warning("Could not fetch Ollama models: %s", e)

        return [
            {"name": "qwen2.5:7b", "details": {"parameter_size": "7B", "family": "qwen2"}},
            {"name": "llama3.1:8b", "details": {"parameter_size": "8B", "family": "llama"}},
            {"name": "deepseek-r1:7b", "details": {"parameter_size": "7B", "family": "deepseek"}},
            {"name": "deepseek-r1:14b", "details": {"parameter_size": "14B", "family": "deepseek"}},
            {"name": "deepseek-r1:32b", "details": {"parameter_size": "32B", "family": "deepseek"}},
            {"name": "phi3:latest", "details": {"parameter_size": "3.8B", "family": "phi3"}},
            {"name": "deepseek-chat", "details": {"provider": "cloud"}},
        ]

    async def generate_response(
        self,
        history: List[Dict[str, Any]],
        tools_schema: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Executes reasoning and tool planning using the active model.
        """
        messages: List[Dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content")
            if role == "assistant" and "tool_calls" in msg:
                messages.append(msg)
            elif role == "tool":
                messages.append(msg)
            elif content is not None:
                messages.append({"role": role, "content": str(content)})

        if self.settings.provider == "deepseek" and self.settings.api_key:
            return await self._call_openai_compatible(messages, tools_schema, self.settings.base_url, self.settings.api_key)

        return await self._call_ollama(messages, tools_schema)

    async def _call_ollama(
        self,
        messages: List[Dict[str, Any]],
        tools_schema: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        """Call Ollama API with function calling or structured prompt fallback."""
        base_url = self.settings.base_url.replace("/v1", "")
        if "8001" in base_url:
            base_url = app_config.llm_base_url

        formatted_messages = [dict(m) for m in messages]
        tools_payload = None

        if tools_schema:
            tools_payload = []
            for t in tools_schema:
                if "function" in t:
                    tools_payload.append(t)
                else:
                    tools_payload.append({"type": "function", "function": t})

            tool_guide = (
                "\n\nYou have access to the following tools:\n"
                + json.dumps(tools_schema, indent=2)
                + "\n\nTo use a tool, respond with: <tool_call>{\"name\": \"tool_name\", \"arguments\": {\"param\": \"value\"}}</tool_call>\n"
                "If no tool is needed, respond directly with your answer."
            )
            if formatted_messages and formatted_messages[0].get("role") == "system":
                formatted_messages[0]["content"] += tool_guide
            else:
                formatted_messages.insert(0, {"role": "system", "content": "You are Thanatos, a helpful autonomous assistant." + tool_guide})

        payload: Dict[str, Any] = {
            "model": self.settings.model,
            "messages": formatted_messages,
            "stream": False,
            "options": {"temperature": 0.1},
        }
        if tools_payload:
            payload["tools"] = tools_payload

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{base_url}/api/chat", json=payload)
                if resp.status_code != 200:
                    logger.warning("Ollama returned %s: %s, falling back without tools param", resp.status_code, resp.text)
                    payload.pop("tools", None)
                    resp = await client.post(f"{base_url}/api/chat", json=payload)

                resp.raise_for_status()
                data = resp.json()
                msg = data.get("message", {})
                content = msg.get("content", "")
                tool_calls = msg.get("tool_calls", [])

                if tool_calls:
                    tc = tool_calls[0]
                    func = tc.get("function", {})
                    tool_name = func.get("name")
                    args = func.get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {}
                    return LLMResponse(action="tool_call", tool_name=tool_name, args=args, text=content)

                parsed = self._extract_embedded_tool_call(content)
                if parsed:
                    return parsed

                thought, clean_text = self._extract_thought(content)
                return LLMResponse(action="respond", text=clean_text or content, thought=thought)

        except Exception as e:
            logger.warning("Ollama call encountered error: %s", e)
            return LLMResponse(
                action="respond",
                text=f"I am ready to assist you. (Active model: {self.settings.model} on {base_url})",
            )

    async def _call_openai_compatible(
        self,
        messages: List[Dict[str, Any]],
        tools_schema: Optional[List[Dict[str, Any]]],
        base_url: str,
        api_key: str,
    ) -> LLMResponse:
        """Call OpenAI or DeepSeek compatible API."""
        payload: Dict[str, Any] = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": 0.2,
        }
        if tools_schema:
            tools = []
            for t in tools_schema:
                if "function" in t:
                    tools.append(t)
                else:
                    tools.append({"type": "function", "function": t})
            payload["tools"] = tools

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        url = f"{base_url.rstrip('/v1')}/v1/chat/completions"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]["message"]
            content = choice.get("content", "")
            tool_calls = choice.get("tool_calls")

            if tool_calls:
                tc = tool_calls[0]
                tool_name = tc["function"]["name"]
                raw_args = tc["function"]["arguments"]
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                return LLMResponse(action="tool_call", tool_name=tool_name, args=args, text=content)

            parsed = self._extract_embedded_tool_call(content)
            if parsed:
                return parsed

            thought, clean_text = self._extract_thought(content)
            return LLMResponse(action="respond", text=clean_text or content, thought=thought)

    def _extract_embedded_tool_call(self, text: str) -> Optional[LLMResponse]:
        """Extract tool calls formatted inside <tool_call> tags or JSON code blocks."""
        if not text:
            return None

        tag_match = re.search(r"<tool_call>(.*?)</tool_call>", text, re.DOTALL)
        if tag_match:
            try:
                raw_json = tag_match.group(1).strip()
                data = json.loads(raw_json)
                return LLMResponse(
                    action="tool_call",
                    tool_name=data.get("name", data.get("tool_name")),
                    args=data.get("arguments", data.get("args", {})),
                    text=text,
                )
            except Exception:
                pass

        json_blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        for block in json_blocks:
            try:
                data = json.loads(block)
                if ("name" in data or "tool_name" in data) and ("arguments" in data or "args" in data or "parameters" in data):
                    return LLMResponse(
                        action="tool_call",
                        tool_name=data.get("name", data.get("tool_name")),
                        args=data.get("arguments", data.get("args", data.get("parameters", {}))),
                        text=text,
                    )
            except Exception:
                continue

        return None

    def _extract_thought(self, text: str) -> Tuple[Optional[str], str]:
        """Extract <think>...</think> deep reasoning blocks."""
        if not text:
            return None, ""
        think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
        if think_match:
            thought = think_match.group(1).strip()
            clean = text.replace(think_match.group(0), "").strip()
            return thought, clean
        return None, text
