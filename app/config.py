from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Infrastructure
    database_url: str = "postgresql+psycopg://rag_user:rag_pass@localhost:5432/rag_db"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"

    # Embeddings
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    normalize_embeddings: bool = True
    embedding_batch_size: int = 32

    # Chunking
    chunk_size: int = 500
    chunk_overlap: int = 50

    # LLM Providers
    llm_provider: str = "groq"
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"

    google_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"

    mistral_api_key: Optional[str] = None
    mistrl_api_key: Optional[str] = None  # accommodate common env spelling
    mistral_model: str = "mistral-small-latest"
    ollama_url: str = "http://localhost:11434"

    # Pipeline Resilience & Worker Concurrency
    max_retries: int = 3
    retry_backoff_factor: float = 1.5
    rate_limit_per_minute: int = 60
    worker_concurrency: int = 4

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()