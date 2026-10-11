from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings
from app.llm import get_llm_provider
from app.retrieval.retriever import default_retriever

router = APIRouter(prefix="", tags=["Chat"])


class ChatRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None
    provider: Optional[str] = None


@router.post("/chat")
async def chat_rag(payload: ChatRequest):
    """
    End-to-end RAG chat endpoint:
    1. Normalizes query & performs semantic vector retrieval from Qdrant.
    2. Builds grounded context window with provenance tags.
    3. Prompts LLM provider (Groq / Gemini / Mistral / Ollama).
    4. Returns verified answer with traceable source citations.
    """
    # 1. Retrieve candidates
    results = default_retriever.retrieve(
        query=payload.query,
        top_k=payload.top_k,
        filters=payload.filters,
    )

    # 2. Build context
    context_str, citations = default_retriever.build_context(results)

    # 3. LLM Generation
    provider = get_llm_provider(payload.provider)
    answer = await provider.generate(query=payload.query, context=context_str)

    return {
        "query": payload.query,
        "answer": answer,
        "citations": citations,
        "provider": payload.provider or settings.llm_provider,
        "evidence_count": len(citations),
    }
