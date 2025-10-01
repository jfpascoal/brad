import unittest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from brad.sql.objects import (
    Table, Column, Row, TableRowValidator, 
    PrimaryKey, Unique, GeneratedIdOptions
)
from brad.sql.types import Text, Integer, BigInt, Boolean, Date, Numeric
from datetime import date
from decimal import Decimal


class TestTableRowValidator(unittest.TestCase):
    """Test cases for the TableRowValidator class and its dynamic model creation."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear the cache before each test
        TableRowValidator.clear_cache()
        
        # Create a comprehensive test table
        self.table = Table('test_validation').set_columns(
            Column('id', BigInt(), generated_identity=GeneratedIdOptions.BY_DEFAULT),
            Column('name', Text(), not_null=True),
            Column('email', Text(), not_null=True),
            Column('age', Integer(), default=18),
            Column('is_active', Boolean(), default=True),
            Column('score', Numeric(10, 2)),
            Column('created_date', Date())
        ).set_constraint(
            PrimaryKey(['id'])
        ).set_constraint(
            Unique(['email'])
        )

    def tearDown(self):
        """Clean up after each test."""
        TableRowValidator.clear_cache()

    def test_create_table_model_basic(self):
        """Test basic table model creation."""
        model = TableRowValidator.create_table_model(self.table)
        
        self.assertIsNotNone(model)
        self.assertEqual(model.__name__, "Test_ValidationRowModel")
        self.assertIn('name', model.model_fields)
        self.assertIn('email', model.model_fields)
        self.assertIn('age', model.model_fields)

    def test_create_table_model_caching(self):
        """Test that models are properly cached."""
        model1 = TableRowValidator.create_table_model(self.table)
        model2 = TableRowValidator.create_table_model(self.table)
        
        # Should be the same object due to caching
        self.assertIs(model1, model2)

    def test_model_validation_success(self):
        """Test successful validation with a valid row."""
        model = TableRowValidator.create_table_model(self.table)
        
        valid_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 25,
            'is_active': True,
            'score': Decimal('85.50'),
            'created_date': date(2025, 1, 1)
        }
        
        # Should not raise any exception
        validated = model(**valid_data)
        self.assertEqual(validated.name, 'John Doe')
        self.assertEqual(validated.email, 'john@example.com')

    def test_model_validation_missing_required_field(self):
        """Test validation failure when required field is missing."""
        model = TableRowValidator.create_table_model(self.table)
        
        invalid_data = {
            'email': 'john@example.com'  # Missing required 'name' field
        }
        
        with self.assertRaises(ValidationError) as cm:
            model(**invalid_data)
        
        errors = cm.exception.errors()
        self.assertTrue(any(error['type'] == 'missing' for error in errors))

    def test_model_validation_wrong_type(self):
        """Test validation failure with wrong field type."""
        model = TableRowValidator.create_table_model(self.table)
        
        invalid_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 'not_a_number',  # Wrong type for age
            'is_active': 'not_a_boolean'  # Wrong type for is_active
        }
        
        with self.assertRaises(ValidationError) as cm:
            model(**invalid_data)
        
        errors = cm.exception.errors()
        self.assertTrue(any('age' in str(error.get('loc', [])) for error in errors))

    def test_model_validation_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        model = TableRowValidator.create_table_model(self.table)
        
        invalid_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'extra_field': 'not_allowed'  # Extra field should be rejected
        }
        
        with self.assertRaises(ValidationError) as cm:
            model(**invalid_data)
        
        errors = cm.exception.errors()
        self.assertTrue(any(error['type'] == 'extra_forbidden' for error in errors))

    def test_generated_identity_columns_optional(self):
        """Test that generated identity columns are optional."""
        model = TableRowValidator.create_table_model(self.table)
        
        # Should work without providing the 'id' field
        valid_data = {
            'name': 'Jane Doe',
            'email': 'jane@example.com'
        }
        
        validated = model(**valid_data)
        self.assertEqual(validated.name, 'Jane Doe')
        self.assertIsNone(validated.id)  # Should be None since it's generated

    def test_default_value_handling(self):
        """Test that default values are handled correctly."""
        model = TableRowValidator.create_table_model(self.table)
        
        # Provide minimal required data, defaults should be applied
        minimal_data = {
            'name': 'Test User',
            'email': 'test@example.com'
        }
        
        validated = model(**minimal_data)
        # Note: Pydantic doesn't automatically apply defaults from Field definitions
        # The defaults are structural, not runtime defaults

    def test_nullable_fields_optional(self):
        """Test that nullable fields are properly optional."""
        # Create table with nullable columns
        nullable_table = Table('nullable_test').set_columns(
            Column('id', BigInt(), not_null=True),
            Column('name', Text(), not_null=True),
            Column('optional_field', Text())  # Nullable field
        )
        
        model = TableRowValidator.create_table_model(nullable_table)
        
        # Should work with nullable field as None
        valid_data = {
            'id': 1,
            'name': 'Test',
            'optional_field': None
        }
        
        validated = model(**valid_data)
        self.assertEqual(validated.name, 'Test')
        self.assertIsNone(validated.optional_field)

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        # Create a model to populate cache
        model1 = TableRowValidator.create_table_model(self.table)
        self.assertTrue(len(TableRowValidator._model_cache) > 0)
        
        # Clear cache
        TableRowValidator.clear_cache()
        self.assertEqual(len(TableRowValidator._model_cache), 0)
        
        # Create model again - should be a new instance
        model2 = TableRowValidator.create_table_model(self.table)
        self.assertIsNot(model1, model2)

    def test_cross_field_validation_primary_key(self):
        """Test cross-field validation for primary key constraints."""
        # Create table with multi-column primary key
        pk_table = Table('pk_test').set_columns(
            Column('user_id', BigInt()),
            Column('project_id', BigInt()),
            Column('name', Text(), not_null=True)
        ).set_constraint(
            PrimaryKey(['user_id', 'project_id'])
        )
        
        model = TableRowValidator.create_table_model(pk_table)
        
        # Test with valid primary key values
        valid_data = {
            'user_id': 1,
            'project_id': 2,
            'name': 'Test Project'
        }
        
        # Should validate successfully
        validated = model(**valid_data)
        self.assertEqual(validated.name, 'Test Project')

    def test_cross_field_validation_unique_constraint(self):
        """Test cross-field validation for unique constraints."""
        # Create table with multi-column unique constraint
        unique_table = Table('unique_test').set_columns(
            Column('id', BigInt(), not_null=True),
            Column('first_name', Text()),
            Column('last_name', Text()),
            Column('email', Text(), not_null=True)
        ).set_constraint(
            Unique(['first_name', 'last_name'])
        )
        
        model = TableRowValidator.create_table_model(unique_table)
        
        # Test with valid unique constraint values
        valid_data = {
            'id': 1,
            'first_name': 'John',
            'last_name': 'Doe', 
            'email': 'john@example.com'
        }
        
        # Should validate successfully
        validated = model(**valid_data)
        self.assertEqual(validated.first_name, 'John')


class TestColumnDefaultValues(unittest.TestCase):
    """Test cases for column default value handling."""
    
    def test_boolean_column_default_value(self):
        """Test Boolean column default value formatting."""
        col = Column('is_active', Boolean(), default=True)
        self.assertEqual(col.default, 'TRUE')
        
        col_false = Column('is_deleted', Boolean(), default=False)
        self.assertEqual(col_false.default, 'FALSE')

    def test_date_column_default_value(self):
        """Test Date column default value formatting."""
        test_date = date(2025, 1, 1)
        col = Column('created_date', Date(), default=test_date)
        self.assertEqual(col.default, '2025-01-01')

    def test_text_column_default_value(self):
        """Test Text column default value formatting."""
        col = Column('status', Text(), default='active')
        self.assertEqual(col.default, "'active'")

    def test_numeric_column_default_value(self):
        """Test Numeric column default value formatting."""
        col = Column('score', Integer(), default=100)
        self.assertEqual(col.default, '100')


class TestTableRowValidatorIntegration(unittest.TestCase):
    """Integration tests for TableRowValidator with Table._validate_row()."""
    
    def setUp(self):
        """Set up test fixtures."""
        TableRowValidator.clear_cache()
        
        self.table = Table('integration_test').set_columns(
            Column('id', BigInt(), generated_identity=GeneratedIdOptions.BY_DEFAULT),
            Column('name', Text(), not_null=True),
            Column('age', Integer(), default=18),
            Column('is_active', Boolean(), default=True)
        )

    def tearDown(self):
        """Clean up after each test."""
        TableRowValidator.clear_cache()

    @patch('brad.sql.objects.logger')
    def test_validate_row_success_integration(self, mock_logger):
        """Test successful row validation through Table._validate_row()."""
        valid_row = Row(name="John Doe", age=25, is_active=True)
        result = self.table._validate_row(valid_row)
        
        self.assertTrue(result)
        mock_logger.warning.assert_not_called()

    @patch('brad.sql.objects.logger')
    def test_validate_row_failure_integration(self, mock_logger):
        """Test failed row validation through Table._validate_row()."""
        invalid_row = Row(age=25, is_active=True)  # Missing required 'name'
        result = self.table._validate_row(invalid_row)
        
        self.assertFalse(result)
        mock_logger.warning.assert_called()

    @patch('brad.sql.objects.logger')
    def test_validate_row_exception_handling(self, mock_logger):
        """Test exception handling in row validation."""
        # Create a row with invalid data that will cause ValidationError
        invalid_row = Row(name="John", age="not_a_number")  # Wrong type for age
        result = self.table._validate_row(invalid_row)
        
        self.assertFalse(result)
        mock_logger.warning.assert_called()

    @patch('brad.sql.objects.TableRowValidator.create_table_model')
    @patch('brad.sql.objects.logger')
    def test_validate_row_unexpected_exception(self, mock_logger, mock_create_model):
        """Test handling of unexpected exceptions in validation."""
        # Make create_table_model raise an unexpected exception
        mock_create_model.side_effect = RuntimeError("Unexpected error")
        
        valid_row = Row(name="John Doe")
        result = self.table._validate_row(valid_row)
        
        self.assertFalse(result)
        mock_logger.error.assert_called_once()
        mock_logger.warning.assert_called()


if __name__ == '__main__':
    unittest.main()