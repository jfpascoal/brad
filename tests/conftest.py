import os
from collections.abc import Generator
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from brad.core.config import Settings, get_settings
from brad.core.models.base import Base


@pytest.fixture(autouse=True)
def mock_env() -> Generator[None, None, None]:
    """Mock environment variables securely for all tests."""
    with patch.dict(
        os.environ,
        {
            "POSTGRES_USER": "test_user",
            "POSTGRES_PASSWORD": "test_password",
            "POSTGRES_DB": "test_db",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "BRAD_SEED_DIR": "/tmp/seed",
            "BRAD_BACKUP_DIR": "/tmp/backup",
        },
        clear=True,
    ):
        # Clear the lru_cache on get_settings so it re-reads the mocked environment
        get_settings.cache_clear()
        yield


@pytest.fixture(scope="session")
def engine():
    """Create a highly isolated, in-memory SQLite engine for the test session."""
    # We use SQLite for speed and isolation. SQLAlchemy abstracts the dialect differences well enough for our CRUD tests.
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    """Provide a transactional workspace for each test that rolls back automatically."""
    connection = engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def settings() -> Settings:
    return get_settings()
