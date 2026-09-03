# Thanatos/apps/api_server/core/config.py

from config.settings import app_config


class Settings:
    """Application settings loaded from the central AppConfig."""
    app_name: str = app_config.app_name
    debug: bool = app_config.debug
    websocket_heartbeat_interval: int = app_config.websocket_heartbeat_interval


settings = Settings()