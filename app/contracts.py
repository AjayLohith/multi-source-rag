"""
Canonical data contracts for the pipeline: fetch -> extract -> normalize ->
validate -> chunk -> hash -> embed -> upsert -> complete (see architecture.md).

These contracts are frozen to ensure every layer (adapters, workers,
normalizers, vectorstore, LLM) interacts through standardized DTOs.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid4())


# ── Enums ─────────────────────────────────────────────────────────────────

class SourceType(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    SQL = "sql"
    WEB = "web"
    API = "api"
    DOCX = "docx"
    JSON = "json"
    TEXT = "text"
    MD = "md"


class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    COMPLETED = "completed"
    RETRYING = "retrying"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    DEAD_LETTERED = "dead_lettered"
    SKIPPED_DUPLICATE = "skipped_duplicate"


class PipelineStage(str, Enum):
    FETCH = "fetch"
    EXTRACT = "extract"
    NORMALIZE = "normalize"
    VALIDATE = "validate"
    CHUNK = "chunk"
    HASH = "hash"
    EMBED = "embed"
    UPSERT = "upsert"


# ── Canonical Contracts ───────────────────────────────────────────────────

class SourceDescriptor(BaseModel):
    """Describes a configured source (folder, table, url, or api)."""
    source_id: str = Field(default_factory=_new_id)
    source_type: SourceType
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)


class RawDocument(BaseModel):
    """Unprocessed output straight from a source adapter."""
    source_id: str
    source_type: SourceType
    raw_content: str
    content_type: str = "text/plain"
    fetched_at: datetime = Field(default_factory=_utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentRecord(BaseModel):
    """The canonical, normalized document ready for chunking and hashing."""
    document_id: str = Field(default_factory=_new_id)
    source_type: SourceType
    source_id: str
    source_name: str
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content_hash: str
    version: int = 1
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class ChunkRecord(BaseModel):
    """A single chunk of a DocumentRecord, ready for embedding."""
    chunk_id: str = Field(default_factory=_new_id)
    document_id: str
    chunk_index: int
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IngestionJob(BaseModel):
    """Tracks a document/source job's progress through the pipeline."""
    job_id: str = Field(default_factory=_new_id)
    source_id: str
    document_id: Optional[str] = None
    status: JobStatus = JobStatus.PENDING
    attempt: int = 0
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class FailureRecord(BaseModel):
    """A durable dead-letter record capturing error context."""
    failure_id: str = Field(default_factory=_new_id)
    job_id: str
    source_id: str
    document_id: Optional[str] = None
    stage: PipelineStage
    error_code: str
    error_message: str
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)
