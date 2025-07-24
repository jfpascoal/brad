import unittest
from unittest.mock import patch, MagicMock

from brad.sql.database import DatabaseManager
from brad.sql.schema import get_all_tables, create_schema, drop_schema


class TestSchemaModule(unittest.TestCase):
    """Tests for the schema module functions and structure."""

    def test_get_all_tables_returns_list(self):
        """Test that get_all_tables returns a non-empty list of Table objects."""
        tables = get_all_tables()
        self.assertIsInstance(tables, list)
        self.assertGreater(len(tables), 0)
        # Check that all items are Table objects
        from brad.sql.objects import Table
        for table in tables:
            self.assertIsInstance(table, Table)

    @patch('brad.sql.schema.logger')
    def test_create_schema_success(self, mock_logger):
        """Test successful schema creation."""
        mock_db = MagicMock(spec=DatabaseManager)
        mock_connection = MagicMock()
        mock_db.get_connection.return_value.__enter__.return_value = mock_connection

        create_schema(mock_db, force=True, seed=True)

        # Verify connection was used
        mock_db.get_connection.assert_called_once()
        mock_connection.commit.assert_called_once()

    @patch('brad.sql.schema.logger')
    def test_create_schema_handles_exception(self, mock_logger):
        """Test that create_schema handles exceptions properly."""
        mock_db = MagicMock(spec=DatabaseManager)
        mock_connection = MagicMock()
        mock_db.get_connection.return_value.__enter__.return_value = mock_connection

        # Mock table creation to raise an exception
        with patch('brad.sql.schema.get_all_tables') as mock_get_tables:
            mock_table = MagicMock()
            mock_table.create.side_effect = Exception("Database error")
            mock_get_tables.return_value = [mock_table]

            with self.assertRaises(Exception):
                create_schema(mock_db)

            mock_connection.rollback.assert_called_once()
            mock_logger.error.assert_called_once()

    @patch('brad.sql.schema.logger')
    def test_drop_schema_success(self, mock_logger):
        """Test successful schema dropping."""
        mock_db = MagicMock(spec=DatabaseManager)
        mock_connection = MagicMock()
        mock_db.get_connection.return_value.__enter__.return_value = mock_connection

        drop_schema(mock_db)

        # Verify connection was used
        mock_db.get_connection.assert_called_once()
        mock_connection.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
