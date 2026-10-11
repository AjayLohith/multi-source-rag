from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.contracts import (
    DocumentRecord,
    FailureRecord,
    IngestionJob,
    JobStatus,
    PipelineStage,
    SourceDescriptor,
    SourceType,
)
from app.database.models import (
    DocumentModel,
    FailedDocumentModel,
    IngestionJobModel,
    SchemaVersionModel,
    SourceConnectionModel,
)


class Repository:
    def __init__(self, session: Session):
        self.session = session

    # ── Documents ──────────────────────────────────────────────────────────

    def save_document(self, doc: DocumentRecord) -> DocumentRecord:
        existing = (
            self.session.query(DocumentModel)
            .filter(DocumentModel.document_id == doc.document_id)
            .first()
        )
        if existing:
            existing.title = doc.title
            existing.content = doc.content
            existing.content_hash = doc.content_hash
            existing.metadata_json = doc.metadata
            existing.version = doc.version
            existing.updated_at = datetime.now(timezone.utc)
        else:
            db_doc = DocumentModel(
                document_id=doc.document_id,
                source_type=doc.source_type.value,
                source_id=doc.source_id,
                source_name=doc.source_name,
                title=doc.title,
                content=doc.content,
                content_hash=doc.content_hash,
                metadata_json=doc.metadata,
                version=doc.version,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
            )
            self.session.add(db_doc)
        self.session.commit()
        return doc

    def get_document_by_id(self, document_id: str) -> Optional[DocumentRecord]:
        row = (
            self.session.query(DocumentModel)
            .filter(DocumentModel.document_id == document_id)
            .first()
        )
        if not row:
            return None
        return DocumentRecord(
            document_id=row.document_id,
            source_type=SourceType(row.source_type),
            source_id=row.source_id,
            source_name=row.source_name,
            title=row.title,
            content=row.content,
            metadata=row.metadata_json or {},
            content_hash=row.content_hash,
            version=row.version,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def get_document_by_hash(self, content_hash: str) -> Optional[DocumentRecord]:
        row = (
            self.session.query(DocumentModel)
            .filter(DocumentModel.content_hash == content_hash)
            .first()
        )
        if not row:
            return None
        return DocumentRecord(
            document_id=row.document_id,
            source_type=SourceType(row.source_type),
            source_id=row.source_id,
            source_name=row.source_name,
            title=row.title,
            content=row.content,
            metadata=row.metadata_json or {},
            content_hash=row.content_hash,
            version=row.version,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ── Jobs ───────────────────────────────────────────────────────────────

    def create_job(self, source_id: str, document_id: Optional[str] = None) -> IngestionJob:
        job = IngestionJob(source_id=source_id, document_id=document_id)
        db_job = IngestionJobModel(
            job_id=job.job_id,
            source_id=job.source_id,
            document_id=job.document_id,
            status=job.status.value,
            attempt=job.attempt,
            created_at=job.created_at,
        )
        self.session.add(db_job)
        self.session.commit()
        return job

    def update_job(self, job: IngestionJob) -> IngestionJob:
        row = (
            self.session.query(IngestionJobModel)
            .filter(IngestionJobModel.job_id == job.job_id)
            .first()
        )
        if row:
            row.status = job.status.value
            row.attempt = job.attempt
            row.document_id = job.document_id
            row.error_code = job.error_code
            row.error_message = job.error_message
            row.started_at = job.started_at
            row.completed_at = job.completed_at
            self.session.commit()
        return job

    def get_job(self, job_id: str) -> Optional[IngestionJob]:
        row = (
            self.session.query(IngestionJobModel)
            .filter(IngestionJobModel.job_id == job_id)
            .first()
        )
        if not row:
            return None
        return IngestionJob(
            job_id=row.job_id,
            source_id=row.source_id,
            document_id=row.document_id,
            status=JobStatus(row.status),
            attempt=row.attempt,
            error_code=row.error_code,
            error_message=row.error_message,
            created_at=row.created_at,
            started_at=row.started_at,
            completed_at=row.completed_at,
        )

    # ── Failures (Dead Letter) ─────────────────────────────────────────────

    def record_failure(self, failure: FailureRecord) -> FailureRecord:
        db_fail = FailedDocumentModel(
            failure_id=failure.failure_id,
            job_id=failure.job_id,
            source_id=failure.source_id,
            document_id=failure.document_id,
            stage=failure.stage.value,
            error_code=failure.error_code,
            error_message=failure.error_message,
            raw_payload_json=failure.raw_payload,
            created_at=failure.created_at,
        )
        self.session.add(db_fail)
        self.session.commit()
        return failure

    # ── Schema Versions ───────────────────────────────────────────────────

    def record_schema_version(self, source_type: str, schema_hash: str, fields: Dict[str, Any]) -> None:
        existing = (
            self.session.query(SchemaVersionModel)
            .filter(
                SchemaVersionModel.source_type == source_type,
                SchemaVersionModel.schema_hash == schema_hash,
            )
            .first()
        )
        if not existing:
            self.session.add(
                SchemaVersionModel(
                    source_type=source_type,
                    schema_hash=schema_hash,
                    fields_json=fields,
                )
            )
            self.session.commit()
