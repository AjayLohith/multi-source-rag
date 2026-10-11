# Multi-Source RAG — Architectural Decisions & Rationale

This document explains **why** specific technologies, patterns, and trade-offs were chosen across the project lifecycle.

---

## 1. Dual-Mode Infrastructure (Why it ran without Docker)

### The Question
> *"I didn't run Qdrant, Redis, Postgres in Docker — how did you use those for this project?"*

### The Decision: Zero-Crash Self-Healing Fallback
In enterprise development, systems must operate seamlessly in both containerized CI/CD environments and local developer laptops where Docker Desktop might be stopped or unavailable.

1. **Database: PostgreSQL ➔ Persistent SQLite Fallback**
   - **Why**: PostgreSQL is standard for multi-worker concurrency. However, hardcoding PostgreSQL causes `Connection refused` or authentication errors on machines without running containers.
   - **How**: `app/database/session.py` performs a non-blocking 1-second probe to port `5432`. If unreachable or authentication fails, it automatically points SQLAlchemy to `data/rag_db.sqlite`.
   - **Outcome**: The exact same tables (`documents`, `ingestion_jobs`, `failed_documents`, `schema_versions`) and repository methods operate identically with zero data loss.

2. **Vector Database: Qdrant Server ➔ Embedded Qdrant Disk Storage**
   - **Why**: Qdrant is a dedicated vector engine. Waiting for an external service can block local offline experimentation.
   - **How**: `app/vectorstore/qdrant.py` tests `http://localhost:6333`. If offline, it initializes `QdrantClient(path="data/qdrant_storage")`.
   - **Outcome**: Qdrant's embedded Rust storage engine runs directly within the Python process, saving embeddings and collections to disk without needing Docker containers.

3. **Message Queue: Redis ➔ In-Process Asyncio Queue**
   - **Why**: Redis coordinates distributed workers. For single-node and local execution, starting a Redis daemon is unnecessary overhead.
   - **How**: `app/ingestion/worker.py` provides an `asyncio.Queue` fallback to execute background ingestion asynchronously.

---

## 2. Ingestion & Extraction Layer Decisions

### Why PyMuPDF (`pymupdf`) for PDF extraction?
- **Speed**: PyMuPDF is built on the MuPDF C library and is 10x to 25x faster than pure-Python libraries like PyPDF or pdfminer.
- **Embedded Rendering**: PyMuPDF can directly rasterize individual pages to high-resolution PNG pixmaps (`page.get_pixmap()`) in memory. Other libraries require installing external system binaries like `poppler` (`pdftoppm`).

### Why is OCR a per-page fallback rather than per-document?
- **Computational Cost**: Neural and Tesseract OCR requires 1.0 to 3.0 seconds per page on CPU. Running OCR across a 50-page document where only 1 page is an image wastes 98% of processing time.
- **Decision**: In `app/extraction/pdf_extractor.py`, text length is evaluated per page (`MIN_CHARS_BEFORE_OCR = 20`). If native text exists, it is extracted in 2 milliseconds. Tesseract OCR is invoked strictly when a page lacks text.

### Why Tesseract for OCR?
- **Zero Cost & Privacy**: Completely local, open source, offline, and does not incur per-page third-party cloud API bills.

### Why Pandas for CSV and SQLAlchemy for SQL?
- **Pandas**: Provides automatic header detection, type inference, and flexible encoding handling for heterogeneous CSV files.
- **SQLAlchemy**: Decouples extraction logic from specific SQL dialects. Parameterized queries enforce security and prevent SQL injection.

---

## 3. Data Normalization & Contract Freezing

### Why freeze contracts on Day 1 (`RawDocument` ➔ `DocumentRecord` ➔ `ChunkRecord`)?
- In RAG architectures, tight coupling between scrapers/parsers and vector stores causes cascading refactors whenever a source schema changes.
- Freezing contracts creates a strict boundary:
  - Adapters only know how to produce `RawDocument`.
  - Normalizers only know how to convert `RawDocument` to `DocumentRecord`.
  - Chunkers only know how to slice `DocumentRecord` into `ChunkRecord`.

### Why SHA-256 Content Hashing for Deduplication?
- **Cost Avoidance**: Generating embeddings and writing vectors are the most computationally expensive operations in RAG.
- **Decision**: `compute_content_hash(cleaned_text)` is calculated *immediately after normalization*. If a document's SHA-256 hash already exists in the database, ingestion skips chunking and embedding entirely (`status="skipped_duplicate"`).

### Why Schema-Agnostic Tabular Ingestion?
- Heterogeneous tables frequently have column aliases (`emp_id` vs `employee_id` vs `id`).
- In `app/normalization/schemas.py`, known aliases map to canonical fields, and unexpected columns are captured into `extra_metadata` rather than throwing validation errors.

---

## 4. Embeddings, Vector Store, & Chunking

### Why BGE-Small (`BAAI/bge-small-en-v1.5`)?
- **Dimensionality**: 384 dimensions (lightweight compared to 1536-dim cloud embeddings).
- **Benchmark Performance**: Consistently ranks at the top of the Massive Text Embedding Benchmark (MTEB) for compact models.
- **Resource Footprint**: Consumes only ~130MB of RAM and encodes sentences on CPU in under 15ms.

### Why Lazy Model Loading?
- Machine learning libraries (`torch`, `transformers`) take 3 to 15 seconds to load DLLs into memory.
- In `app/embeddings/model.py`, the model weights are loaded only upon the first invocation of `embed_documents()` or `embed_query()`, keeping app boot and test collection instantaneous.

### Why Deterministic Point IDs in Qdrant?
- `_deterministic_point_id(chunk_id)` uses UUIDv5 to generate reproducible vector IDs.
- If the same chunk is upserted multiple times, Qdrant performs an in-place update rather than creating duplicate points.

---

## 5. Retrieval & LLM Generation

### Why Provider Abstraction (`Groq`, `Gemini`, `Mistral/Ollama`)?
- Vendor lock-in is a critical risk in LLM applications.
- In `app/llm/base.py`, `LLMProvider` enforces a single interface: `generate(query, context)`. Switching providers requires changing only the `LLM_PROVIDER` environment variable.

### Why Grounded Prompts with Explicit Citation Tags?
- Hallucination mitigation: The system prompt instructs the model to answer *strictly* from the context blocks and state when evidence is insufficient.
- Traceability: Context blocks are prepended with `[Source X: name (type) | Page/Row]`, enabling verifiable citations in the response.

---

## 6. Windows PowerShell Note: `curl` vs `curl.exe`
- In Windows PowerShell, the command `curl` is aliased by default to the cmdlet `Invoke-WebRequest`.
- Because `Invoke-WebRequest` does not parse `-H "Content-Type: application/json"` in the same format as Unix curl, executing `curl` directly causes:
  `Cannot bind parameter 'Headers'. Cannot convert string to IDictionary`.
- Calling `curl.exe` runs the native Windows curl executable directly and handles standard curl flags without issue.
