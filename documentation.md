# Multi-Source RAG — Complete System Documentation

## 1. Overview
This project is an enterprise-grade, multi-source Retrieval-Augmented Generation (RAG) platform. It is engineered from first principles to ingest, extract, normalize, deduplicate, chunk, embed, index, and query information across heterogeneous data types without coupling the components.

### Supported Data Formats
- **PDF Documents**: Dual-path engine utilizing PyMuPDF for native vector text and Tesseract OCR for scanned/rasterized pages.
- **CSV Spreadsheets**: Schema-agnostic extraction handling column reordering and unexpected schema drift.
- **SQL Relational Databases**: SQLAlchemy-powered extractor with explicit developer limits and relational mapping.
- **Markdown (`.md`) & Plain Text (`.txt`)**: Text extraction with line and paragraph boundary preservation.
- **JSON Files (`.json`)**: Hierarchical and tabular record parsing.
- **Microsoft Word (`.docx`)**: Paragraph and table structure parsing via python-docx.
- **Web Pages**: Async HTTP fetching with BeautifulSoup DOM cleaning (stripping scripts, styling, nav, and footers).
- **REST APIs**: Generic JSON endpoint extraction.

---

## 2. Dual-Mode Infrastructure (Docker & Local Standalone)

### How did the app run without starting Docker?
In production or standard containerized deployments, the application connects to services configured in `docker/docker-compose.yml`:
- **PostgreSQL**: Durable metadata, document versioning, schema hashes, and job logs.
- **Redis**: Asynchronous job queue for background workers.
- **Qdrant**: High-performance vector database on port `6333`.

However, developer environments frequently do not have Docker running or encounter port/permission conflicts. To make this project work reliably without Docker, the architecture includes an **Automatic Local-First Fallback Layer**:

1. **Database Fallback (`app/database/session.py`)**:
   - The engine checks if the configured PostgreSQL port (`5432`) is reachable and authenticated using a 1-second non-blocking probe.
   - If PostgreSQL is offline or authentication fails, it automatically switches to an embedded SQLite database persisted at `data/rag_db.sqlite`.
   - The database models and queries use standard SQLAlchemy ORM abstractions, so all features (deduplication, job tracking, DLQ, schema versioning) work identically on both engines.

2. **Vector Store Fallback (`app/vectorstore/qdrant.py`)**:
   - The Qdrant client checks if the Docker container is reachable on `http://localhost:6333`.
   - If offline, it initializes Qdrant's embedded persistent on-disk engine targeting `data/qdrant_storage/`.
   - The API, collection schema, cosine distance similarity search, and payload filtering run the exact same Qdrant Rust engine locally without needing Docker containers.

3. **Queue Fallback (`app/ingestion/manager.py` & `worker.py`)**:
   - In the absence of a live Redis instance, an internal asynchronous `asyncio.Queue` processes jobs backgrounded through FastAPI's async runtime.

---

## 3. Directory Structure

```
multi-source-rag/
├── app/
│   ├── main.py                     # FastAPI application bootstrap & lifespan
│   ├── config.py                   # Centralized Pydantic BaseSettings
│   ├── contracts.py                # Frozen data contracts (DTOs & Enums)
│   ├── api/                        # HTTP route handlers (/ingest, /search, /chat)
│   ├── sources/                    # SourceAdapter implementations (PDF, CSV, SQL, etc.)
│   ├── extraction/                 # Pure parsing logic & typed exceptions
│   ├── normalization/              # Cleaning, schema mapping, & SHA-256 hashing
│   ├── chunking/                   # Source-aware boundary chunkers
│   ├── database/                   # SQLAlchemy models, session, & repository
│   ├── resilience/                 # Retries, backoff, rate limiting, and DLQ
│   ├── embeddings/                 # SentenceTransformers local model & batching
│   ├── vectorstore/                # Qdrant upsert, collection setup, and search
│   ├── retrieval/                  # Semantic search, context builder, & citations
│   ├── llm/                        # Provider abstraction (Groq, Gemini, Mistral/Ollama)
│   └── utils/                      # Hashing, logging, and UUID generation
├── data/
│   ├── raw/                        # Raw source files by format
│   ├── rag_db.sqlite               # Local persistent database (fallback)
│   └── qdrant_storage/             # Local persistent vector store (fallback)
├── docker/
│   └── docker-compose.yml          # PostgreSQL, Redis, Qdrant containers
├── notebooks/
│   ├── Day1_smoke_tes.ipynb        # Day 1 infrastructure smoke test
│   └── day2_smoke_test.ipynb       # Day 2 adapter & OCR smoke test
├── scripts/
│   ├── test_sources.py             # Test all source adapters
│   ├── ingest_all.py               # Batch ingestion script
│   └── rebuild_index.py            # Re-index all database records into vector store
├── tests/                          # 37-test automated test suite (pytest)
├── requirements.txt
├── architecture.md
├── documentation.md
├── flow.md
└── decision.md
```

---

## 4. Canonical Data Contracts (`app/contracts.py`)

Every subsystem in the application communicates strictly through frozen Pydantic contracts:
1. `SourceDescriptor`: Defines a source connection (type, name, configuration path/url/query).
2. `RawDocument`: Raw, unnormalized text payload yielded from an adapter's `fetch()` generator.
3. `DocumentRecord`: The normalized canonical document with clean text, provenance metadata, version number, and a deterministic SHA-256 content hash.
4. `ChunkRecord`: Text slice associated with a `document_id`, with chunk index, character bounds, and source metadata.
5. `IngestionJob`: Durable state machine tracking job execution (`pending`, `in_progress`, `completed`, `failed`, `dead_letter`, `skipped_duplicate`).
6. `FailureRecord`: Dead-Letter Queue record storing the failed pipeline stage, error code, error message, and raw payload.

---

## 5. Execution & Testing Guide

### Running Pytest
```powershell
.venv\Scripts\pytest -v
```
Executes all 37 unit and integration tests across contracts, extractors, normalizers, deduplication, chunking, retrieval, and API endpoints.

### Testing Source Adapters
```powershell
.venv\Scripts\python.exe scripts/test_sources.py
```
Validates that PDF text, OCR fallback, CSV, and SQL adapters successfully extract structured data into `RawDocument` objects.

### Ingesting Fixtures
```powershell
.venv\Scripts\python.exe scripts/ingest_all.py
```
Runs the end-to-end pipeline over sample PDFs, scanned documents, CSVs, and SQLite tables. Subsequent runs will output `skipped_duplicate` because of SHA-256 deduplication.

### Rebuilding Vector Index
```powershell
.venv\Scripts\python.exe scripts/rebuild_index.py
```
Reads all canonical documents from the database, chunks them, computes embeddings, and repopulates the Qdrant index.

### Starting the FastAPI Server
```powershell
.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```
Interactive Swagger API documentation: `http://localhost:8000/docs`

---

## 6. Windows PowerShell API Invocation Notes
In Windows PowerShell, the command `curl` is an alias for the cmdlet `Invoke-WebRequest`. To execute standard curl requests from PowerShell, use `curl.exe` or PowerShell's `Invoke-RestMethod`:

```powershell
# Using native curl.exe
curl.exe -X POST http://localhost:8000/search -H "Content-Type: application/json" -d "{\"query\":\"Who is the Lead Propulsion Engineer?\",\"top_k\":2}"

# Or using PowerShell Invoke-RestMethod
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post -ContentType "application/json" -Body '{"query":"What department is Elena Vance in?","top_k":2,"provider":"groq"}'
```
