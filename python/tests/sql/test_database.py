import unittest
from unittest.mock import patch, MagicMock, call
from brad.sql.database import DatabaseManager
import psycopg2


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

    @patch('brad.sql.database.psycopg2.connect')
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

    @patch('brad.sql.database.TABLES')
    @patch('brad.sql.database.psycopg2.connect')
    @patch('builtins.print')
    def test_initialize_schema_with_seeding(self, mock_print, mock_connect, mock_tables):
        """
        Test that initialize_schema creates tables and inserts seed data by default.
        """
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_table = MagicMock()
        mock_table.name = "test_table"
        mock_table.get_create_statement.return_value = "CREATE TABLE test_table (id INT);"
        mock_table.get_insert_statement.return_value = ("INSERT INTO test_table VALUES (%s);", [('1',)])
        mock_tables.__iter__.return_value = [mock_table]
        mock_tables.__reversed__ = lambda: reversed([mock_table])
        
        db = DatabaseManager(connection_string="test_connection")
        result = db.initialize_schema()
        
        self.assertTrue(result)
        mock_cursor.execute.assert_any_call("CREATE TABLE test_table (id INT);")
        mock_cursor.executemany.assert_called_once_with("INSERT INTO test_table VALUES (%s);", [('1',)])
        mock_print.assert_called_with("Seed data inserted successfully.")

    @patch('brad.sql.database.TABLES')
    @patch('brad.sql.database.psycopg2.connect')
    @patch('builtins.print')
    def test_initialize_schema_without_seeding(self, mock_print, mock_connect, mock_tables):
        """
        Test that initialize_schema creates tables but skips seed data when seed=False.
        """
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_table = MagicMock()
        mock_table.name = "test_table"
        mock_table.get_create_statement.return_value = "CREATE TABLE test_table (id INT);"
        mock_table.get_insert_statement.return_value = ("INSERT INTO test_table VALUES (%s);", [('1',)])
        mock_tables.__iter__.return_value = [mock_table]
        mock_tables.__reversed__ = lambda: reversed([mock_table])
        
        db = DatabaseManager(connection_string="test_connection")
        result = db.initialize_schema(seed=False)
        
        self.assertTrue(result)
        mock_cursor.execute.assert_any_call("CREATE TABLE test_table (id INT);")
        mock_cursor.executemany.assert_not_called()
        mock_print.assert_called_with("Database schema initialized successfully.")

    @patch('brad.sql.database.TABLES')
    @patch('brad.sql.database.psycopg2.connect')
    def test_initialize_schema_with_force(self, mock_connect, mock_tables):
        """
        Test that initialize_schema drops tables first when force=True.
        """
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_table = MagicMock()
        mock_table.name = "test_table"
        mock_table.get_create_statement.return_value = "CREATE TABLE test_table (id INT);"
        mock_table.get_insert_statement.return_value = None
        mock_tables.__iter__.return_value = [mock_table]
        mock_tables.__reversed__ = MagicMock(return_value=reversed([mock_table]))
        
        db = DatabaseManager(connection_string="test_connection")
        result = db.initialize_schema(force=True)
        
        self.assertTrue(result)
        mock_cursor.execute.assert_any_call('DROP TABLE IF EXISTS "test_table" CASCADE;')
        mock_cursor.execute.assert_any_call("CREATE TABLE test_table (id INT);")

    @patch('brad.sql.database.DatabaseManager.get_connection')
    @patch('builtins.print')
    def test_initialize_schema_handles_database_error(self, mock_print, mock_get_connection):
        """
        Test that initialize_schema returns False when a database error occurs.
        """
        mock_get_connection.side_effect = psycopg2.Error("Database connection failed")
        
        db = DatabaseManager(connection_string="test_connection")
        result = db.initialize_schema()
        
        self.assertFalse(result)
        mock_print.assert_called_with("An error occurred during schema initialization: Database connection failed")

    @patch('brad.sql.database.psycopg2.connect')
    def test_insert_success(self, mock_connect):
        """
        Test successful insertion of data into a table.
        """
        # Setup mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        db = DatabaseManager(connection_string="test_connection")
        
        # Mock the validator to return True
        db.validator.validate = MagicMock(return_value=True)
        
        test_data = {'name': 'test', 'value': 123}
        result = db.insert('test_table', test_data)
        
        self.assertTrue(result)
        db.validator.validate.assert_called_once_with('test_table', test_data)
        expected_sql = 'INSERT INTO "test_table" ("name", "value") VALUES (%s, %s)'
        mock_cursor.execute.assert_called_once_with(expected_sql, ('test', 123))

    @patch('brad.sql.database.psycopg2.connect')
    def test_insert_validation_failure(self, mock_connect):
        """
        Test that insert returns False when validation fails.
        """
        db = DatabaseManager(connection_string="test_connection")
        
        # Mock the validator to return False
        db.validator.validate = MagicMock(return_value=False)
        
        test_data = {'name': 'test', 'value': 123}
        result = db.insert('test_table', test_data)
        
        self.assertFalse(result)
        db.validator.validate.assert_called_once_with('test_table', test_data)
        mock_connect.assert_not_called()

    @patch('brad.sql.database.DatabaseManager.get_connection')
    @patch('builtins.print')
    def test_insert_database_error(self, mock_print, mock_get_connection):
        """
        Test that insert returns False when a database error occurs.
        """
        mock_get_connection.side_effect = psycopg2.Error("Database error")
        
        db = DatabaseManager(connection_string="test_connection")
        
        # Mock the validator to return True
        db.validator.validate = MagicMock(return_value=True)
        
        test_data = {'name': 'test', 'value': 123}
        result = db.insert('test_table', test_data)
        
        self.assertFalse(result)
        mock_print.assert_called_with("Database error on insert into 'test_table': Database error")


if __name__ == "__main__":
    unittest.main()
