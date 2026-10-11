from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract interface for LLM backends (Groq, Gemini, Mistral/Ollama)."""

    @abstractmethod
    async def generate(self, query: str, context: str) -> str:
        """Generates a grounded completion from the query and context."""
        raise NotImplementedError
