import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.database.models import DocumentModel
from app.contracts import DocumentRecord, SourceType
from app.chunking.chunker import chunk_document
from app.embeddings.model import default_embedding_model
from app.vectorstore.qdrant import default_vector_store
from app.vectorstore.collections import ensure_collection
from app.config import settings


async def rebuild_index():
    print("=== Rebuilding Vector Store Index from Database Records ===")

    # 1. Reset / ensure clean collection
    print(f"Ensuring collection '{default_vector_store.collection_name}'...")
    ensure_collection(
        default_vector_store.client,
        collection_name=default_vector_store.collection_name,
        vector_size=settings.embedding_dim,
    )

    # 2. Fetch all stored documents
    with SessionLocal() as session:
        docs = session.query(DocumentModel).all()
        print(f"Found {len(docs)} document record(s) in database.")

        total_chunks = 0
        for d in docs:
            doc_record = DocumentRecord(
                document_id=d.document_id,
                source_type=SourceType(d.source_type),
                source_id=d.source_id,
                source_name=d.source_name,
                title=d.title,
                content=d.content,
                metadata=d.metadata_json or {},
                content_hash=d.content_hash,
                version=d.version,
            )
            chunks = chunk_document(doc_record)
            texts = [c.content for c in chunks]
            embeddings = default_embedding_model.embed_documents(texts)
            upserted = default_vector_store.upsert_chunks(chunks, embeddings)
            total_chunks += upserted

        print(f"Re-indexing complete. Upserted {total_chunks} total chunks.")


if __name__ == "__main__":
    asyncio.run(rebuild_index())
