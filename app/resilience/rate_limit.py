import asyncio
import time
from typing import Dict


class RateLimiter:
    """Per-source token bucket rate limiter to prevent upstream flooding."""

    def __init__(self, requests_per_minute: int = 60):
        self.rate = requests_per_minute / 60.0
        self.capacity = float(requests_per_minute)
        self.tokens: Dict[str, float] = {}
        self.last_check: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, source_key: str) -> None:
        async with self._lock:
            now = time.monotonic()
            if source_key not in self.tokens:
                self.tokens[source_key] = self.capacity
                self.last_check[source_key] = now

            elapsed = now - self.last_check[source_key]
            self.last_check[source_key] = now
            self.tokens[source_key] = min(self.capacity, self.tokens[source_key] + elapsed * self.rate)

            if self.tokens[source_key] < 1.0:
                wait_time = (1.0 - self.tokens[source_key]) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens[source_key] = 0.0
            else:
                self.tokens[source_key] -= 1.0


default_rate_limiter = RateLimiter(requests_per_minute=60)
