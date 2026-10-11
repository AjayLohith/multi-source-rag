from app.api.routes_ingest import router as ingest_router
from app.api.routes_search import router as search_router
from app.api.routes_chat import router as chat_router

__all__ = ["ingest_router", "search_router", "chat_router"]
