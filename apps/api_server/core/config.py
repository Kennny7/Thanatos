# Thanatos/apps/api_server/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""
    app_name: str = "Thanatos API Server"
    debug: bool = False
    websocket_heartbeat_interval: int = 15

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()