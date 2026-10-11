from typing import Any, Dict, Optional
from app.contracts import FailureRecord, PipelineStage
from app.database.repository import Repository
from app.database.session import SessionLocal


def send_to_dead_letter(
    job_id: str,
    source_id: str,
    stage: PipelineStage,
    error_code: str,
    error_message: str,
    document_id: Optional[str] = None,
    raw_payload: Optional[Dict[str, Any]] = None,
) -> FailureRecord:
    """Persists unrecoverable failure details to durable dead-letter storage."""
    failure = FailureRecord(
        job_id=job_id,
        source_id=source_id,
        document_id=document_id,
        stage=stage,
        error_code=error_code,
        error_message=error_message,
        raw_payload=raw_payload or {},
    )
    with SessionLocal() as session:
        repo = Repository(session)
        repo.record_failure(failure)
    return failure
