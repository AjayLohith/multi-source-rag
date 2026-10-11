import socket
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct

from app.config import settings
from app.contracts import ChunkRecord
from app.embeddings.batcher import batch_items
from app.vectorstore.collections import ensure_collection


def _is_port_open(host: str, port: int, timeout: float = 0.2) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def _deterministic_point_id(chunk_id: str) -> str:
    """Produces a valid UUID string deterministically from chunk_id."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))


class QdrantVectorStore:
    """Manages idempotent upsert and lifecycle of vectors in Qdrant with persistent disk fallback."""

    def __init__(self, url: Optional[str] = None, collection_name: str = "documents"):
        self.collection_name = collection_name
        self.url = url or settings.qdrant_url
        self._client: Optional[QdrantClient] = None

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            self._client = self._init_client()
            try:
                ensure_collection(
                    self._client,
                    collection_name=self.collection_name,
                    vector_size=settings.embedding_dim,
                )
            except Exception:
                pass
        return self._client

    def _init_client(self) -> QdrantClient:
        storage_path = Path("data/qdrant_storage").resolve()
        storage_path.mkdir(parents=True, exist_ok=True)

        if "localhost:6333" in self.url or "127.0.0.1:6333" in self.url:
            if not _is_port_open("localhost", 6333):
                return QdrantClient(path=str(storage_path))

        try:
            return QdrantClient(url=self.url, timeout=1.0, prefer_grpc=False)
        except Exception:
            return QdrantClient(path=str(storage_path))

    def upsert_chunks(
        self,
        chunks: List[ChunkRecord],
        embeddings: List[List[float]],
        batch_size: int = 64,
    ) -> int:
        """Batches and upserts chunk vectors with rich provenance payload."""
        if not chunks:
            return 0

        points: List[PointStruct] = []
        for chunk, vec in zip(chunks, embeddings):
            point_id = _deterministic_point_id(chunk.chunk_id)
            payload = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.content,
                **chunk.metadata,
            }
            points.append(PointStruct(id=point_id, vector=vec, payload=payload))

        total_upserted = 0
        for batch in batch_items(points, batch_size):
            self.client.upsert(collection_name=self.collection_name, points=batch)
            total_upserted += len(batch)

        return total_upserted

    def delete_by_document_id(self, document_id: str) -> None:
        """Removes existing vectors for a document before re-indexing."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
        )


default_vector_store = QdrantVectorStore()
