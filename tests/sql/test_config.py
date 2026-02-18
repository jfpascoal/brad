import os
import unittest
from unittest.mock import patch, mock_open

from brad.sql.config import Config, get_connection_string


class TestConfig(unittest.TestCase):
    """
    Unit tests for the Config class and get_connection_string function.
    """

    @patch.dict(os.environ, {
        'POSTGRES_HOST': 'test_host',
        'POSTGRES_PORT': '5432',
        'POSTGRES_DB': 'test_db',
        'POSTGRES_USER': 'test_user',
        'POSTGRES_PASSWORD': 'test_password'
    })
    def test_get_with_env_variables(self):
        """
        Test that Config.get() correctly retrieves connection parameters from environment variables.
        """
        config = Config()
        expected = {
            'host': 'test_host',
            'port': 5432,
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_password'
        }
        self.assertEqual(expected, config.get())

    @patch("builtins.open", new_callable=mock_open, read_data="test_value")
    @patch("os.path.exists", return_value=True)
    @patch.dict(os.environ, {
        'POSTGRES_HOST': 'test_host',
        'POSTGRES_PORT': '5432'
    })
    def test_get_with_secrets(self, mock_exists, mock_open):
        """
        Test that Config.get() retrieves connection parameters from the secrets directory
        when environment variables are not fully set.
        """
        with patch("brad.sql.config.SECRETS_DIR", "test_secrets"):
            config = Config()
            expected = {
                'host': 'test_host',
                'port': 5432,
                'database': 'test_value',
                'user': 'test_value',
                'password': 'test_value'
            }
            self.assertEqual(expected, config.get())

    @patch("brad.sql.config.Config.get", return_value={
        'host': 'test_host',
        'port': 5432,
        'database': 'db',
        'user': 'usr',
        'password': 'pw'
    })
    def test_get_connection_string(self, mock_get):
        """
        Test that get_connection_string() generates the correct PostgreSQL connection string.
        """
        expected = (
            "host=test_host port=5432 dbname=db user=usr password=pw"
        )
        self.assertEqual(expected, get_connection_string())


if __name__ == "__main__":
    unittest.main()
