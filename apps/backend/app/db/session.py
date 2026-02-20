from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base

_ENGINE = None
_SessionLocal = None


def init_db(database_url: str) -> None:
    global _ENGINE, _SessionLocal
    _ENGINE = create_engine(database_url, pool_pre_ping=True)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_ENGINE)

    # Ensure models are registered before creating tables.
    from app import models  # noqa: F401

    # TODO: replace with Alembic migrations for production use.
    Base.metadata.create_all(bind=_ENGINE)


def get_session() -> Generator[Session, None, None]:
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized")
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()
