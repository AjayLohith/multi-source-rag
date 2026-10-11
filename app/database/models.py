from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DocumentModel(Base):
    __tablename__ = "documents"

    document_id = Column(String(64), primary_key=True)
    source_type = Column(String(32), nullable=False)
    source_id = Column(String(64), nullable=False, index=True)
    source_name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    metadata_json = Column(JSON, default=dict)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class IngestionJobModel(Base):
    __tablename__ = "ingestion_jobs"

    job_id = Column(String(64), primary_key=True)
    source_id = Column(String(64), nullable=False, index=True)
    document_id = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    attempt = Column(Integer, default=0)
    error_code = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class SourceConnectionModel(Base):
    __tablename__ = "source_connections"

    source_id = Column(String(64), primary_key=True)
    source_type = Column(String(32), nullable=False)
    name = Column(String(255), nullable=False)
    config_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class FailedDocumentModel(Base):
    __tablename__ = "failed_documents"

    failure_id = Column(String(64), primary_key=True)
    job_id = Column(String(64), nullable=False, index=True)
    source_id = Column(String(64), nullable=False)
    document_id = Column(String(64), nullable=True)
    stage = Column(String(32), nullable=False)
    error_code = Column(String(64), nullable=False)
    error_message = Column(Text, nullable=False)
    raw_payload_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class SchemaVersionModel(Base):
    __tablename__ = "schema_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String(32), nullable=False)
    schema_hash = Column(String(64), nullable=False, index=True)
    fields_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
