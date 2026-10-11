import httpx
from app.config import settings
from app.llm.base import LLMProvider
from app.llm.prompts import RAG_SYSTEM_INSTRUCTION


class GroqProvider(LLMProvider):
    """Groq API client implementation."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_model

    async def generate(self, query: str, context: str) -> str:
        if not self.api_key:
            return f"(Groq API key not configured. Mock answer from context: {context[:200]}...)"

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = [
            {"role": "system", "content": RAG_SYSTEM_INSTRUCTION},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}",
            },
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1024,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
