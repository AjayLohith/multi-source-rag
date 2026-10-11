from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.database.models import Base


def _get_engine():
    db_url = settings.database_url
    if "postgres" in db_url:
        try:
            pg_engine = create_engine(db_url, connect_args={"connect_timeout": 1})
            with pg_engine.connect() as conn:
                pass
            return pg_engine
        except Exception:
            pass

    fallback_path = Path("data/rag_db.sqlite").resolve()
    fallback_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        f"sqlite:///{fallback_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )


engine = _get_engine()
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Creates all database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI session dependency."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
