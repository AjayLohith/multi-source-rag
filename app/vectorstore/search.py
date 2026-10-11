from typing import Any, Dict, List, Optional
from qdrant_client.models import FieldCondition, Filter, MatchValue
from app.vectorstore.qdrant import QdrantVectorStore, default_vector_store


def build_qdrant_filter(filters: Optional[Dict[str, Any]] = None) -> Optional[Filter]:
    """Constructs a Qdrant Filter object from key-value filter conditions."""
    if not filters:
        return None

    conditions = []
    for key, val in filters.items():
        if val is not None:
            conditions.append(
                FieldCondition(key=key, match=MatchValue(value=val))
            )

    return Filter(must=conditions) if conditions else None


def search_vectors(
    query_vector: List[float],
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None,
    vector_store: Optional[QdrantVectorStore] = None,
) -> List[Dict[str, Any]]:
    """Performs similarity search with metadata filtering on Qdrant."""
    store = vector_store or default_vector_store
    qdrant_filter = build_qdrant_filter(filters)

    try:
        # Use query_points (modern qdrant-client) or search
        if hasattr(store.client, "query_points"):
            response = store.client.query_points(
                collection_name=store.collection_name,
                query=query_vector,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True,
            )
            points = response.points
        else:
            points = store.client.search(
                collection_name=store.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True,
            )
    except Exception as exc:
        return []

    results = []
    for p in points:
        payload = p.payload or {}
        results.append(
            {
                "point_id": str(p.id),
                "score": float(p.score) if hasattr(p, "score") and p.score is not None else 0.0,
                "text": payload.get("text", ""),
                "chunk_id": payload.get("chunk_id"),
                "document_id": payload.get("document_id"),
                "source_type": payload.get("source_type"),
                "source_name": payload.get("source_name"),
                "metadata": payload,
            }
        )

    return results
