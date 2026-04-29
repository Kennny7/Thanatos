# Thanatos\services\local_llm\ollama_client.py

import logging
import httpx
import os

from shared.logging_setup import ensure_logging

ensure_logging()
logger = logging.getLogger(__name__)

# Allow override via env, fallback to Docker default (backward compatible)

OLLAMA_URL = (
    os.getenv("LLM_BASE_URL", "http://ollama:11434")
)

logger.debug("OLLAMA_URL configured: %s", str(OLLAMA_URL)[:100])


async def chat(model: str, messages: list, temperature: float = 0.0):
    logger.info("Ollama chat request initiated | model=%s | messages=%d", model, len(messages))

    # Minimal safe preview (avoid huge logs)
    try:
        preview_messages = messages[-2:] if len(messages) > 2 else messages
        logger.debug("Message preview (last 2): %s", str(preview_messages)[:500])
    except Exception:
        logger.debug("Failed to generate message preview (non-critical)")

    try:
        # FIX: explicit timeout to prevent ReadTimeout on cold starts / CPU inference
        timeout = httpx.Timeout(
            connect=10.0,
            read=120.0,   
            write=10.0,
            pool=10.0
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            url = f"{OLLAMA_URL}/api/chat"
            logger.debug("Sending request to Ollama | url=%s", url)

            payload = {
                "model": model,
                "messages": messages,
                "options": {
                    "temperature": temperature
                },
                "stream": False
            }

            logger.debug("Payload keys sent to Ollama: %s", list(payload.keys()))

            response = await client.post(
                url,
                json=payload
            )

            logger.debug("Received response from Ollama | status_code=%s", response.status_code)

            if response.status_code != 200:
                logger.error(
                    "Ollama API error | status_code=%s | response=%s",
                    response.status_code,
                    response.text[:500]  # truncate to avoid log bloat
                )

            response.raise_for_status()

            data = response.json()

            logger.info("Ollama response processed successfully")
            logger.debug("Response preview: %s", str(data)[:500])

            return data

    except httpx.RequestError:
        logger.exception("Network error while communicating with Ollama")
        raise

    except httpx.HTTPStatusError:
        logger.exception("HTTP error returned from Ollama")
        raise

    except Exception:
        logger.exception("Unexpected error in Ollama client")
        raise