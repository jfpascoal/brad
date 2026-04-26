import os
import urllib.parse
from functools import lru_cache
from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        secrets_dir=os.environ.get("BRAD_SECRETS_DIR", "/run/secrets"),
        case_sensitive=False,
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
        encoded_password = urllib.parse.quote_plus(self.postgres_password)
        return (
            f"postgresql+psycopg://{self.postgres_user}:{encoded_password}"
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
