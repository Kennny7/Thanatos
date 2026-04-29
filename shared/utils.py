# Thanatos/shared/utils.py
import socket
import asyncio
import logging
from typing import Callable, Any, Optional
from .logging_setup import ensure_logging

ensure_logging()
logger = logging.getLogger(__name__)


async def retry_async(
    func: Callable,
    *args,
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,),
    **kwargs
) -> Any:
    """
    Retry an asynchronous function with exponential backoff.

    Args:
        func: Async function to call.
        max_retries: Maximum number of retry attempts.
        delay: Initial delay between retries in seconds.
        exceptions: Tuple of exceptions to catch and retry.
        *args, **kwargs: Arguments passed to the function.

    Returns:
        The function's return value if successful.

    Raises:
        The last exception if all retries fail.
    """
    logger.debug(
        "retry_async started | func=%s | max_retries=%d | delay=%.2f",
        getattr(func, "__name__", str(func)),
        max_retries,
        delay
    )

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            logger.debug(
                "Attempt %d/%d for function %s",
                attempt + 1,
                max_retries + 1,
                getattr(func, "__name__", str(func))
            )

            result = await func(*args, **kwargs)

            if attempt > 0:
                logger.info(
                    "Function %s succeeded after %d retries",
                    getattr(func, "__name__", str(func)),
                    attempt
                )
            else:
                logger.debug(
                    "Function %s succeeded on first attempt",
                    getattr(func, "__name__", str(func))
                )

            return result

        except exceptions as e:
            last_exception = e

            if attempt < max_retries:
                wait_time = delay * (2 ** attempt)  # exponential backoff

                logger.warning(
                    "Attempt %d/%d failed for %s | error=%s | retrying in %.2fs",
                    attempt + 1,
                    max_retries + 1,
                    getattr(func, "__name__", str(func)),
                    str(e),
                    wait_time
                )

                await asyncio.sleep(wait_time)

            else:
                logger.error(
                    "All %d attempts failed for %s",
                    max_retries + 1,
                    getattr(func, "__name__", str(func)),
                    exc_info=True
                )
                raise last_exception

    raise last_exception  # fallback


def resolve_llm_base_url(
    base_url: str | None = None,
    default_local: str = "http://localhost:8001/v1",   # FIXED (was 11434)
    default_docker: str = "http://local-llm:8001/v1"   # FIXED (was ollama:11434)
) -> str:
    """
    Resolve LLM base URL depending on environment (no env vars).

    Priority:
    1. Explicit base_url argument
    2. Docker network (if 'ollama' resolves)
    3. Localhost fallback
    """
    if base_url:
        logger.debug("Using explicit LLM base_url: %s", base_url)
        return base_url

    # Docker detection
    try:
        socket.gethostbyname("ollama")
        logger.info("Resolved LLM base_url via Docker network: %s", default_docker)
        return default_docker
    except socket.error:
        logger.info("Falling back to local LLM base_url: %s", default_local)
        return default_local