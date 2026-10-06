# Thanatos/services/llm_brain/model_selector.py
"""
Targeted Model & SLM Selection Agent.
Evaluates agent tasks, hardware resource constraints (RAM, VRAM, GPU),
and automatically selects or pulls targeted SLMs <= 8-9B parameter models
(e.g., qwen2.5:3b, qwen2.5:7b, phi3:mini, llama3.2:3b, deepseek-r1:7b) via Ollama.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from config.settings import app_config

logger = logging.getLogger(__name__)

# Curated catalog of high-performing SLMs under 9B parameter threshold
SLM_CATALOG = {
    "router": {
        "model": "qwen2.5:3b",
        "size_gb": 2.0,
        "description": "Ultra-fast intent classifier and task decomposition router",
    },
    "reasoning": {
        "model": "deepseek-r1:7b",
        "size_gb": 4.7,
        "description": "High-impact deep mathematical & architectural reasoning with think tags",
    },
    "coding": {
        "model": "qwen2.5:7b",
        "size_gb": 4.7,
        "description": "Code synthesis, LaTeX parsing, and tool-calling execution",
    },
    "creative": {
        "model": "mistral:7b",
        "size_gb": 4.1,
        "description": "Creative writing, novel translation, and conversational tone",
    },
    "reader": {
        "model": "phi3:mini",
        "size_gb": 2.3,
        "description": "Fast comprehension, long context reading, and text summarization",
    },
    "compact": {
        "model": "llama3.2:3b",
        "size_gb": 2.0,
        "description": "Low-footprint general assistant suitable for lightweight secondary nodes",
    },
}


class ModelSelectorAgent:
    """
    Evaluates agent workload needs, inspects local and remote Ollama instances,
    and automatically pulls and provisions targeted SLMs when needed.
    """

    def __init__(self, max_parameter_limit_billions: float = 9.0) -> None:
        self.max_parameter_limit = max_parameter_limit_billions
        self.base_url = app_config.llm_base_url.rstrip("/")

    async def get_installed_models(self, endpoint: Optional[str] = None) -> List[str]:
        """Fetch list of models already pulled on the target Ollama instance."""
        url = (endpoint or self.base_url).rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(f"{url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    return [m.get("name", "").split(":")[0] for m in data.get("models", [])]
        except Exception as e:
            logger.warning("Could not query Ollama at %s: %s", url, e)
        return []

    def recommend_slm(self, role: str) -> Dict[str, Any]:
        """Recommend optimal SLM <= 9B for a specific agent role."""
        role_lower = role.lower()
        if any(k in role_lower for k in ["code", "latex", "resume", "developer", "tool"]):
            return SLM_CATALOG["coding"]
        elif any(k in role_lower for k in ["math", "reason", "plan", "audit"]):
            return SLM_CATALOG["reasoning"]
        elif any(k in role_lower for k in ["read", "doc", "summary", "article"]):
            return SLM_CATALOG["reader"]
        elif any(k in role_lower for k in ["chat", "companion", "friendly", "novel", "creative"]):
            return SLM_CATALOG["creative"]
        elif any(k in role_lower for k in ["route", "classify", "gate"]):
            return SLM_CATALOG["router"]
        return SLM_CATALOG["compact"]

    async def ensure_model_available(self, model_name: str, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify if model is present. If missing, automatically pull it via Ollama.
        """
        url = (endpoint or self.base_url).rstrip("/")
        installed = await self.get_installed_models(url)
        clean_name = model_name.split(":")[0]

        if any(clean_name in m for m in installed):
            return {"status": "available", "model": model_name, "pulled": False}

        logger.info("Targeted SLM '%s' not present on %s. Initiating autonomous pull...", model_name, url)
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                resp = await client.post(
                    f"{url}/api/pull",
                    json={"name": model_name, "stream": False},
                )
                if resp.status_code == 200:
                    logger.info("Successfully pulled SLM '%s' on %s.", model_name, url)
                    return {"status": "available", "model": model_name, "pulled": True}
                else:
                    return {"status": "error", "error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            logger.exception("Failed pulling SLM %s: %s", model_name, e)
            return {"status": "error", "error": str(e)}


model_selector = ModelSelectorAgent()
