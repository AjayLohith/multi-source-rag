from typing import Any, List, Optional
from app.config import settings


class EmbeddingModel:
    """Wrapper around SentenceTransformer with lazy model loading and batching."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.embedding_model
        self._model: Optional[Any] = None

    @property
    def model(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_documents(self, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        if not texts:
            return []
        bs = batch_size or settings.embedding_batch_size
        embeddings = self.model.encode(
            texts,
            batch_size=bs,
            normalize_embeddings=settings.normalize_embeddings,
            show_progress_bar=False,
        )
        return [vec.tolist() for vec in embeddings]

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode(
            text,
            normalize_embeddings=settings.normalize_embeddings,
            show_progress_bar=False,
        )
        return embedding.tolist()


# Global default instance
default_embedding_model = EmbeddingModel()
