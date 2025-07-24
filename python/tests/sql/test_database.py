import unittest
from unittest.mock import patch, MagicMock

from brad.sql.database import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """
    Unit tests for the DatabaseManager class.
    """

    @patch('brad.sql.database.get_connection_string')
    def test_init_with_default_connection_string(self, mock_get_connection_string):
        """
        Test that DatabaseManager initializes with default connection string when none is provided.
        """
        mock_get_connection_string.return_value = "test_connection_string"
        db = DatabaseManager()

        self.assertEqual("test_connection_string", db.connection_string)
        mock_get_connection_string.assert_called_once()

    def test_init_with_custom_connection_string(self):
        """
        Test that DatabaseManager initializes with custom connection string when provided.
        """
        custom_connection = "custom_connection_string"
        db = DatabaseManager(connection_string=custom_connection)

        self.assertEqual(custom_connection, db.connection_string)

    @patch('brad.sql.database.psycopg.connect')
    def test_get_connection(self, mock_connect):
        """
        Test that get_connection establishes a database connection using the connection string.
        """
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        db = DatabaseManager(connection_string="test_connection")
        result = db.get_connection()

        mock_connect.assert_called_once_with("test_connection")
        self.assertEqual(mock_connection, result)

    @patch('brad.sql.database.psycopg.connect')
    def test_execute_query_without_params(self, mock_connect):
        """
        Test that execute_query executes a query without parameters.
        """
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        db = DatabaseManager(connection_string="test_connection")
        db.execute_query("SELECT * FROM test_table")

        mock_cursor.execute.assert_called_once_with("SELECT * FROM test_table", None)

    @patch('brad.sql.database.psycopg.connect')
    def test_execute_query_with_params(self, mock_connect):
        """
        Test that execute_query executes a query with parameters.
        """
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        db = DatabaseManager(connection_string="test_connection")
        params = ("test_value",)
        db.execute_query("SELECT * FROM test_table WHERE name = %s", params)

        mock_cursor.execute.assert_called_once_with("SELECT * FROM test_table WHERE name = %s", params)

    @patch('brad.sql.database.psycopg.connect')
    def test_execute_many(self, mock_connect):
        """
        Test that execute_many executes a query with multiple parameter sets.
        """
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        db = DatabaseManager(connection_string="test_connection")
        data = [("value1",), ("value2",), ("value3",)]
        db.execute_many("INSERT INTO test_table (name) VALUES (%s)", data)

        mock_cursor.executemany.assert_called_once_with("INSERT INTO test_table (name) VALUES (%s)", data)

    @patch('brad.sql.database.psycopg.connect')
    def test_execute_as_transaction(self, mock_connect):
        """
        Test that execute_as_transaction executes multiple queries in a transaction.
        """
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        db = DatabaseManager(connection_string="test_connection")
        queries = [
            ("INSERT INTO table1 (name) VALUES (%s)", ("value1",)),
            ("UPDATE table2 SET active = %s WHERE id = %s", (True, 1)),
            ("DELETE FROM table3 WHERE status = %s", ("inactive",))
        ]
        db.execute_as_transaction(queries)

        # Verify all queries were executed
        expected_calls = [
            unittest.mock.call("INSERT INTO table1 (name) VALUES (%s)", ("value1",)),
            unittest.mock.call("UPDATE table2 SET active = %s WHERE id = %s", (True, 1)),
            unittest.mock.call("DELETE FROM table3 WHERE status = %s", ("inactive",))
        ]
        mock_cursor.execute.assert_has_calls(expected_calls)

    @patch('brad.sql.database.psycopg.connect')
    def test_connection_context_manager(self, mock_connect):
        """
        Test that database connections are properly managed using context managers.
        """
        mock_connection = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_connection

        db = DatabaseManager(connection_string="test_connection")
        db.execute_query("SELECT 1")

        # Verify connection was used as context manager
        mock_connect.return_value.__enter__.assert_called()
        mock_connect.return_value.__exit__.assert_called()


if __name__ == "__main__":
    unittest.main()
