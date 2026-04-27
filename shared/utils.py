# Thanatos/shared/utils.py

import asyncio
import logging
from typing import Callable, Any, Optional

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
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = delay * (2 ** attempt)  # exponential backoff
                logger.warning(
                    f"Attempt {attempt + 1} failed with error: {e}. "
                    f"Retrying in {wait_time:.2f}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {max_retries + 1} attempts failed.")
                raise last_exception
    raise last_exception  # fallback