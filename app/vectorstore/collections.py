from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


def ensure_collection(
    client: QdrantClient,
    collection_name: str = "documents",
    vector_size: int = 384,
) -> None:
    """Ensures the primary Qdrant collection exists with appropriate dimensionality."""
    collections = [c.name for c in client.get_collections().collections]
    if collection_name not in collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
