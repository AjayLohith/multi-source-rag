import random


def calculate_backoff(
    attempt: int,
    base: float = 0.5,
    factor: float = 2.0,
    max_backoff: float = 10.0,
    jitter: bool = True,
) -> float:
    """Calculates exponential backoff with optional random jitter."""
    delay = min(base * (factor ** attempt), max_backoff)
    if jitter:
        delay = delay * (0.5 + random.random() * 0.5)
    return max(0.1, delay)
