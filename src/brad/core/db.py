"""Lazy database engine and session factory."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from brad.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """Create and cache the SQLAlchemy engine on first use."""
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=False,
    )


def get_session_factory() -> sessionmaker:
    """Return a sessionmaker bound to the lazy engine."""
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    """Yield a transactional session; commit on success, rollback on error."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
