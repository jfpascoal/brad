import os
from typing import Dict, Any

from brad.sql import SECRETS_DIR


class Config:
    """
    PostgreSQL database connection configuration manager.
    
    Handles loading database configuration from environment variables or secrets files.
    If environment variables are not set, attempts to read configuration from files
    in the secrets directory.
    """

    def __init__(self):
        # Initialize with environment variables or secrets
        self.POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
        self.POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
        self.POSTGRES_DB = os.getenv('POSTGRES_DB', None)
        self.POSTGRES_USER = os.getenv('POSTGRES_USER', None)
        self.POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', None)

        # If not set, read from secrets directory (when running locally)
        if not self.POSTGRES_DB or not self.POSTGRES_USER or not self.POSTGRES_PASSWORD:
            secrets_dir = SECRETS_DIR
            for param in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"):
                if getattr(self, param) is not None:
                    continue

                secret_path = os.path.join(secrets_dir, f'{param}.txt'.lower())
                if not os.path.exists(secret_path):
                    raise RuntimeError(f"Missing configuration for {param}.")

                with open(secret_path, 'r') as f:
                    setattr(self, param, f.read().strip())

    def get(self) -> Dict[str, Any]:
        """
        Returns a dictionary with PostgreSQL connection parameters.
        
        :return: Dictionary containing host, port, database, user, and password.
        """
        return {
            'host': self.POSTGRES_HOST,
            'port': self.POSTGRES_PORT,
            'database': self.POSTGRES_DB,
            'user': self.POSTGRES_USER,
            'password': self.POSTGRES_PASSWORD
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
