# Thanatos/services/local_llm/ollama_client.py

import logging
import httpx
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from config.settings import app_config

OLLAMA_URL = app_config.llm_base_url


class OllamaClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or OLLAMA_URL).replace("/v1", "")
        self.timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)

    async def is_healthy(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(3.0)) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.warning("Error querying Ollama models: %s", e)
        return ["qwen2.5:7b", "llama3.1:8b", "deepseek-r1:7b", "deepseek-r1:14b", "phi3:latest"]

    async def chat(self, model: str, messages: List[Dict[str, Any]], temperature: float = 0.1) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "model": model,
                "messages": messages,
                "options": {"temperature": temperature},
                "stream": False,
            }
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            return resp.json()


async def chat(model: str, messages: list, temperature: float = 0.0) -> Dict[str, Any]:
    client = OllamaClient()
    return await client.chat(model=model, messages=messages, temperature=temperature)
