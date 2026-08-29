# Thanatos/apps/api_server/routes/config.py

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.settings import runtime_settings, Settings
from services.llm_brain.provider import UnifiedLLMProvider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/config", tags=["Configuration"])

llm_provider = UnifiedLLMProvider(runtime_settings)


class ConfigUpdateRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = None
    api_key: Optional[str] = None


@router.get("")
async def get_current_config() -> Dict[str, Any]:
    """Return active server and LLM model configuration."""
    return {
        "provider": runtime_settings.provider,
        "model": runtime_settings.model,
        "base_url": runtime_settings.base_url,
        "temperature": runtime_settings.temperature,
        "is_local": runtime_settings.is_local,
        "supports_tools": runtime_settings.supports_tools,
    }


@router.post("/llm")
async def update_llm_config(payload: ConfigUpdateRequest) -> Dict[str, Any]:
    """Dynamically switch active LLM model, provider, or endpoint."""
    global runtime_settings, llm_provider

    if payload.provider:
        runtime_settings.provider = payload.provider
    if payload.model:
        runtime_settings.model = payload.model
    if payload.base_url:
        runtime_settings.base_url = payload.base_url
    if payload.temperature is not None:
        runtime_settings.temperature = payload.temperature
    if payload.api_key is not None:
        runtime_settings.api_key = payload.api_key

    runtime_settings.is_local = any(
        loc in runtime_settings.base_url for loc in ("localhost", "127.0.0.1", "ollama", "local-llm")
    )
    llm_provider.update_settings(runtime_settings)

    logger.info("Updated active model config: %s (%s)", runtime_settings.model, runtime_settings.provider)
    return {
        "status": "success",
        "message": f"Active model updated to {runtime_settings.model}",
        "config": {
            "provider": runtime_settings.provider,
            "model": runtime_settings.model,
            "base_url": runtime_settings.base_url,
            "temperature": runtime_settings.temperature,
            "is_local": runtime_settings.is_local,
        }
    }


@router.get("/models")
async def list_available_models() -> Dict[str, Any]:
    """List available local Ollama models and cloud models."""
    models = await llm_provider.list_available_models()
    return {
        "active_model": runtime_settings.model,
        "active_provider": runtime_settings.provider,
        "models": models,
    }
