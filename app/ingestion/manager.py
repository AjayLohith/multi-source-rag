import asyncio
from typing import Optional
from app.contracts import IngestionJob, SourceDescriptor
from app.database.repository import Repository
from app.database.session import SessionLocal
from app.ingestion.pipeline import execute_ingestion_pipeline


class IngestionManager:
    """Manages job creation, background dispatch, and status retrieval."""

    def submit_job(self, descriptor: SourceDescriptor) -> IngestionJob:
        with SessionLocal() as session:
            repo = Repository(session)
            job = repo.create_job(source_id=descriptor.source_id)

        # Trigger background processing task
        asyncio.create_task(self._run_async_job(descriptor, job.job_id))
        return job

    async def _run_async_job(self, descriptor: SourceDescriptor, job_id: str) -> None:
        try:
            await execute_ingestion_pipeline(descriptor, job_id=job_id)
        except Exception:
            pass

    def get_job_status(self, job_id: str) -> Optional[IngestionJob]:
        with SessionLocal() as session:
            repo = Repository(session)
            return repo.get_job(job_id)


default_ingestion_manager = IngestionManager()
