import hashlib
from pathlib import Path
from typing import Optional

from app.contracts import DocumentRecord, RawDocument
from app.normalization.cleaners import clean_text
from app.normalization.schemas import normalize_record_schema


def compute_content_hash(text: str) -> str:
    """Computes a deterministic SHA-256 hex digest for document content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_document(raw_doc: RawDocument, source_name: Optional[str] = None) -> DocumentRecord:
    """
    Transforms any heterogeneous RawDocument (PDF, CSV, SQL, Web, API, etc.)
    into a single canonical DocumentRecord.

    - Cleans noise, unicode artifacts, and extra whitespace.
    - Resolves document title and source name provenance.
    - Handles schema aliases and unexpected fields gracefully.
    - Produces a deterministic content hash for deduplication.
    """
    cleaned_content = clean_text(raw_doc.raw_content)
    content_hash = compute_content_hash(cleaned_content)

    meta = dict(raw_doc.metadata)

    # Derive human-readable title and source name
    title = meta.get("title")
    resolved_source_name = source_name

    if "source_file" in meta:
        file_path = Path(meta["source_file"])
        if not resolved_source_name:
            resolved_source_name = file_path.name
        if not title:
            title = file_path.stem.replace("_", " ").title()
    elif "url" in meta:
        if not resolved_source_name:
            resolved_source_name = meta["url"]
        if not title:
            title = meta.get("title") or meta["url"]
    elif "table_name" in meta:
        if not resolved_source_name:
            resolved_source_name = f"table:{meta['table_name']}"
        if not title:
            title = f"{meta['table_name'].replace('_', ' ').title()} Record"
    elif "endpoint" in meta:
        if not resolved_source_name:
            resolved_source_name = meta["endpoint"]
        if not title:
            title = "API Record"

    if not title:
        first_line = cleaned_content.splitlines()[0] if cleaned_content else "Untitled Document"
        title = first_line[:60].strip()

    if not resolved_source_name:
        resolved_source_name = f"source-{raw_doc.source_type.value}"

    # Handle structured / tabular records schema drift
    if "row_data" in meta and isinstance(meta["row_data"], dict):
        canonical, extra, schema_hash = normalize_record_schema(meta["row_data"])
        meta["canonical_fields"] = canonical
        meta["extra_metadata"] = extra
        meta["schema_hash"] = schema_hash

    # Preserve provenance
    meta["raw_content_type"] = raw_doc.content_type
    meta["fetched_at"] = raw_doc.fetched_at.isoformat()

    return DocumentRecord(
        source_type=raw_doc.source_type,
        source_id=raw_doc.source_id,
        source_name=resolved_source_name,
        title=title,
        content=cleaned_content,
        metadata=meta,
        content_hash=content_hash,
    )
