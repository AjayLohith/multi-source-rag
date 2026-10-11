from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.retrieval.retriever import default_retriever

router = APIRouter(prefix="", tags=["Search"])


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None


@router.post("/search")
async def search_evidence(payload: SearchRequest):
    """
    Retrieval-only diagnostic endpoint for inspecting vector search
    scores, extracted snippets, and source metadata without invoking an LLM.
    """
    results = default_retriever.retrieve(
        query=payload.query,
        top_k=payload.top_k,
        filters=payload.filters,
    )
    context_str, citations = default_retriever.build_context(results)

    return {
        "query": payload.query,
        "results_count": len(results),
        "citations": citations,
        "assembled_context": context_str,
    }
