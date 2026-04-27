# Thanatos/shared/constants.py
import os

DEEPSEEK_API_BASE_URL = os.getenv(
    "LLM_BASE_URL",
    "http://ollama:11434/v1"
)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

DEEPSEEK_CHAT_MODEL = os.getenv(
    "LLM_MODEL",
    "mistral:7b-instruct"
)

DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")


# Running on host machine http://localhost:11434
# Running on docker compose http://ollama:11434
# Running on proxy mode "http://local-llm:8001/v1"

# If you are treating ollama as openai, use http://ollama:11434/v1