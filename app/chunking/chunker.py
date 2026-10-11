from typing import List, Optional
import re

from app.config import settings
from app.contracts import ChunkRecord, DocumentRecord, SourceType


def _split_text_with_overlap(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Splits plain text into character windows with overlap, respecting line boundaries."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:].strip())
            break

        # Attempt to split cleanly on a newline or space near end
        split_point = text.rfind("\n", start + chunk_overlap, end)
        if split_point == -1:
            split_point = text.rfind(" ", start + chunk_overlap, end)
        if split_point == -1:
            split_point = end

        chunks.append(text[start:split_point].strip())
        start = max(split_point + 1, start + chunk_size - chunk_overlap)

    return [c for c in chunks if c]


def chunk_document(
    doc: DocumentRecord,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> List[ChunkRecord]:
    """
    Source-aware chunker that divides a canonical DocumentRecord into ChunkRecords.
    - Tabular records (CSV/SQL/JSON) stay intact per row if under chunk_size.
    - PDF documents preserve page boundaries when [PAGE X] headers exist.
    - Web / Text / Markdown documents split on paragraph boundaries with configurable overlap.
    """
    size = chunk_size or settings.chunk_size
    overlap = chunk_overlap or settings.chunk_overlap

    base_metadata = {
        "document_id": doc.document_id,
        "source_type": doc.source_type.value,
        "source_id": doc.source_id,
        "source_name": doc.source_name,
        "title": doc.title,
        "content_hash": doc.content_hash,
        "version": doc.version,
    }
    # Inherit source location pointers
    for key in ("source_file", "url", "table_name", "page", "row_index", "endpoint"):
        if key in doc.metadata:
            base_metadata[key] = doc.metadata[key]

    raw_chunks: List[str] = []

    # 1. Tabular records (CSV, SQL, JSON)
    if doc.source_type in (SourceType.CSV, SourceType.SQL, SourceType.JSON, SourceType.API):
        if len(doc.content) <= size:
            raw_chunks = [doc.content]
        else:
            raw_chunks = _split_text_with_overlap(doc.content, size, overlap)

    # 2. PDF documents with page headers
    elif doc.source_type == SourceType.PDF and "[PAGE " in doc.content:
        pages = re.split(r"(?=\[PAGE \d+\])", doc.content)
        for page_text in pages:
            page_text = page_text.strip()
            if not page_text:
                continue
            if len(page_text) <= size:
                raw_chunks.append(page_text)
            else:
                raw_chunks.extend(_split_text_with_overlap(page_text, size, overlap))

    # 3. Text, Markdown, Web, DOCX
    else:
        # Split on paragraph blocks first
        paragraphs = [p.strip() for p in doc.content.split("\n\n") if p.strip()]
        current_chunk = []
        current_len = 0

        for p in paragraphs:
            if current_len + len(p) + 2 <= size:
                current_chunk.append(p)
                current_len += len(p) + 2
            else:
                if current_chunk:
                    raw_chunks.append("\n\n".join(current_chunk))
                if len(p) > size:
                    raw_chunks.extend(_split_text_with_overlap(p, size, overlap))
                    current_chunk = []
                    current_len = 0
                else:
                    current_chunk = [p]
                    current_len = len(p)

        if current_chunk:
            raw_chunks.append("\n\n".join(current_chunk))

    if not raw_chunks:
        raw_chunks = [doc.content]

    records: List[ChunkRecord] = []
    for idx, chunk_text in enumerate(raw_chunks):
        chunk_meta = dict(base_metadata)
        chunk_meta["chunk_index"] = idx
        chunk_meta["char_length"] = len(chunk_text)

        # Detect page number if embedded in text
        page_match = re.search(r"\[PAGE (\d+)\]", chunk_text)
        if page_match:
            chunk_meta["page_number"] = int(page_match.group(1))

        records.append(
            ChunkRecord(
                document_id=doc.document_id,
                chunk_index=idx,
                content=chunk_text,
                metadata=chunk_meta,
            )
        )

    return records
