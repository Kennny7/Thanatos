# Thanatos/shared/settings.py

import os
import socket
import logging
from typing import Optional

from config.settings import app_config

logger = logging.getLogger(__name__)


def _detect_base_url(
    default_local: str = app_config.llm_base_url,
    default_docker: str = app_config.llm_base_url_docker,
) -> str:
    try:
        socket.gethostbyname("ollama")
        return default_docker
    except socket.error:
        return default_local


class Settings:
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str],
        model: str,
        provider: str,
        is_local: bool,
        supports_tools: bool = True,
        temperature: float = 0.1,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self.is_local = is_local
        self.supports_tools = supports_tools
        self.temperature = temperature

    @classmethod
    def load(cls) -> "Settings":
        env_base_url = os.getenv("LLM_BASE_URL")
        deepseek_key = app_config.deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
        openai_key = app_config.openai_api_key or os.getenv("OPENAI_API_KEY")
        model = os.getenv("LLM_MODEL", app_config.llm_model)

        if env_base_url:
            base_url = env_base_url
        elif deepseek_key:
            base_url = app_config.deepseek_api_base_url
        else:
            base_url = _detect_base_url()

        is_local = any(local in base_url for local in ("localhost", "127.0.0.1", "ollama", "local-llm"))

        if "deepseek" in base_url:
            provider = "deepseek"
            api_key = deepseek_key
        elif "openai" in base_url:
            provider = "openai"
            api_key = openai_key
        else:
            provider = "ollama"
            api_key = "ollama"

        return cls(
            base_url=base_url,
            api_key=api_key,
            model=model,
            provider=provider,
            is_local=is_local,
            supports_tools=True,
            temperature=float(os.getenv("LLM_TEMPERATURE", str(app_config.llm_temperature))),
        )

    def __repr__(self) -> str:
        return f"Settings(provider={self.provider}, model={self.model}, base_url={self.base_url}, is_local={self.is_local})"


# Global shared instance
runtime_settings = Settings.load()
