from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker as SessionMakerClass

from brad.core.db import get_engine, get_session, get_session_factory


def test_get_engine_caching() -> None:
    """Test that get_engine returns the same engine and caching works."""
    get_engine.cache_clear()

    with patch("brad.core.db.create_engine") as mock_create_engine:
        mock_engine = MagicMock(spec=Engine)
        mock_create_engine.return_value = mock_engine

        # Call 1
        engine1 = get_engine()
        # Call 2
        engine2 = get_engine()

        # Verify it's exactly the same object and create_engine was called only once
        assert engine1 is engine2
        assert engine1 is mock_engine
        mock_create_engine.assert_called_once()

    get_engine.cache_clear()


def test_get_session_factory() -> None:
    """Test that session factory returns a bound sessionmaker."""
    get_engine.cache_clear()
    with patch("brad.core.db.get_engine") as mock_get_engine:
        mock_get_engine.return_value = MagicMock(spec=Engine)

        factory = get_session_factory()

        assert isinstance(factory, SessionMakerClass)
        assert factory.kw["bind"] == mock_get_engine.return_value
        assert factory.kw["expire_on_commit"] is False


def test_get_session_commits_on_success() -> None:
    """Test that get_session yields a session, then commits and closes it."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)

    with patch("brad.core.db.get_session_factory", return_value=mock_factory):
        generator = get_session()

        # Yield should return the session
        session = next(generator)
        assert session is mock_session

        # No calls to commit or close yet
        mock_session.commit.assert_not_called()
        mock_session.close.assert_not_called()

        # End iteration normally
        with pytest.raises(StopIteration):
            next(generator)

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.rollback.assert_not_called()


def test_get_session_rolls_back_on_error() -> None:
    """Test that get_session rolls back the session if an exception happens."""
    mock_session = MagicMock()
    mock_factory = MagicMock(return_value=mock_session)

    class TestException(Exception):
        pass

    with patch("brad.core.db.get_session_factory", return_value=mock_factory):
        generator = get_session()

        # Yield should return the session
        session = next(generator)
        assert session is mock_session

        # Trigger an exception inside the context block
        with pytest.raises(TestException):
            generator.throw(TestException())

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.commit.assert_not_called()
