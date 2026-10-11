from typing import Any, Dict, List, Optional, Tuple
from app.embeddings.model import default_embedding_model, EmbeddingModel
from app.vectorstore.qdrant import default_vector_store, QdrantVectorStore
from app.vectorstore.search import search_vectors
from app.retrieval.reranker import BaseReranker, SimpleScoreReranker


class MultiSourceRetriever:
    """Retrieves relevant evidence from heterogeneous sources with citations."""

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        vector_store: Optional[QdrantVectorStore] = None,
        reranker: Optional[BaseReranker] = None,
    ):
        self.embedding_model = embedding_model or default_embedding_model
        self.vector_store = vector_store or default_vector_store
        self.reranker = reranker or SimpleScoreReranker()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        clean_query = query.strip()
        query_vector = self.embedding_model.embed_query(clean_query)
        raw_results = search_vectors(
            query_vector=query_vector,
            top_k=top_k * 2 if self.reranker else top_k,
            filters=filters,
            vector_store=self.vector_store,
        )

        reranked = self.reranker.rerank(clean_query, raw_results)
        return reranked[:top_k]

    def build_context(
        self,
        results: List[Dict[str, Any]],
        max_chars: int = 4000,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Assembles bounded context string with source attribution headers
        and structured citation references.
        """
        context_blocks = []
        citations = []
        accumulated_chars = 0

        for idx, item in enumerate(results):
            text = item.get("text", "").strip()
            if not text:
                continue

            if accumulated_chars + len(text) > max_chars and context_blocks:
                break

            source_name = item.get("source_name") or item.get("metadata", {}).get("source_name", "Unknown Source")
            source_type = item.get("source_type") or item.get("metadata", {}).get("source_type", "unknown")
            page = item.get("metadata", {}).get("page_number") or item.get("metadata", {}).get("page")
            row = item.get("metadata", {}).get("row_index")

            location_tag = ""
            if page is not None:
                location_tag = f" | Page: {page}"
            elif row is not None:
                location_tag = f" | Row: {row}"

            citation_num = idx + 1
            header = f"[Source {citation_num}: {source_name} ({source_type}){location_tag}]"
            context_blocks.append(f"{header}\n{text}")
            accumulated_chars += len(header) + len(text)

            citations.append({
                "citation_id": citation_num,
                "source_name": source_name,
                "source_type": source_type,
                "document_id": item.get("document_id"),
                "chunk_id": item.get("chunk_id"),
                "location": location_tag.strip(" |"),
                "snippet": text[:200],
            })

        full_context = "\n\n".join(context_blocks)
        return full_context, citations


default_retriever = MultiSourceRetriever()
