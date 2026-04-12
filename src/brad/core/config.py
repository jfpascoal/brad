import os
import urllib.parse
from functools import lru_cache
from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


_project_root = Path(__file__).resolve().parents[3]
_local_secrets = _project_root / "docker" / "secrets"
_default_secrets_dir = str(_local_secrets) if _local_secrets.exists() else "/run/secrets"

# Automatically map local .txt secrets to environment variables to mimic docker's behavior
if _local_secrets.exists():
    for secret_file in _local_secrets.glob("*.txt"):
        env_key = secret_file.stem.upper()
        if env_key not in os.environ:
            os.environ[env_key] = secret_file.read_text(encoding="utf-8").strip()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="",
        secrets_dir=os.environ.get("BRAD_SECRETS_DIR", _default_secrets_dir),
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str
    postgres_user: str
    postgres_password: str

    # Paths
    project_root: Path = Path(__file__).resolve().parents[3]

    @computed_field
    @property
    def database_url(self) -> str:
        """SQLAlchemy-compatible connection string."""
        user = urllib.parse.quote_plus(self.postgres_user)
        pwd = urllib.parse.quote_plus(self.postgres_password)

        return (
            f"postgresql+psycopg://{user}:{pwd}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field
    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @computed_field
    @property
    def backup_dir(self) -> Path:
        return self.data_dir / "backup"

    @computed_field
    @property
    def config_dir(self) -> Path:
        return self.project_root / "config"

    @computed_field
    @property
    def seed_dir(self) -> Path:
        return self.data_dir / "seed"


@lru_cache
def get_settings() -> Settings:
    """Cached singleton for application settings."""
    return Settings()
