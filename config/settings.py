# Thanatos/config/settings.py

import os
from typing import Optional
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """
    Central configuration for the entire Thanatos project.

    All values have sensible defaults and can be overridden via
    environment variables or a `.env` file in the project root.
    Environment variable names match the field names in UPPER_CASE
    (e.g. ``llm_model`` -> ``LLM_MODEL``).
    """

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    app_name: str = "Thanatos AI"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    websocket_heartbeat_interval: int = 15

    # ------------------------------------------------------------------ #
    # LLM - Local (Ollama)
    # ------------------------------------------------------------------ #
    llm_provider: str = "ollama"
    llm_model: str = "qwen2.5:7b"
    llm_base_url: str = "http://localhost:11434"
    llm_base_url_docker: str = "http://ollama:11434"
    llm_adapter_url: str = "http://localhost:8001/v1"
    llm_adapter_url_docker: str = "http://local-llm:8001/v1"
    llm_temperature: float = 0.1
    llm_max_retries: int = 3
    llm_retry_delay: float = 1.0

    # ------------------------------------------------------------------ #
    # LLM - Cloud (DeepSeek / OpenAI)
    # ------------------------------------------------------------------ #
    deepseek_api_key: Optional[str] = None
    deepseek_api_base_url: str = "https://api.deepseek.com"
    deepseek_chat_model: str = "deepseek-chat"
    openai_api_key: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Memory / ChromaDB
    # ------------------------------------------------------------------ #
    memory_persist_dir: str = "./memory_store"
    memory_collection: str = "thanatos_memories"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_device: str = "cpu"

    # ------------------------------------------------------------------ #
    # User Profile Defaults
    # ------------------------------------------------------------------ #
    user_name: str = "User"
    user_email: str = "user@example.com"
    user_location: str = ""
    user_title: str = ""

    # ------------------------------------------------------------------ #
    # Voice / Speech
    # ------------------------------------------------------------------ #
    tts_voice: str = "en-US-AriaNeural"
    stt_model: str = "base"
    stt_device: str = "cpu"
    stt_compute_type: str = "int8"
    speaker_enrollment_dir: str = "./voice_profiles"

    # ------------------------------------------------------------------ #
    # Logging
    # ------------------------------------------------------------------ #
    log_dir: str = "logs"
    log_config_path: str = "config/logging.conf"

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


# Singleton instance - import this everywhere
app_config = AppConfig()
