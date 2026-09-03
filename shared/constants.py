# Thanatos\shared\constants.py

from config.settings import app_config

# Retry defaults
DEFAULT_MAX_RETRIES = app_config.llm_max_retries
DEFAULT_RETRY_DELAY = app_config.llm_retry_delay

# Model default
DEFAULT_MODEL = app_config.llm_model

# Provider default (used only by existing code that imports it)
DEFAULT_PROVIDER = app_config.llm_provider

# Legacy names kept for backward compatibility
DEEPSEEK_API_BASE_URL = app_config.deepseek_api_base_url
DEEPSEEK_API_KEY = app_config.deepseek_api_key
LLM_BASE_URL = app_config.llm_base_url
DEEPSEEK_CHAT_MODEL = app_config.deepseek_chat_model