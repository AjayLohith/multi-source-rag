<div align="center">

# Multi-Source RAG

A production-grade Retrieval-Augmented Generation system that ingests, normalizes, deduplicates, and queries across 9+ heterogeneous data formats through a single async API.

<p align="left">Built with the tools and technologies:</p>

<p align="left">
  <img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688.svg?style=flat&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Pydantic-E92063.svg?style=flat&logo=pydantic&logoColor=white" alt="Pydantic">
  <img src="https://img.shields.io/badge/SQLAlchemy-D71F00.svg?style=flat&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1.svg?style=flat&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/SQLite-003B57.svg?style=flat&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/Qdrant-DC2626.svg?style=flat&logo=qdrant&logoColor=white" alt="Qdrant">
  <img src="https://img.shields.io/badge/Redis-DC382D.svg?style=flat&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Docker-2496ED.svg?style=flat&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/HuggingFace-FFD21E.svg?style=flat&logo=huggingface&logoColor=black" alt="HuggingFace">
  <img src="https://img.shields.io/badge/Groq-FF6B35.svg?style=flat&logo=groq&logoColor=white" alt="Groq">
  <img src="https://img.shields.io/badge/Google%20Gemini-4285F4.svg?style=flat&logo=googlegemini&logoColor=white" alt="Gemini">
  <img src="https://img.shields.io/badge/Tesseract%20OCR-4B8BBE.svg?style=flat&logo=tesseract&logoColor=white" alt="Tesseract OCR">
  <img src="https://img.shields.io/badge/Pandas-150458.svg?style=flat&logo=pandas&logoColor=white" alt="Pandas">
  <img src="https://img.shields.io/badge/Pytest-0A9EDC.svg?style=flat&logo=pytest&logoColor=white" alt="Pytest">
</p>

</div>

---

## Overview

Most RAG implementations handle a single file type, re-embed unchanged documents on every run, crash without Docker, and return answers without citations. This project solves all of that.

The system accepts **9 data formats** — scanned and digital PDFs, CSV, SQL databases, Word documents, JSON, Markdown, plain text, web pages, and REST APIs — processes them through a uniform pipeline, and serves grounded, cited answers via a FastAPI REST API.

**What makes it different:**

- **Per-page OCR fallback** — PyMuPDF extracts native text in under 2ms per page. Only pages with fewer than 20 characters of text are routed to Tesseract OCR, avoiding the 98% compute waste of full-document OCR.
- **Content-addressed deduplication** — Every document is SHA-256 hashed before embedding. If the hash already exists in the database, the entire embedding and vector write is skipped at zero cost.
- **Zero-crash dual runtime** — The app probes PostgreSQL, Redis, and Qdrant on startup. If any service is offline, it silently falls back to SQLite, asyncio queues, and Qdrant's embedded disk engine. No configuration changes needed.
- **Multi-LLM provider abstraction** — Swap between Groq (Llama-3.3-70b), Google Gemini 1.5 Flash, and Mistral with a single `provider` parameter. All responses enforce strict context grounding and source-level citations.
- **37 automated tests** covering contracts, every source adapter, OCR fallback paths, schema drift, corrupted inputs, rate limiting, and all API endpoints.

---

## System Architecture

```
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                         DATA EXTRACTION & ADAPTERS                          │
  │   PDF (Native + OCR) │ CSV │ SQL │ DOCX │ JSON │ Markdown │ Web │ REST API  │
  └──────────────────────────────────────┬──────────────────────────────────────┘
                                         │  RawDocument
                                         ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                           NORMALIZATION LAYER                               │
  │      Unicode / Whitespace Cleaning │ Schema Mapping │ SHA-256 Hashing       │
  └──────────────────────────────────────┬──────────────────────────────────────┘
                                         │  DocumentRecord
                                         ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                     IDEMPOTENT DEDUPLICATION CHECK                          │
  │             Hash exists in DB? ──► YES ──► Skip (0 cost)                    │
  │                                └──► NO  ──► Continue                        │
  └──────────────────────────────────────┬──────────────────────────────────────┘
                                         │  ChunkRecord[]
                                         ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                    ADAPTIVE CHUNKING & LOCAL EMBEDDINGS                     │
  │    Source-Aware Splitting ──► BGE-small-en-v1.5 Batcher (384-d vectors)     │
  └──────────────────────────────────────┬──────────────────────────────────────┘
                                         │  Vectors + Payloads
                                         ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                   STORAGE & VECTOR INDEX (DUAL RUNTIME)                     │
  │   PostgreSQL / SQLite  ◄── Metadata │ Qdrant Server / Disk ──► Vectors      │
  └──────────────────────────────────────┬──────────────────────────────────────┘
                                         │  Top-K Cosine Search
                                         ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                      RETRIEVAL & GROUNDED GENERATION                        │
  │      Context Bounding ──► Multi-LLM (Groq / Gemini / Mistral)               │
  └──────────────────────────────────────┬──────────────────────────────────────┘
                                         │
                                         ▼
                               Cited Answer + Sources
```

The pipeline uses frozen Pydantic contracts at every boundary (`RawDocument` → `DocumentRecord` → `ChunkRecord`), so adding a new source adapter or swapping the vector database requires zero changes to the rest of the system.

---

## Supported Data Sources

| Format | Engine | How It Handles Edge Cases |
| :--- | :--- | :--- |
| **PDF** | PyMuPDF + Tesseract | Native text extraction with automatic per-page OCR fallback for scanned/image pages |
| **CSV** | Pandas | Schema-agnostic — handles reordered columns, dirty whitespace, and alias mapping |
| **SQL** | SQLAlchemy | Parameterized queries, primary key auto-discovery, row limits to prevent OOM |
| **DOCX** | python-docx | Paragraph and nested table extraction with empty section pruning |
| **JSON** | stdlib | Flat objects and nested arrays unrolled into searchable text |
| **Markdown** | Regex parser | Header hierarchy preservation for boundary-aware chunking |
| **Plain Text** | Streaming | UTF-8 normalization with whitespace cleanup |
| **Web Pages** | HTTPX + BeautifulSoup | Strips scripts, CSS, nav, footers — extracts clean body text |
| **REST API** | HTTPX async | JSON endpoint extraction with auth headers and pagination |

---

## Design Decisions

| Decision | Why |
| :--- | :--- |
| **PyMuPDF over pdfminer/poppler** | 10–25x faster on CPU. Built-in page rasterization for OCR without external system binaries. |
| **Per-page OCR, not per-document** | A 50-page PDF with 1 scanned page wastes 49 pages of OCR compute. Threshold check (<20 chars) triggers OCR only where needed. |
| **SHA-256 dedup over timestamps** | File paths and modified dates change across machines. Content hashing gives true idempotence. |
| **Local BGE-small embeddings** | Zero API cost, full privacy, deterministic 384-d vectors, no network latency. |
| **Dual runtime fallback** | Developers shouldn't need Docker running to test locally. Auto-probe and fallback to SQLite + disk Qdrant. |
| **Frozen Pydantic contracts** | Decouples extractors from storage. Adding a source or swapping a vector DB causes zero cascading changes. |
| **Dead Letter Queue** | Failed documents go to DLQ instead of crashing the pipeline. Retry with exponential backoff + jitter. |

---

## Getting Started

### Prerequisites
- Python 3.11+
- Git
- *(Optional)* Docker & Docker Compose — for PostgreSQL, Redis, and Qdrant containers. Without Docker, the system uses SQLite and local Qdrant automatically.

### Setup
```powershell
git clone https://github.com/AjayLohith/multi-source-rag.git
cd multi-source-rag

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

### Configure Environment
```powershell
cp .env.example .env
```
Fill in your API keys in `.env`:
```env
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-1.5-flash

GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Optional — system falls back to SQLite + disk Qdrant if these are unreachable
DATABASE_URL=postgresql+psycopg://rag_user:rag_pass@localhost:5432/rag_db
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
```

### Run Tests
```powershell
# Full 37-test suite
.venv\Scripts\pytest -v

# Individual adapter verification
.venv\Scripts\python.exe scripts/test_sources.py
```

### Ingest Data
```powershell
# Ingest all sample fixtures (PDF, CSV, SQL, DOCX, JSON, MD, TXT)
.venv\Scripts\python.exe scripts/ingest_all.py

# Rebuild vector index from database
.venv\Scripts\python.exe scripts/rebuild_index.py
```

### Start the Server
```powershell
.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```
Swagger docs at **http://localhost:8000/docs**

---

## API Usage

### Ingest a source
```powershell
curl.exe -X POST "http://localhost:8000/ingest" `
  -H "Content-Type: application/json" `
  -d '{"source_type": "csv", "name": "Support FAQ", "config": {"path": "data/raw/csv/support_faq_clean.csv"}}'
```
```json
{
  "job_id": "job_94c483a9",
  "status": "queued",
  "source_type": "csv",
  "message": "Ingestion job queued for Support FAQ"
}
```

### Search
```powershell
curl.exe -X POST "http://localhost:8000/search" `
  -H "Content-Type: application/json" `
  -d '{"query": "What is the policy for medical leave?", "top_k": 3}'
```

### Chat (grounded RAG)
```powershell
curl.exe -X POST "http://localhost:8000/chat" `
  -H "Content-Type: application/json" `
  -d '{"query": "Who is the Lead Propulsion Engineer?", "top_k": 3, "provider": "groq"}'
```
```json
{
  "query": "Who is the Lead Propulsion Engineer?",
  "answer": "Elena Vance is the Lead Propulsion Engineer in the Aerospace Engineering department.",
  "citations": [
    {
      "document_id": "doc_e4a8b792",
      "chunk_id": "chunk_3f21a8b0",
      "source_type": "csv",
      "score": 0.892,
      "preview": "Name: Elena Vance | Department: Aerospace Engineering | Role: Lead Propulsion Engineer"
    }
  ],
  "provider": "groq",
  "model": "llama-3.3-70b-versatile"
}
```

---

## Project Structure

```
multi-source-rag/
├── app/
│   ├── main.py                # FastAPI bootstrap and lifespan
│   ├── config.py              # Pydantic BaseSettings
│   ├── contracts.py           # Frozen data contracts (RawDocument, DocumentRecord, ChunkRecord)
│   ├── api/                   # Route handlers — /health, /ingest, /search, /chat
│   ├── sources/               # Source adapters — PDF, CSV, SQL, DOCX, JSON, MD, TXT, Web, API
│   ├── extraction/            # Parsing engines, OCR fallback, typed exceptions
│   ├── normalization/         # Unicode cleanup, schema drift mapping, SHA-256 hashing
│   ├── chunking/              # Source-aware boundary chunkers
│   ├── database/              # SQLAlchemy ORM models, session factory, repository
│   ├── resilience/            # Exponential backoff, jitter, rate limiter, Dead Letter Queue
│   ├── embeddings/            # SentenceTransformers (BGE-small) model and batching
│   ├── vectorstore/           # Qdrant client, collection setup, similarity search
│   ├── retrieval/             # Semantic search, context builder, citation linker
│   └── llm/                   # Multi-provider LLM abstraction (Groq, Gemini, Mistral)
├── data/
│   └── raw/                   # Sample fixtures across all 9 formats
├── docker/
│   └── docker-compose.yml     # PostgreSQL, Redis, Qdrant container config
├── scripts/
│   ├── ingest_all.py          # Batch ingest all raw data
│   ├── rebuild_index.py       # Re-index database records into Qdrant
│   └── test_sources.py        # Adapter diagnostic script
├── tests/                     # 37 automated tests
├── documentation.md           # Full system documentation
├── flow.md                    # Execution flows and Mermaid diagrams
├── decision.md                # Engineering trade-off rationales
├── .env.example               # Environment variable template
└── requirements.txt           # Dependencies
```

---

## License

MIT