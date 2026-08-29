# Thanatos/config/settings.py

import os
from typing import Optional
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    app_name: str = "Thanatos AI"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # LLM Settings
    llm_provider: str = "ollama"
    llm_model: str = "qwen2.5:7b"
    llm_base_url: str = "http://localhost:11434"
    llm_temperature: float = 0.1
    deepseek_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Memory Settings
    memory_persist_dir: str = "./memory_store"
    memory_collection: str = "thanatos_memories"
    
    # Voice Settings
    tts_voice: str = "en-US-AriaNeural"
    stt_model: str = "base"
    speaker_enrollment_dir: str = "./voice_profiles"

    class Config:
        env_file = ".env"
        extra = "ignore"


app_config = AppConfig()
