# Multi-Source RAG — End-to-End System Flow

This document details the complete end-to-end data and execution flows across all stages of the application.

---

## 1. Global Pipeline Architecture

```
[ Data Source ] 
       │
       ▼
1. FETCH (app/sources/)
       │
       ▼
2. EXTRACT (app/extraction/) ──> (OCR Fallback if scanned page)
       │
       ▼
3. NORMALIZE (app/normalization/) ──> Clean Unicode / Whitespace / Schema Drift
       │
       ▼
4. DEDUPLICATE (app/database/) ──> Compute SHA-256 (Skip unchanged docs)
       │
       ▼
5. CHUNK (app/chunking/) ──> Source-Aware Boundary Splitting
       │
       ▼
6. EMBED (app/embeddings/) ──> Local BGE Model Batching
       │
       ▼
7. UPSERT (app/vectorstore/) ──> Deterministic Point ID Upsert into Qdrant
       │
       ▼
8. CHECKPOINT (app/database/) ──> Mark Job COMPLETED
```

---

## 2. Ingestion Flow (Step-by-Step)

```mermaid
sequenceDiagram
    autonumber
    actor User as User / API Client
    participant API as FastAPI (/ingest)
    participant Pipeline as IngestionPipeline
    participant Adapter as SourceAdapter (PDF, CSV, SQL, Web)
    participant Normalizer as Normalizer & Schemas
    participant DB as Database (Postgres / SQLite)
    participant Chunker as SourceAware Chunker
    participant Embed as BGE Embedding Model
    participant Qdrant as Qdrant Vector Store

    User->>API: POST /ingest (source_type, name, config)
    API->>DB: Create IngestionJob (status=PENDING)
    API->>Pipeline: execute_ingestion_pipeline(descriptor)
    Pipeline->>Adapter: validate() & fetch()
    Adapter-->>Pipeline: Yield RawDocument stream

    loop For each RawDocument
        Pipeline->>Normalizer: normalize_document(raw_doc)
        Normalizer-->>Pipeline: Returns DocumentRecord (content_hash)
        
        Pipeline->>DB: Check if content_hash exists
        alt Hash matches existing document
            Pipeline->>Pipeline: Increment skipped_duplicates count
            Note over Pipeline: Skip redundant embedding & upsert!
        else New or updated document
            Pipeline->>DB: Save DocumentRecord to documents table
            Pipeline->>Chunker: chunk_document(doc)
            Chunker-->>Pipeline: List of ChunkRecord
            Pipeline->>Embed: embed_documents([chunk.text])
            Embed-->>Pipeline: List of vector floats (384-dim)
            Pipeline->>Qdrant: upsert_chunks(chunks, vectors)
        end
    end

    Pipeline->>DB: Update IngestionJob (status=COMPLETED)
    Pipeline-->>API: Return job summary (docs, chunks, duplicates)
    API-->>User: HTTP 200 JSON Response
```

---

## 3. Specialized Extraction Flows

### A. PDF Extraction & OCR Fallback Flow
```
PDF File
   │
   ▼
Open via PyMuPDF (fitz)
   │
   ├─► For each page:
   │      │
   │      ├─► Extract text layer: `text = page.get_text()`
   │      │
   │      ├─► Evaluate: `len(text.strip()) < 20`?
   │      │      │
   │      │      ├─► NO (Native Text):
   │      │      │     Keep extracted text, `ocr_used = False`
   │      │      │
   │      │      └─► YES (Scanned / Image-Only):
   │      │            Render page pixmap (`page.get_pixmap()`)
   │      │            Convert to PNG image bytes
   │      │            Invoke Tesseract OCR engine (`pytesseract`)
   │      │            Recover text, set `ocr_used = True`
   │      │
   │      └─► Store page metadata (page_number, char_count, ocr_used)
   │
   ▼
Yield RawDocument with embedded page boundaries
```

### B. Tabular Schema Drift Flow (CSV / SQL / JSON)
```
Raw Row Dict: {'emp_id': 101, 'full_name': 'Alice', 'dept': 'Eng', 'clearance': 'TopSecret'}
   │
   ▼
normalize_record_schema()
   │
   ├─► Known Aliases (CANONICAL_ALIASES):
   │      'emp_id'    ──► 'id': 101
   │      'full_name' ──► 'name': 'Alice'
   │      'dept'      ──► 'department': 'Eng'
   │
   ├─► Unknown / Unexpected Fields:
   │      'clearance' ──► extra_metadata: {'clearance': 'TopSecret'}
   │      (Ingestion does not crash; extra metadata preserved)
   │
   └─► Fingerprint:
          SHA-256 of sorted keys ──► schema_hash: '9a8b7c6d5e4f'
```

---

## 4. Retrieval & Grounded RAG Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Client
    participant API as FastAPI (/chat or /search)
    participant Ret as MultiSourceRetriever
    participant Embed as BGE Model
    participant Qdrant as Qdrant Vector Store
    participant Rerank as Reranker
    participant LLM as LLM Provider (Groq / Gemini / Ollama)

    User->>API: POST /chat (query="Who is the Lead Propulsion Engineer?", top_k=2)
    API->>Ret: retrieve(query, top_k=2)
    Ret->>Embed: embed_query(query)
    Embed-->>Ret: 384-dimensional query vector
    Ret->>Qdrant: search_vectors(query_vector, top_k=4)
    Qdrant-->>Ret: Candidate chunks with similarity scores
    Ret->>Rerank: rerank(query, candidates)
    Rerank-->>Ret: Top 2 re-scored candidates
    
    Ret->>Ret: build_context(results)
    Note over Ret: Assembles source header tags:<br/>[Source 1: Internal Employee Database | Row: 0]<br/>[Source 2: Orbital Manual | Page: 2]<br/>Generates Citation objects

    API->>LLM: generate(query, context)
    Note over LLM: Applies Grounded System Prompt:<br/>Answer STRICTLY from context.<br/>If information is missing, state so.<br/>Cite source tags.
    LLM-->>API: Grounded Answer
    API-->>User: HTTP 200 { answer, citations, evidence_count }
```

---

## 5. Resilience & Failure Handling Flow (DLQ)

```
Pipeline Execution
       │
       ▼
Error Encountered?
       │
       ├─► Transient Network / 429 / 5xx / Timeout:
       │      │
       │      └─► Tenacity Exponential Backoff:
       │            Attempt 1: wait 0.5s
       │            Attempt 2: wait 1.0s
       │            Attempt 3: wait 2.0s
       │            Retry operation
       │
       └─► Permanent Failure (Corrupt File / Auth Error / Max Retries Exceeded):
              │
              ├─► Trap Typed Error (`ExtractionError`, `PDFExtractionError`, etc.)
              │
              ├─► Route to Dead-Letter Queue:
              │     Persist into `failed_documents` table:
              │     - `failure_id`
              │     - `job_id`
              │     - `stage` (FETCH / EXTRACT / NORMALIZE / EMBED)
              │     - `error_code` (e.g. 'PDF_CORRUPT')
              │     - `error_message`
              │     - `raw_payload`
              │
              └─► Mark `ingestion_jobs` status as `FAILED` or `DEAD_LETTER`
```
