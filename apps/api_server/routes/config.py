# Thanatos/apps/api_server/routes/config.py

import json
import logging
import os
import platform
import psutil
from typing import Any, AsyncGenerator, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import httpx
from pydantic import BaseModel

from shared.settings import runtime_settings, Settings
from services.llm_brain.provider import UnifiedLLMProvider
from services.local_llm.ollama_client import OllamaClient
from services.memory.hybrid_memory_service import hybrid_memory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/config", tags=["Configuration"])

llm_provider = UnifiedLLMProvider(runtime_settings)
ollama_client = OllamaClient()


class ConfigUpdateRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = None
    api_key: Optional[str] = None
    assistant_name: Optional[str] = None
    user_name: Optional[str] = None


class OllamaPullRequest(BaseModel):
    model: str


class RecommendRequest(BaseModel):
    task_type: Optional[str] = "general"  # general, coding, reasoning, creative, fast_dialogue


@router.get("")
async def get_current_config() -> Dict[str, Any]:
    """Return active server, LLM model configuration, and assistant identity."""
    return {
        "provider": runtime_settings.provider,
        "model": runtime_settings.model,
        "base_url": runtime_settings.base_url,
        "temperature": runtime_settings.temperature,
        "is_local": runtime_settings.is_local,
        "supports_tools": runtime_settings.supports_tools,
        "assistant_name": hybrid_memory.profile.assistant_name,
        "user_name": hybrid_memory.profile.name,
    }


@router.post("/llm")
async def update_llm_config(payload: ConfigUpdateRequest) -> Dict[str, Any]:
    """Dynamically switch active LLM model, provider, endpoint, or persona."""
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
    if payload.assistant_name:
        hybrid_memory.profile.assistant_name = payload.assistant_name
        hybrid_memory.save_profile()
    if payload.user_name:
        hybrid_memory.profile.name = payload.user_name
        hybrid_memory.save_profile()

    runtime_settings.is_local = any(
        loc in runtime_settings.base_url for loc in ("localhost", "127.0.0.1", "ollama", "local-llm")
    )
    llm_provider.update_settings(runtime_settings)

    logger.info("Updated active model config: %s (%s)", runtime_settings.model, runtime_settings.provider)
    return {
        "status": "success",
        "message": f"Active configuration updated.",
        "config": {
            "provider": runtime_settings.provider,
            "model": runtime_settings.model,
            "base_url": runtime_settings.base_url,
            "temperature": runtime_settings.temperature,
            "is_local": runtime_settings.is_local,
            "assistant_name": hybrid_memory.profile.assistant_name,
            "user_name": hybrid_memory.profile.name,
        }
    }


@router.get("/models")
async def list_available_models() -> Dict[str, Any]:
    """List available local Ollama models and cloud models dynamically."""
    models = await llm_provider.list_available_models()
    return {
        "active_model": runtime_settings.model,
        "active_provider": runtime_settings.provider,
        "models": models,
    }


@router.get("/ollama/tags")
async def get_ollama_tags() -> Dict[str, Any]:
    """Directly query Ollama daemon for currently installed models."""
    base_url = runtime_settings.base_url.replace("/v1", "")
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(f"{base_url}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {"status": "ok", "models": models, "raw": data.get("models", [])}
    except Exception as e:
        logger.warning("Failed querying Ollama tags directly: %s", e)
    return {"status": "offline", "models": ["qwen2.5:7b", "llama3.1:8b", "deepseek-r1:7b", "phi3:latest"]}


@router.post("/ollama/pull")
async def pull_ollama_model(payload: OllamaPullRequest):
    """Stream pulling a model from Ollama library with live progress."""
    base_url = runtime_settings.base_url.replace("/v1", "")

    async def generate_pull_stream() -> AsyncGenerator[str, None]:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(1200.0, connect=10.0)) as client:
                async with client.stream("POST", f"{base_url}/api/pull", json={"name": payload.model, "stream": True}) as response:
                    async for line in response.aiter_lines():
                        if line:
                            yield f"data: {line}\n\n"
        except Exception as e:
            err_json = json.dumps({"status": "error", "error": str(e)})
            yield f"data: {err_json}\n\n"

    return StreamingResponse(generate_pull_stream(), media_type="text/event-stream")


@router.get("/hardware-spec")
async def get_hardware_specs() -> Dict[str, Any]:
    """Detect host CPU, RAM, OS, and GPU/VRAM for intelligent model recommendations."""
    ram = psutil.virtual_memory()
    total_ram_gb = round(ram.total / (1024 ** 3), 1)
    avail_ram_gb = round(ram.available / (1024 ** 3), 1)

    gpu_info = []
    has_nvidia = False
    try:
        import torch
        if torch.cuda.is_available():
            has_nvidia = True
            for i in range(torch.cuda.device_count()):
                dev_name = torch.cuda.get_device_name(i)
                vram_gb = round(torch.cuda.get_device_properties(i).total_memory / (1024 ** 3), 1)
                gpu_info.append({"id": i, "name": dev_name, "vram_gb": vram_gb})
    except Exception:
        pass

    return {
        "os": platform.system(),
        "platform": platform.platform(),
        "cpu_count": psutil.cpu_count(logical=True),
        "total_ram_gb": total_ram_gb,
        "available_ram_gb": avail_ram_gb,
        "has_gpu": has_nvidia,
        "gpus": gpu_info,
    }


@router.post("/recommend-model")
async def recommend_model(payload: RecommendRequest) -> Dict[str, Any]:
    """
    Intelligent hardware & task-aware heuristic model selector.
    Chooses the optimal model for the host resources and task, requiring user confirmation.
    """
    hw = await get_hardware_specs()
    avail_ram = hw["available_ram_gb"]
    vram = hw["gpus"][0]["vram_gb"] if hw["has_gpu"] and hw["gpus"] else 0.0
    task = (payload.task_type or "general").lower()

    recommended_model = "qwen2.5:7b"
    reason = "Balanced performance and high reasoning density."
    needs_confirmation = True

    if task in ["coding", "code", "refactoring"]:
        if vram >= 16 or avail_ram >= 24:
            recommended_model = "qwen2.5-coder:14b"
            reason = "High RAM/VRAM detected; 14B coder gives state-of-the-art code generation."
        elif vram >= 8 or avail_ram >= 12:
            recommended_model = "qwen2.5-coder:7b"
            reason = "Optimal balance of latency and AST-accurate code syntax."
        else:
            recommended_model = "deepseek-coder:6.7b"
            reason = "Compact footprint suited for constrained hardware."
    elif task in ["reasoning", "math", "deep_thinking"]:
        if vram >= 18 or avail_ram >= 28:
            recommended_model = "deepseek-r1:14b"
            reason = "Exceptional step-by-step reasoning with chain-of-thought verification."
        else:
            recommended_model = "deepseek-r1:7b"
            reason = "Fast chain-of-thought reasoning that fits within 8GB VRAM/RAM."
    elif task in ["fast_dialogue", "chat", "voice"]:
        if avail_ram < 8 and vram < 6:
            recommended_model = "phi3:mini"
            reason = "Ultra-fast response latency ideal for conversational voice interaction."
        else:
            recommended_model = "llama3.2:3b"
            reason = "High conversational fluency with low compute latency."
    else:  # General
        if vram >= 14 or avail_ram >= 20:
            recommended_model = "llama3.1:8b"
            reason = "Broad world knowledge, strong instruction following, fits comfortably in available resources."
        else:
            recommended_model = "qwen2.5:7b"
            reason = "Versatile multilingual generalist running efficiently on standard hardware."

    return {
        "task_type": task,
        "recommended_model": recommended_model,
        "reason": reason,
        "hardware_detected": {
            "ram_gb": avail_ram,
            "vram_gb": vram,
            "has_gpu": hw["has_gpu"],
        },
        "prompt_user_confirmation": needs_confirmation,
        "confirmation_message": f"Based on your {task} task and hardware ({avail_ram}GB RAM, {vram}GB VRAM), '{recommended_model}' is recommended. Would you like to switch to it?"
    }
