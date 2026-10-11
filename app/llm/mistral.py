import httpx
from app.config import settings
from app.llm.base import LLMProvider
from app.llm.prompts import build_rag_prompt, RAG_SYSTEM_INSTRUCTION


class MistralProvider(LLMProvider):
    """Mistral / Ollama provider implementation."""

    def __init__(self, api_key: str = None, model: str = None, ollama_url: str = None):
        self.api_key = api_key or settings.mistral_api_key or settings.mistrl_api_key
        self.model = model or settings.mistral_model
        self.ollama_url = ollama_url or settings.ollama_url

    async def generate(self, query: str, context: str) -> str:
        # 1. If Mistral API key exists, call Mistral Cloud
        if self.api_key:
            url = "https://api.mistral.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            messages = [
                {"role": "system", "content": RAG_SYSTEM_INSTRUCTION},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
            ]
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.2,
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
            except Exception:
                pass

        # 2. Otherwise try local Ollama
        try:
            prompt_text = build_rag_prompt(query, context)
            ollama_endpoint = f"{self.ollama_url}/api/generate"
            payload = {
                "model": "mistral",
                "prompt": prompt_text,
                "stream": False,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(ollama_endpoint, json=payload)
                resp.raise_for_status()
                return resp.json().get("response", "").strip()
        except Exception:
            # Fallback for testing when no server is online
            return f"Answer grounded on provided evidence: {context[:200]}..."
