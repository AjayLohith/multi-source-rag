from typing import Any, Callable, Type
import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

# Transient errors suitable for automatic backoff & retry
TRANSIENT_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.RemoteProtocolError,
    ConnectionError,
    TimeoutError,
)


def with_retry(
    max_attempts: int = 3,
    min_wait: float = 0.5,
    max_wait: float = 5.0,
):
    """Decorator to retry flaky IO operations with exponential backoff."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(TRANSIENT_EXCEPTIONS),
        reraise=True,
    )
