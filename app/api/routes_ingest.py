from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.contracts import SourceDescriptor, SourceType
from app.database.repository import Repository
from app.database.session import SessionLocal
from app.ingestion.pipeline import execute_ingestion_pipeline

router = APIRouter(prefix="", tags=["Ingestion"])


class IngestRequest(BaseModel):
    source_type: SourceType
    name: str
    config: Dict[str, Any]


@router.post("/ingest")
async def ingest_source(payload: IngestRequest):
    """
    Submits a new data source for ingestion across the pipeline:
    fetch -> extract -> normalize -> deduplicate -> chunk -> embed -> upsert
    """
    descriptor = SourceDescriptor(
        source_type=payload.source_type,
        name=payload.name,
        config=payload.config,
    )
    try:
        result = await execute_ingestion_pipeline(descriptor)
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": str(exc), "source": payload.name},
        )


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Returns durable status and timings for a specific ingestion job."""
    with SessionLocal() as session:
        repo = Repository(session)
        job = repo.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job.model_dump()
