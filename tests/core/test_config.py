import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from brad.core.config import Settings


def test_settings_load_from_mock_env(settings):
    """Ensure settings correctly load the values established in conftest.py's mock_env."""
    assert settings.postgres_user == "test_user"
    assert settings.postgres_host == "localhost"
    assert settings.postgres_port == 5432
    assert settings.seed_dir.name == "seed"


def test_missing_required_env_var_raises_validation_error():
    """Ensure Pydantic settings fail if critical DB config is missing."""
    with patch.dict(os.environ, clear=True):
        with pytest.raises(ValidationError) as exc:
            Settings()

        errors = str(exc.value)
        assert "postgres_user" in errors
        assert "postgres_password" in errors


@pytest.mark.parametrize(
    "host, port, expected_dsn",
    [
        (
            "localhost",
            "5432",
            "postgresql+psycopg://test_user:test_password@localhost:5432/test_db",
        ),
        (
            "db.internal.net",
            "5433",
            "postgresql+psycopg://test_user:test_password@db.internal.net:5433/test_db",
        ),
    ],
)
def test_database_url_computation(host, port, expected_dsn):
    """Ensure the computed database_url property builds correctly."""
    with patch.dict(os.environ, {"POSTGRES_HOST": host, "POSTGRES_PORT": port}):
        s = Settings()
        assert s.database_url == expected_dsn
