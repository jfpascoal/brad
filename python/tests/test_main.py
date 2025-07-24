import re
import unittest
from unittest.mock import patch, MagicMock
from brad.main import parse_args, initialize_db, MethodOptions


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


class TestInitializeDb(unittest.TestCase):
    """
    Tests for the initialize_db function.
    """

    @patch('brad.main.create_schema')
    @patch('brad.main.DatabaseManager')
    def test_initialize_db_default_behavior(self, mock_db_manager, mock_create_schema):
        """Test default behavior seeds data without flags."""
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance

        result = initialize_db([])
        
        mock_db_manager.assert_called_once()
        mock_create_schema.assert_called_once_with(mock_db_instance, force=False, seed=True)
        self.assertEqual(mock_db_instance, result)

    @patch('brad.main.create_schema')
    @patch('brad.main.DatabaseManager')
    def test_initialize_db_with_force_flag(self, mock_db_manager, mock_create_schema):
        """Test force flag handling."""
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance
        
        result = initialize_db(['-f'])
        
        mock_db_manager.assert_called_once()
        mock_create_schema.assert_called_once_with(mock_db_instance, force=True, seed=True)
        self.assertEqual(mock_db_instance, result)

    @patch('brad.main.create_schema')
    @patch('brad.main.DatabaseManager')
    def test_initialize_db_with_force_long_flag(self, mock_db_manager, mock_create_schema):
        """Test --force flag handling."""
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance
        
        result = initialize_db(['--force'])
        
        mock_db_manager.assert_called_once()
        mock_create_schema.assert_called_once_with(mock_db_instance, force=True, seed=True)
        self.assertEqual(mock_db_instance, result)

    @patch('brad.main.create_schema')
    @patch('brad.main.DatabaseManager')
    def test_initialize_db_with_no_seed_flag(self, mock_db_manager, mock_create_schema):
        """Test --no-seed flag disables seeding."""
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance
        
        result = initialize_db(['--no-seed'])
        
        mock_db_manager.assert_called_once()
        mock_create_schema.assert_called_once_with(mock_db_instance, force=False, seed=False)
        self.assertEqual(mock_db_instance, result)

    @patch('brad.main.create_schema')
    @patch('brad.main.DatabaseManager')
    def test_initialize_db_with_both_flags(self, mock_db_manager, mock_create_schema):
        """Test both force and no-seed flags together."""
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance
        
        result = initialize_db(['-f', '--no-seed'])
        
        mock_db_manager.assert_called_once()
        mock_create_schema.assert_called_once_with(mock_db_instance, force=True, seed=False)
        self.assertEqual(mock_db_instance, result)

    @patch('brad.main.create_schema')
    @patch('brad.main.DatabaseManager')
    def test_initialize_db_with_unknown_option(self, mock_db_manager, mock_create_schema):
        """Test warning is printed for unknown options."""
        mock_db_instance = MagicMock()
        mock_db_manager.return_value = mock_db_instance
        
        result = initialize_db(['--unknown-option'])
        
        mock_db_manager.assert_called_once()
        mock_create_schema.assert_called_once_with(mock_db_instance, force=False, seed=True)
        self.assertEqual(mock_db_instance, result)


if __name__ == "__main__":
    unittest.main()
