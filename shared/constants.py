# Static defaults – no environment reads
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0

# Model default (static)
DEFAULT_MODEL = "phi3:latest" #"mistral:7b-instruct"

# Provider default (static, used only by existing code that imports it)
DEFAULT_PROVIDER = "ollama"

# Legacy names kept for backward compatibility (static)
DEEPSEEK_API_BASE_URL = None #"http://ollama:11434/v1"
DEEPSEEK_API_KEY = None
LLM_BASE_URL = None
DEEPSEEK_CHAT_MODEL = DEFAULT_MODEL