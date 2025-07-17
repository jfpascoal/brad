import unittest
from unittest.mock import patch
import io
from decimal import Decimal

# Import the shared test data from the package's __init__.py
from . import TEST_TABLES
from bread.sql.validation import DataValidator


class TestDataValidator(unittest.TestCase):
    """
    Unit tests for the DataValidator class using a custom schema.
    """

    def setUp(self):
        """
        Set up a new DataValidator instance for each test.
        """
        # Use the shared TEST_TABLES imported from the package
        self.validator = DataValidator(tables=TEST_TABLES)

    def test_valid_data(self):
        """
        Tests validation with a valid data object.
        """
        valid_data = {'name': 'Alice', 'age': 30}
        # Use patch to suppress print output during the tests
        with patch('sys.stdout', new_callable=io.StringIO):
            self.assertTrue(self.validator.validate('users', valid_data))

    def test_valid_data_missing_nullable_field(self):
        """
        Tests validation with valid data that omits an optional (nullable) field.
        """
        valid_data = {'name': 'Bob'}
        with patch('sys.stdout', new_callable=io.StringIO):
            self.assertTrue(self.validator.validate('users', valid_data))

    def test_invalid_table_name(self):
        """
        Tests validation against a table name that does not exist.
        """
        invalid_data = {'name': 'Charlie'}
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.assertFalse(self.validator.validate('non_existent_table', invalid_data))
            self.assertIn("Invalid table name: 'non_existent_table'", mock_stdout.getvalue())

    def test_extra_column_provided(self):
        """
        Tests validation when the data contains a column not defined in the schema.
        """
        invalid_data = {'name': 'David', 'age': 40, 'location': 'City'}
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.assertFalse(self.validator.validate('users', invalid_data))
            self.assertIn("Invalid column name(s) provided: {'location'}", mock_stdout.getvalue())

    def test_generated_identity_always_column_provided(self):
        """
        Tests validation when the data attempts to provide a value for a column with generated identity
        set to ALWAYS.
        """
        invalid_data = {'id': 1, 'name': 'Eve'}
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.assertFalse(self.validator.validate('users', invalid_data))
            self.assertIn("Invalid column name(s) provided: {'id'}", mock_stdout.getvalue())

    def test_generated_identity_by_default_column_provided(self):
        """
        Tests validation when the data attempts to provide a value for a column with generated identity
        set top BY DEFAULT.
        """
        data = {'id': 1, 'type': 'Electronics'}
        with patch('sys.stdout', new_callable=io.StringIO):
            self.assertTrue(self.validator.validate('product_types', data))

    def test_missing_required_column(self):
        """
        Tests validation when a non-nullable column is missing from the data.
        """
        invalid_data = {'sku': 'A1234', 'price': Decimal('19.99')}  # Missing 'name'
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.assertFalse(self.validator.validate('products', invalid_data))
            output = mock_stdout.getvalue()
            self.assertIn("Required column 'name' was not provided.", output)

    def test_none_for_non_nullable_column(self):
        """
        Tests validation when a non-nullable column is explicitly set to None.
        """
        invalid_data = {'name': None, 'age': 25}
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.assertFalse(self.validator.validate('users', invalid_data))
            self.assertIn("Non-nullable column 'name' cannot be None.", mock_stdout.getvalue())

    def test_wrong_data_type(self):
        """
        Tests validation when a column has a value of the wrong Python type.
        """
        invalid_data = {'name': 'Frank', 'age': 'twenty-one'}  # age should be int
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.assertFalse(self.validator.validate('users', invalid_data))
            self.assertIn("Invalid data type for column 'age': expected int, got str", mock_stdout.getvalue())

    def test_wrong_data_type_for_decimal(self):
        """
        Tests validation with an incorrect type for a Decimal column.
        """
        invalid_data = {'sku': 'XYZ-123', 'name': 'Gadget', 'price': 19.99}  # price should be Decimal, not float
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            self.assertFalse(self.validator.validate('products', invalid_data))
            self.assertIn("Invalid data type for column 'price': expected Decimal, got float", mock_stdout.getvalue())

    def test_valid_data_for_decimal(self):
        """
        Tests validation with a correct Decimal type.
        """
        valid_data = {'sku': 'ABC-456', 'name': 'Widget', 'price': Decimal('25.50')}
        with patch('sys.stdout', new_callable=io.StringIO):
            self.assertTrue(self.validator.validate('products', valid_data))


if __name__ == '__main__':
    unittest.main(verbosity=2)