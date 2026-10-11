import asyncio
import logging
from typing import Optional
from app.contracts import SourceDescriptor
from app.ingestion.pipeline import execute_ingestion_pipeline

logger = logging.getLogger("ingestion.worker")


class IngestionWorker:
    """Worker handling asynchronous background job execution."""

    def __init__(self, queue: Optional[asyncio.Queue] = None):
        self.queue = queue or asyncio.Queue()
        self._running = False

    async def enqueue(self, descriptor: SourceDescriptor, job_id: str) -> None:
        await self.queue.put((descriptor, job_id))

    async def run_loop(self) -> None:
        self._running = True
        while self._running:
            try:
                descriptor, job_id = await self.queue.get()
                await execute_ingestion_pipeline(descriptor, job_id=job_id)
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Worker execution failed: {exc}")

    def stop(self) -> None:
        self._running = False
