import asyncio
from typing import Dict
from app.config import settings


class ConcurrencyManager:
    """Maintains bounded semaphores per source to prevent I/O saturation."""

    def __init__(self, max_concurrency: int = 4):
        self.max_concurrency = max_concurrency
        self.semaphores: Dict[str, asyncio.Semaphore] = {}
        self._lock = asyncio.Lock()

    async def get_semaphore(self, source_id: str) -> asyncio.Semaphore:
        async with self._lock:
            if source_id not in self.semaphores:
                self.semaphores[source_id] = asyncio.Semaphore(self.max_concurrency)
            return self.semaphores[source_id]


default_concurrency_manager = ConcurrencyManager(
    max_concurrency=settings.worker_concurrency
)
