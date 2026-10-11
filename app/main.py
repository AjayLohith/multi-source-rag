from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.database.session import init_db
from app.api import ingest_router, search_router, chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield


app = FastAPI(
    title="Multi-Source RAG Application",
    description="Production-minded ingestion, retrieval, and RAG across heterogeneous data sources.",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount API routers
app.include_router(ingest_router)
app.include_router(search_router)
app.include_router(chat_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "multi-source RAG",
        "llm_provider": settings.llm_provider,
        "embedding_model": settings.embedding_model,
    }
