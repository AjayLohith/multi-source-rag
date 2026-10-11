from typing import Optional
from app.config import settings
from app.llm.base import LLMProvider
from app.llm.groq import GroqProvider
from app.llm.gemini import GeminiProvider
from app.llm.mistral import MistralProvider
from app.llm.prompts import build_rag_prompt, RAG_SYSTEM_INSTRUCTION


def get_llm_provider(name: Optional[str] = None) -> LLMProvider:
    """Factory creating configured LLM provider instance."""
    provider_name = (name or settings.llm_provider).lower()

    if provider_name == "groq":
        return GroqProvider()
    elif provider_name in ("gemini", "google"):
        return GeminiProvider()
    elif provider_name in ("mistral", "ollama"):
        return MistralProvider()
    else:
        # Default fallback
        return GroqProvider()


__all__ = [
    "LLMProvider",
    "GroqProvider",
    "GeminiProvider",
    "MistralProvider",
    "build_rag_prompt",
    "RAG_SYSTEM_INSTRUCTION",
    "get_llm_provider",
]
