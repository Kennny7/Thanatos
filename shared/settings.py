# Thanatos/shared/settings.py

"""
Centralised LLM configuration.
Reads environment variables once and exposes a deterministic Settings object.
"""
import os
import socket
import logging
from typing import Optional
from shared.logging_setup import ensure_logging

ensure_logging()

logger = logging.getLogger(__name__)

# Local detection helper (no env reading)
def _detect_base_url(
    default_local: str = "http://localhost:8001/v1",
    default_docker: str = "http://local-llm:8001/v1"  # route via adapter, not raw Ollama
) -> str:
    """Detect whether we're inside a Docker network."""
    logger.debug("Detecting base URL via network resolution")

    try:
        socket.gethostbyname("ollama")
        logger.debug("Detected Docker environment (ollama hostname resolved)")
        return default_docker
    except socket.error:
        logger.debug("Falling back to local environment (ollama hostname not found)")
        return default_local


class Settings:
    """Immutable settings object populated from environment."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str],
        model: str,
        provider: str,
        is_local: bool,
        supports_tools: bool,  # NEW
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self.is_local = is_local
        self.supports_tools = supports_tools  # NEW

    @classmethod
    def load(cls) -> "Settings":
        logger.info("Loading Settings configuration")

        # 1. Base URL resolution
        env_base_url = os.getenv("LLM_BASE_URL")
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")

        if env_base_url:
            base_url = env_base_url
            logger.debug("Using LLM_BASE_URL from environment: %s", base_url)
        elif deepseek_key:
            base_url = "https://api.deepseek.com/v1"
            logger.debug("DeepSeek API key detected, using cloud endpoint")
        else:
            base_url = _detect_base_url()
            logger.debug("Auto-detected base URL: %s", base_url)

        # 2. Determine local vs cloud
        is_local = any(local in base_url for local in ("localhost", "ollama", "local-llm"))

        # Provider classification (more precise, backward compatible)
        if "deepseek" in base_url:
            provider = "deepseek"
        elif "8001" in base_url:
            provider = "local_adapter"
        elif "11434" in base_url or "ollama" in base_url:
            provider = "ollama"
        else:
            provider = "unknown"

        logger.debug(
            "Provider resolution | is_local=%s | provider=%s",
            is_local,
            provider
        )

        # Tool capability detection (NEW)
        supports_tools = provider in ("deepseek", "local_adapter")

        # 3. API key
        if is_local:
            api_key = "ollama"  # dummy, Ollama doesn't require auth
            logger.debug("Using local provider, assigning dummy API key")
        else:
            api_key = deepseek_key  # may be None → caller must validate
            if api_key:
                logger.debug("Using provided DeepSeek API key")
            else:
                logger.warning("DeepSeek provider selected but API key is missing")

        # 4. Model (keep backward-compatible env name)
        model = os.getenv("LLM_MODEL", "phi3:latest")
        logger.debug("Model selected: %s", model)

        settings = cls(
            base_url=base_url,
            api_key=api_key,
            model=model,
            provider=provider,
            is_local=is_local,
            supports_tools=supports_tools,  # NEW
        )

        logger.info(
            "Settings loaded | provider=%s | model=%s | base_url=%s | tools=%s",
            settings.provider,
            settings.model,
            settings.base_url,
            settings.supports_tools
        )

        return settings

    def __repr__(self) -> str:
        return (
            f"Settings(base_url={self.base_url}, provider={self.provider}, "
            f"model={self.model}, is_local={self.is_local})"
        )