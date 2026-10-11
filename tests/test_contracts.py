from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from app.contracts import (
    SourceDescriptor,
    RawDocument,
    DocumentRecord,
    ChunkRecord,
    IngestionJob,
    FailureRecord,
    SourceType,
    JobStatus,
    PipelineStage,
)


def test_source_descriptor_creation():
    desc = SourceDescriptor(
        source_type=SourceType.PDF,
        name="test-pdfs",
        config={"path": "data/raw/pdf"},
    )
    assert desc.source_id is not None
    assert desc.source_type == SourceType.PDF
    assert desc.name == "test-pdfs"
    assert desc.config["path"] == "data/raw/pdf"
    assert isinstance(desc.created_at, datetime)


def test_raw_document_creation():
    raw = RawDocument(
        source_id="src-123",
        source_type=SourceType.CSV,
        raw_content="col1: val1\ncol2: val2",
        metadata={"row_index": 0},
    )
    assert raw.source_id == "src-123"
    assert raw.source_type == SourceType.CSV
    assert raw.raw_content == "col1: val1\ncol2: val2"
    assert raw.content_type == "text/plain"
    assert raw.metadata["row_index"] == 0
    assert isinstance(raw.fetched_at, datetime)


def test_document_record_creation():
    doc = DocumentRecord(
        source_type=SourceType.SQL,
        source_id="src-sql",
        source_name="employees",
        title="Employee Record",
        content="id: 1, name: Alice",
        content_hash="abc123hash",
    )
    assert doc.document_id is not None
    assert doc.version == 1
    assert doc.source_name == "employees"
    assert isinstance(doc.created_at, datetime)
    assert isinstance(doc.updated_at, datetime)


def test_chunk_record_creation():
    chunk = ChunkRecord(
        document_id="doc-123",
        chunk_index=0,
        content="first chunk content",
        metadata={"start_char": 0, "end_char": 19},
    )
    assert chunk.chunk_id is not None
    assert chunk.document_id == "doc-123"
    assert chunk.chunk_index == 0
    assert chunk.embedding is None
    assert chunk.metadata["start_char"] == 0


def test_ingestion_job_lifecycle():
    job = IngestionJob(source_id="src-456")
    assert job.job_id is not None
    assert job.status == JobStatus.PENDING
    assert job.attempt == 0
    assert job.started_at is None
    assert job.completed_at is None


def test_failure_record_creation():
    failure = FailureRecord(
        job_id="job-999",
        source_id="src-456",
        stage=PipelineStage.EXTRACT,
        error_code="PDF_CORRUPT",
        error_message="Corrupted PDF bytes",
        raw_payload={"path": "corrupt.pdf"},
    )
    assert failure.failure_id is not None
    assert failure.stage == PipelineStage.EXTRACT
    assert failure.error_code == "PDF_CORRUPT"


def test_source_type_enum():
    assert SourceType.PDF.value == "pdf"
    assert SourceType.CSV.value == "csv"
    assert SourceType.SQL.value == "sql"
    assert SourceType.WEB.value == "web"


def test_job_status_enum():
    assert JobStatus.PENDING.value == "pending"
    assert JobStatus.IN_PROGRESS.value == "in_progress"
    assert JobStatus.COMPLETED.value == "completed"
    assert JobStatus.FAILED.value == "failed"


def test_pipeline_stage_enum():
    stages = [s.value for s in PipelineStage]
    assert "fetch" in stages
    assert "extract" in stages
    assert "normalize" in stages
    assert "chunk" in stages
