# Multi-Source RAG — Architectural Decisions & Rationale

*(This file is linked to [decision.md](file:///d:/multi-source-rag-app/decision.md))*

Please see the comprehensive architectural rationale in [decision.md](file:///d:/multi-source-rag-app/decision.md).

---

## Summary of Key Decisions

1. **How it Ran Without Docker**:
   - **PostgreSQL Fallback**: `app/database/session.py` tests port `5432`. If offline, it automatically connects to persistent SQLite at `data/rag_db.sqlite`.
   - **Qdrant Fallback**: `app/vectorstore/qdrant.py` checks `localhost:6333`. If offline, it uses Qdrant's embedded persistent disk storage at `data/qdrant_storage/`.
   - **Redis Fallback**: In-process `asyncio.Queue` processes background tasks if Redis is unreachable.

2. **Source Ingestion & OCR**:
   - PyMuPDF for fast 2ms text parsing.
   - Tesseract OCR per-page fallback only when text character count is below 20.

3. **Normalization & Deduplication**:
   - Schema-agnostic alias mapping (`CANONICAL_ALIASES`) captures unknown columns into `extra_metadata` instead of failing.
   - SHA-256 content hashing deduplicates documents *before* chunking and embedding, skipping redundant vector writes.

4. **Embeddings & Vector Store**:
   - BGE-small (`BAAI/bge-small-en-v1.5`) runs locally on CPU with zero API costs.
   - Qdrant uses deterministic UUIDv5 point IDs for idempotent upserts.

5. **LLM Provider Abstraction**:
   - Unified `LLMProvider` interface supports Groq, Gemini, and Mistral/Ollama without altering retrieval code.

6. **PowerShell `curl.exe` Note**:
   - In PowerShell, run `curl.exe` (not `curl`) to invoke the native Windows curl binary rather than PowerShell's `Invoke-WebRequest` alias.
