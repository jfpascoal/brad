import unittest
from unittest.mock import patch, MagicMock

from brad.main import parse_args, initialize_db, load_history, MethodOptions
from brad.sql.schema import ACCOUNT_BALANCES, PRODUCT_VALUES, ACCOUNTS, FINANCIAL_PRODUCTS


class TestParseArgs(unittest.TestCase):
    """
    Tests for the parse_args function.
    """

    @patch('sys.argv', ['brad', 'db_init'])
    def test_parse_args_basic(self):
        """Test parsing basic command line arguments."""
        args = parse_args()

        self.assertEqual('db_init', args.method)
        self.assertEqual([], args.options)

    @patch('sys.argv', ['brad', 'db_init', '-f', '--no-seed'])
    def test_parse_args_with_options(self):
        """Test parsing command line arguments with options."""
        args = parse_args()

        self.assertEqual('db_init', args.method)
        self.assertEqual(['-f', '--no-seed'], args.options)


class TestMethodOptions(unittest.TestCase):
    """
    Tests for the MethodOptions class.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.test_opts = {
            'force': (['-f', '--force'], bool, "Force action"),
            'no_seed': (['--no-seed'], bool, "Skip seeding"),
            'count': (['-c', '--count'], int, "Set count value")
        }
        self.options = MethodOptions(self.test_opts)

    def test_initialization(self):
        """Test MethodOptions initialization."""
        # Check that attributes are initialized with default values
        self.assertFalse(self.options.force)
        self.assertFalse(self.options.no_seed)
        self.assertEqual(0, self.options.count)

    def test_flag_list(self):
        """Test flag_list method returns all valid flags."""
        expected_flags = ['-f', '--force', '--no-seed', '-c', '--count']
        self.assertEqual(set(expected_flags), set(self.options.flag_list()))

    def test_valid_opts(self):
        """Test valid_opts method returns formatted option descriptions."""
        result = self.options.valid_opts()
        self.assertIn('-f,\t--force: Force action', result)
        self.assertIn('--no-seed: Skip seeding', result)
        self.assertIn('-c,\t--count: Set count value', result)

    def test_set_boolean_flags(self):
        """Test setting boolean flag options."""
        self.options.set(['-f', '--no-seed'])

        self.assertTrue(self.options.force)
        self.assertTrue(self.options.no_seed)
        self.assertEqual(0, self.options.count)  # Should remain default

    @patch('brad.main.logger')
    def test_set_unknown_flag_warning(self, mock_logger):
        """Test warning is printed for unknown flags."""
        self.options.set(['--unknown-flag'])

        mock_logger.warning.assert_called_with("Unknown option '--unknown-flag'.")

    def test_set_value_option(self):
        """Test setting value-based options."""
        self.options.set(['-c', '42'])

        self.assertEqual(42, self.options.count)
        self.assertFalse(self.options.force)  # Should remain default

    @patch('brad.main.logger')
    def test_set_value_without_flag_warning(self, mock_logger):
        """Test warning for value without preceding option."""
        self.options.set(['42'])

        mock_logger.warning.assert_called_with("Value '42' without a preceding option.")

    def test_set_mixed_options(self):
        """Test setting mixed boolean and value options."""
        self.options.set(['-f', '-c', '10', '--no-seed'])

        self.assertTrue(self.options.force)
        self.assertTrue(self.options.no_seed)
        self.assertEqual(10, self.options.count)


@patch('brad.main.create_schema')
@patch('brad.main.DatabaseManager')
class TestInitializeDb(unittest.TestCase):
    """
    Tests for the initialize_db function.
    """

    def test_initialize_db_default_behavior(self, mock_db_manager, mock_create_schema):
        """Test default behavior seeds data without flags."""
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance

        result = initialize_db([])

        mock_db_manager.assert_called_once()
        mock_create_schema.assert_called_once_with(mock_db_instance, force=False, seed=True)
        self.assertEqual(mock_db_instance, result)

    def test_initialize_db_with_force_flag(self, mock_db_manager, mock_create_schema):
        """Test force flag handling."""
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance

        result = initialize_db(['-f'])

        mock_db_manager.assert_called_once()
        mock_create_schema.assert_called_once_with(mock_db_instance, force=True, seed=True)
        self.assertEqual(mock_db_instance, result)

    def test_initialize_db_with_force_long_flag(self, mock_db_manager, mock_create_schema):
        """Test --force flag handling."""
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance

        result = initialize_db(['--force'])

        mock_db_manager.assert_called_once()
        mock_create_schema.assert_called_once_with(mock_db_instance, force=True, seed=True)
        self.assertEqual(mock_db_instance, result)

    def test_initialize_db_with_no_seed_flag(self, mock_db_manager, mock_create_schema):
        """Test --no-seed flag disables seeding."""
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance

        result = initialize_db(['--no-seed'])

        mock_db_manager.assert_called_once()
        mock_create_schema.assert_called_once_with(mock_db_instance, force=False, seed=False)
        self.assertEqual(mock_db_instance, result)

    def test_initialize_db_with_both_flags(self, mock_db_manager, mock_create_schema):
        """Test both force and no-seed flags together."""
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance

        result = initialize_db(['-f', '--no-seed'])

        mock_db_manager.assert_called_once()
        mock_create_schema.assert_called_once_with(mock_db_instance, force=True, seed=False)
        self.assertEqual(mock_db_instance, result)

    def test_initialize_db_with_unknown_option(self, mock_db_manager, mock_create_schema):
        """Test warning is printed for unknown options."""
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance

        result = initialize_db(['--unknown-option'])

        mock_db_manager.assert_called_once()
        mock_create_schema.assert_called_once_with(mock_db_instance, force=False, seed=True)
        self.assertEqual(mock_db_instance, result)


@patch('brad.main.get_reference_data')
@patch('brad.main.backup_data')
@patch('brad.main.write_to_db')
@patch('brad.main.ingest_from_excel')
@patch('brad.main.DatabaseManager')
class TestLoadHistory(unittest.TestCase):
    """
    Tests for the load_history function.
    """

    def setUp(self):
        """Set up test fixtures."""
        # Mock database instance
        self.mock_db_instance = MagicMock()

        # Mock data fixtures
        self.simple_mock_data = {'test': 'data'}
        self.empty_schema_data = {ACCOUNT_BALANCES: [], PRODUCT_VALUES: []}
        self.history_data_with_content = {ACCOUNT_BALANCES: [{'history': 'data'}], PRODUCT_VALUES: []}
        self.reference_data_with_content = {ACCOUNTS: [{'ref': 'data'}], FINANCIAL_PRODUCTS: []}
        self.reference_data_no_content = {ACCOUNTS: [], FINANCIAL_PRODUCTS: []}
        self.test_data_flow_data = {
            ACCOUNT_BALANCES: [{'account': 'test', 'amount': 100}],
            PRODUCT_VALUES: [{'product': 'fund', 'value': 500}]
        }

    def test_load_history_no_options(self, mock_db_manager, mock_ingest, mock_write, mock_backup, mock_get_ref):
        """Test load_history with no command line options."""
        mock_db_manager.return_value = self.mock_db_instance
        mock_ingest.return_value = self.simple_mock_data

        load_history([])

        mock_db_manager.assert_called_once()
        mock_ingest.assert_called_once_with(history_file='')
        mock_get_ref.assert_not_called()  # Should not be called when no --load-reference
        mock_write.assert_called_once_with(db=self.mock_db_instance, data=self.simple_mock_data)
        mock_backup.assert_called_once_with(backup_file_name='history', data=self.simple_mock_data, source='excel',
                                            fmt='json')

    def test_load_history_with_file_option(self, mock_db_manager, mock_ingest, mock_write, mock_backup, mock_get_ref):
        """Test load_history with file option."""
        mock_db_manager.return_value = self.mock_db_instance
        mock_ingest.return_value = self.empty_schema_data

        load_history(['--file', '/path/to/test.xlsx'])

        mock_db_manager.assert_called_once()
        mock_ingest.assert_called_once_with(history_file='/path/to/test.xlsx')
        mock_get_ref.assert_not_called()  # Should not be called when no --load-reference
        mock_write.assert_called_once_with(db=self.mock_db_instance, data=self.empty_schema_data)
        mock_backup.assert_called_once_with(backup_file_name='history', data=self.empty_schema_data, source='excel',
                                            fmt='json')

    def test_load_history_with_reference_option(self, mock_db_manager, mock_ingest, mock_write, mock_backup,
                                                mock_get_ref):
        """Test load_history with load-reference option."""
        mock_db_manager.return_value = self.mock_db_instance
        mock_ingest.return_value = self.history_data_with_content
        mock_get_ref.return_value = self.reference_data_with_content

        load_history(['--load-reference'])

        mock_db_manager.assert_called_once()
        mock_ingest.assert_called_once_with(history_file='')
        mock_get_ref.assert_called_once_with(with_history_transactions=True)

        # Check that data was merged - history data should be updated with reference data
        expected_merged_data = self.history_data_with_content.copy()
        expected_merged_data.update(self.reference_data_with_content)
        mock_write.assert_called_once_with(db=self.mock_db_instance, data=expected_merged_data)
        mock_backup.assert_called_once_with(backup_file_name='history', data=expected_merged_data, source='excel',
                                            fmt='json')

    def test_load_history_with_both_options(self, mock_db_manager, mock_ingest, mock_write, mock_backup, mock_get_ref):
        """Test load_history with both file and load-reference options."""
        mock_db_manager.return_value = self.mock_db_instance
        mock_ingest.return_value = self.history_data_with_content
        mock_get_ref.return_value = self.reference_data_with_content

        load_history(['--file', '/path/to/test.xlsx', '--load-reference'])

        mock_db_manager.assert_called_once()
        mock_ingest.assert_called_once_with(history_file='/path/to/test.xlsx')
        mock_get_ref.assert_called_once_with(with_history_transactions=True)

        # Check that data was merged
        expected_merged_data = self.history_data_with_content.copy()
        expected_merged_data.update(self.reference_data_with_content)
        mock_write.assert_called_once_with(db=self.mock_db_instance, data=expected_merged_data)
        mock_backup.assert_called_once_with(backup_file_name='history', data=expected_merged_data, source='excel',
                                            fmt='json')

    @patch('brad.main.logger')
    def test_load_history_with_unknown_option(self, mock_logger, mock_db_manager, mock_ingest, mock_write, mock_backup,
                                              mock_get_ref):
        """Test load_history with unknown options logs warning."""
        mock_db_manager.return_value = self.mock_db_instance
        mock_ingest.return_value = self.empty_schema_data

        load_history(['--unknown-option'])

        mock_logger.warning.assert_called_with("Unknown option '--unknown-option'.")
        mock_db_manager.assert_called_once()
        mock_ingest.assert_called_once_with(history_file='')
        mock_get_ref.assert_not_called()  # Should not be called when no --load-reference
        mock_write.assert_called_once_with(db=self.mock_db_instance, data=self.empty_schema_data)
        mock_backup.assert_called_once_with(backup_file_name='history', data=self.empty_schema_data, source='excel',
                                            fmt='json')

    def test_load_history_option_parsing(self, mock_db_manager, mock_ingest, mock_write, mock_backup, mock_get_ref):
        """Test that options are correctly parsed and mapped to function parameters."""
        mock_db_manager.return_value = self.mock_db_instance
        mock_ingest.return_value = self.empty_schema_data
        mock_get_ref.return_value = self.reference_data_no_content

        # Test that attribute names are correctly mapped to parameter names
        load_history(['--file', 'test.xlsx', '--load-reference'])

        # Verify that functions are called with correct parameters
        mock_ingest.assert_called_once_with(history_file='test.xlsx')
        mock_get_ref.assert_called_once_with(with_history_transactions=True)

    def test_load_history_data_flow(self, mock_db_manager, mock_ingest, mock_write, mock_backup, mock_get_ref):
        """Test that data flows correctly between functions."""
        mock_db_manager.return_value = self.mock_db_instance
        mock_ingest.return_value = self.test_data_flow_data
        mock_get_ref.return_value = {}

        load_history(['--file', 'data.xlsx'])

        # Verify that the same data returned by ingest_from_excel is passed to both write_to_db and backup_data
        mock_write.assert_called_once_with(db=self.mock_db_instance, data=self.test_data_flow_data)
        mock_backup.assert_called_once_with(backup_file_name='history', data=self.test_data_flow_data, source='excel',
                                            fmt='json')

    def test_load_history_function_execution_order(self, mock_db_manager, mock_ingest, mock_write, mock_backup,
                                                   mock_get_ref):
        """Test that functions are called in the correct order."""
        mock_db_manager.return_value = self.mock_db_instance
        mock_ingest.return_value = self.simple_mock_data
        mock_get_ref.return_value = {}

        # Use a manager to track call order
        manager = MagicMock()
        manager.attach_mock(mock_db_manager, 'db_manager')
        manager.attach_mock(mock_ingest, 'ingest')
        manager.attach_mock(mock_write, 'write')
        manager.attach_mock(mock_backup, 'backup')

        load_history([])

        # Verify the order of function calls
        expected_calls = [
            ('db_manager', (), {}),
            ('ingest', (), {'history_file': ''}),
            ('write', (), {'db': self.mock_db_instance, 'data': self.simple_mock_data}),
            ('backup', (),
             {'backup_file_name': 'history', 'data': self.simple_mock_data, 'source': 'excel', 'fmt': 'json'})
        ]

        actual_calls = [(name, args, kwargs) for name, args, kwargs in manager.mock_calls]
        self.assertEqual(expected_calls, actual_calls)


if __name__ == "__main__":
    unittest.main()
