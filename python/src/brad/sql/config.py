import os
from typing import Dict, Any, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from brad import SECRETS_DIR


class Config(BaseSettings):
    """
    PostgreSQL database connection configuration manager.
    
    Handles loading database configuration from environment variables or secrets files.
    If environment variables are not set, attempts to read configuration from files
    in the secrets directory.
    """

    host: str = Field(default='localhost')
    port: int = Field(default=5432) 
    db: Optional[str] = Field(default=None)
    user: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)

    model_config = {
        'case_sensitive': False,
        'env_prefix': 'POSTGRES_',
    }

    def __init__(self, **kwargs):
        """Initialize with validation and secrets fallback."""
        super().__init__(**kwargs)
        
        # Fallback to secrets files if required fields are None
        if not self.db or not self.user or not self.password:
            self._load_from_secrets()
    
    def _load_from_secrets(self) -> None:
        """Load missing configuration from secrets directory."""
        secrets_dir = SECRETS_DIR
        field_mapping = {
            'db': 'postgres_db.txt',
            'user': 'postgres_user.txt', 
            'password': 'postgres_password.txt'
        }
        
        for field_name, filename in field_mapping.items():
            if getattr(self, field_name) is not None:
                continue

            secret_path = os.path.join(secrets_dir, filename)
            if not os.path.exists(secret_path):
                raise RuntimeError(f"Missing configuration for 'POSTGRES_{field_name.upper()}'.")

            with open(secret_path, 'r') as f:
                setattr(self, field_name, f.read().strip())

    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        """Validate PostgreSQL port is in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError('PostgreSQL port must be between 1 and 65535')
        return v

    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        """Validate PostgreSQL host is not empty."""
        if not v or not v.strip():
            raise ValueError('PostgreSQL host cannot be empty')
        return v.strip()

    def get(self) -> Dict[str, Any]:
        """
        Returns a dictionary with PostgreSQL connection parameters.
        
        :return: Dictionary containing host, port, database, user, and password.
        """
        return {
            'host': self.host,
            'port': self.port,
            'database': self.db,
            'user': self.user,
            'password': self.password
        }


def get_connection_string() -> str:
    """
    Returns a PostgreSQL connection string.
    
    :return: Formatted PostgreSQL connection string ready for use with psycopg.
    """
    config = Config().get()
    return (f"host={config['host']} "
            f"port={config['port']} "
            f"dbname={config['database']} "
            f"user={config['user']} "
            f"password={config['password']}")
