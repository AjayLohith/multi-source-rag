from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import logging

from app.contracts import (
    DocumentRecord,
    IngestionJob,
    JobStatus,
    PipelineStage,
    SourceDescriptor,
    SourceType,
)
from app.database.repository import Repository
from app.database.session import SessionLocal
from app.normalization.normalizer import normalize_document
from app.chunking.chunker import chunk_document
from app.embeddings.model import default_embedding_model
from app.vectorstore.qdrant import default_vector_store
from app.resilience.dead_letter import send_to_dead_letter
from app.sources import (
    PDFSource,
    CSVSource,
    SQLSource,
    TextSource,
    MarkdownSource,
    JSONSource,
    DocSource,
    WebSource,
    APISource,
)

logger = logging.getLogger("ingestion.pipeline")


def get_adapter_for_source(desc: SourceDescriptor):
    """Factory resolving appropriate SourceAdapter instance for descriptor."""
    adapters = {
        SourceType.PDF: PDFSource,
        SourceType.CSV: CSVSource,
        SourceType.SQL: SQLSource,
        SourceType.TEXT: TextSource,
        SourceType.MD: MarkdownSource,
        SourceType.JSON: JSONSource,
        SourceType.DOCX: DocSource,
        SourceType.WEB: WebSource,
        SourceType.API: APISource,
    }
    adapter_cls = adapters.get(desc.source_type)
    if not adapter_cls:
        raise ValueError(f"Unsupported source type: {desc.source_type}")
    return adapter_cls(desc)


async def execute_ingestion_pipeline(
    descriptor: SourceDescriptor,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes the end-to-end ingestion pipeline:
    fetch -> extract -> normalize -> deduplicate -> chunk -> embed -> upsert
    """
    with SessionLocal() as session:
        repo = Repository(session)
        job = repo.get_job(job_id) if job_id else repo.create_job(descriptor.source_id)
        job.status = JobStatus.IN_PROGRESS
        job.started_at = datetime.now(timezone.utc)
        job.attempt += 1
        repo.update_job(job)

    current_stage = PipelineStage.FETCH
    processed_docs: List[DocumentRecord] = []
    skipped_duplicates = 0
    total_chunks_upserted = 0

    try:
        current_stage = PipelineStage.FETCH
        adapter = get_adapter_for_source(descriptor)
        adapter.validate()

        current_stage = PipelineStage.EXTRACT
        raw_documents = [doc async for doc in adapter.fetch()]

        with SessionLocal() as session:
            repo = Repository(session)

            for raw_doc in raw_documents:
                current_stage = PipelineStage.NORMALIZE
                doc = normalize_document(raw_doc, source_name=descriptor.name)

                # Deduplication check
                current_stage = PipelineStage.HASH
                existing_doc = repo.get_document_by_hash(doc.content_hash)
                if existing_doc:
                    # Unchanged content: skip embedding/upsert
                    skipped_duplicates += 1
                    continue

                # Content is new or modified: persist document record
                current_stage = PipelineStage.VALIDATE
                repo.save_document(doc)
                processed_docs.append(doc)

                # Chunking stage
                current_stage = PipelineStage.CHUNK
                chunks = chunk_document(doc)

                # Embedding stage
                current_stage = PipelineStage.EMBED
                texts = [c.content for c in chunks]
                embeddings = default_embedding_model.embed_documents(texts)

                # Upsert stage
                current_stage = PipelineStage.UPSERT
                upserted = default_vector_store.upsert_chunks(chunks, embeddings)
                total_chunks_upserted += upserted

        # Complete job
        with SessionLocal() as session:
            repo = Repository(session)
            job = repo.get_job(job.job_id)
            if job:
                job.status = (
                    JobStatus.SKIPPED_DUPLICATE
                    if (skipped_duplicates > 0 and len(processed_docs) == 0)
                    else JobStatus.COMPLETED
                )
                job.completed_at = datetime.now(timezone.utc)
                repo.update_job(job)

        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "processed_documents": len(processed_docs),
            "skipped_duplicates": skipped_duplicates,
            "chunks_upserted": total_chunks_upserted,
        }

    except Exception as exc:
        error_msg = str(exc)
        error_code = getattr(exc, "error_code", "INGESTION_PIPELINE_ERROR")

        # Record durable dead letter failure
        send_to_dead_letter(
            job_id=job.job_id,
            source_id=descriptor.source_id,
            stage=current_stage,
            error_code=error_code,
            error_message=error_msg,
            raw_payload=descriptor.config,
        )

        with SessionLocal() as session:
            repo = Repository(session)
            db_job = repo.get_job(job.job_id)
            if db_job:
                db_job.status = JobStatus.FAILED
                db_job.error_code = error_code
                db_job.error_message = error_msg
                db_job.completed_at = datetime.now(timezone.utc)
                repo.update_job(db_job)

        raise
