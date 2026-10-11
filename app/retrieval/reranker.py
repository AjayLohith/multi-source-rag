from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseReranker(ABC):
    @abstractmethod
    def rerank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        raise NotImplementedError


class NoOpReranker(BaseReranker):
    """Pass-through reranker for zero-latency / local zero-cost mode."""

    def rerank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return results


class SimpleScoreReranker(BaseReranker):
    """Sorts results by similarity score and term frequency overlap."""

    def rerank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        query_words = set(query.lower().split())

        def scoring(item):
            text_words = set(item.get("text", "").lower().split())
            overlap = len(query_words.intersection(text_words))
            return item.get("score", 0.0) + (overlap * 0.05)

        return sorted(results, key=scoring, reverse=True)
