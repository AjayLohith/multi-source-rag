# Multi-Source RAG Architecture

## Pipeline Boundary
```
fetch -> extract -> normalize -> validate -> chunk -> hash -> embed -> upsert -> complete
```

---

## Day 1 — Foundation and Architecture Contracts
- **Canonical Contracts** (`app/contracts.py`):
  - `SourceDescriptor`: Source configuration metadata.
  - `RawDocument`: Raw unvalidated output straight from an adapter.
  - `DocumentRecord`: Canonical, normalized document with stable hashes.
  - `ChunkRecord`: Chunked text segment ready for embeddings.
  - `IngestionJob`: Durable tracking record for asynchronous worker execution.
  - `FailureRecord`: Dead-Letter Queue (DLQ) diagnostic record with pipeline stage tags.
- **Enums**: `SourceType`, `JobStatus`, `PipelineStage`.
- **Infrastructure**: Local-first Docker Compose running PostgreSQL (metadata), Redis (queue), and Qdrant (vectors).
- **Configuration** (`app/config.py`): Centralized `Settings` object using `pydantic-settings`.

---

## Day 2 — Source Adapters and Extraction

### Two-Layer Architecture
1. **Extraction Layer** (`app/extraction/`):
   - Pure parsing logic with zero knowledge of adapters, storage, or queues.
   - Submodules:
     - `pdf_extractor.py`: PyMuPDF (`pymupdf`) text extraction.
     - `ocr.py`: PyTesseract optical character recognition fallback.
     - `csv_extractor.py`: Pandas tabular parser emitting `column: value` pairs.
     - `sql_extractor.py`: SQLAlchemy database query engine with bounded limits.
     - `errors.py`: Typed exceptions carrying `source_ref` and `error_code`.
2. **Sources Layer** (`app/sources/`):
   - Thin discovery and orchestration.
   - `SourceAdapter` base class (`base.py`) defines `validate()` and `fetch() -> AsyncIterator[RawDocument]`.
   - Concrete implementations: `PDFSource`, `CSVSource`, `SQLSource`.

### Key Design Decisions
- **OCR is per-page, not per-document**: PyMuPDF checks text density against `MIN_CHARS_BEFORE_OCR = 20`. OCR runs strictly when a page has insufficient text layer.
- **Typed Exceptions**: Failures raise `PDFExtractionError`, `CSVExtractionError`, `SQLExtractionError`, or `OCRError` rather than silently dropping documents or swallowing exceptions.
- **Schema-Agnostic Extraction**: CSV and SQL extractors preserve all encountered columns without forcing schema constraints at extraction time. Normalization and alias mapping are deferred to Day 3.
- **Separation of Concerns**: Adapters and extractors contain zero chunking, embedding, vector database, or LLM logic.
