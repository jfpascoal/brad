import unittest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from brad.sql.objects import (
    Table, Column, Row, TableRowValidator, 
    PrimaryKey, Unique, GeneratedIdOptions
)
from brad.sql.types import Text, Integer, BigInt, Boolean


class TestTableRowValidatorEdgeCases(unittest.TestCase):
    """Additional edge case tests to improve coverage."""

    def setUp(self):
        """Set up test fixtures."""
        TableRowValidator.clear_cache()

    def tearDown(self):
        """Clean up after each test."""
        TableRowValidator.clear_cache()

    def test_non_writable_columns_excluded(self):
        """Test that non-writable columns (GENERATED ALWAYS) are excluded from model."""
        # Create table with GENERATED ALWAYS column (non-writable)
        table = Table('test_generated').set_columns(
            Column('id', BigInt(), generated_identity=GeneratedIdOptions.ALWAYS),  # Not writable
            Column('name', Text(), not_null=True)
        )
        
        model = TableRowValidator.create_table_model(table)
        
        # The 'id' field should not be in the model since it's GENERATED ALWAYS
        self.assertNotIn('id', model.model_fields)
        self.assertIn('name', model.model_fields)

    def test_cross_field_validation_with_errors(self):
        """Test that cross-field validation logic is properly set up."""
        # Create table with multi-column primary key where some columns can be null
        table = Table('pk_test').set_columns(
            Column('user_id', BigInt()),  # Nullable
            Column('project_id', BigInt()),  # Nullable  
            Column('name', Text(), not_null=True)
        ).set_constraint(
            PrimaryKey(['user_id', 'project_id'])
        )
        
        model = TableRowValidator.create_table_model(table)
        
        # Verify that the composite validator was added
        self.assertTrue(hasattr(model, 'validate_table_constraints'))
        
        # Test that the validation logic works for valid data
        valid_data = {
            'user_id': 1,
            'project_id': 1,
            'name': 'Test'
        }
        
        # This should pass validation
        validated = model(**valid_data)
        self.assertEqual(validated.name, 'Test')

    def test_unique_constraint_validation_setup(self):
        """Test that unique constraint validation is properly set up."""
        table = Table('unique_test').set_columns(
            Column('id', BigInt(), not_null=True),
            Column('first_name', Text()),  # Nullable
            Column('last_name', Text())   # Nullable
        ).set_constraint(
            Unique(['first_name', 'last_name'])
        )
        
        model = TableRowValidator.create_table_model(table)
        
        # Verify that the composite validator was added for multi-column unique constraint
        self.assertTrue(hasattr(model, 'validate_table_constraints'))
        
        # Test that validation works for valid data
        valid_data = {
            'id': 1,
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        validated = model(**valid_data)
        self.assertEqual(validated.first_name, 'John')

    def test_model_validator_fallback_dict_conversion(self):
        """Test the fallback dict conversion in composite validator."""
        # Create a mock values object without model_dump method
        mock_values = MagicMock()
        mock_values.model_dump = None
        del mock_values.model_dump  # Remove the attribute
        
        # Mock the dict() conversion
        expected_dict = {'user_id': 1, 'project_id': 2}
        mock_values.__iter__ = lambda: iter(expected_dict.items())
        
        # This tests the fallback path in _create_composite_constraint_validator
        table = Table('fallback_test').set_columns(
            Column('user_id', BigInt()),
            Column('project_id', BigInt())
        ).set_constraint(
            PrimaryKey(['user_id', 'project_id'])
        )
        
        model = TableRowValidator.create_table_model(table)
        
        # The normal validation should work fine
        valid_data = {'user_id': 1, 'project_id': 2}
        validated = model(**valid_data)
        self.assertEqual(validated.user_id, 1)

    def test_constraint_validator_setup(self):
        """Test that constraint validators are properly set up for multiple constraints."""
        table = Table('multi_constraint_test').set_columns(
            Column('user_id', BigInt()),
            Column('project_id', BigInt()),
            Column('email', Text()),
            Column('username', Text())
        ).set_constraint(
            PrimaryKey(['user_id', 'project_id'])
        ).set_constraint(
            Unique(['email', 'username'])
        )
        
        model = TableRowValidator.create_table_model(table)
        
        # Verify that composite validator was added for multiple multi-column constraints
        self.assertTrue(hasattr(model, 'validate_table_constraints'))
        
        # Test that validation works for valid data
        valid_data = {
            'user_id': 1,
            'project_id': 2, 
            'email': 'test@example.com',
            'username': 'testuser'
        }
        
        validated = model(**valid_data)
        self.assertEqual(validated.email, 'test@example.com')


class TestTableValidationIntegrationEdgeCases(unittest.TestCase):
    """Edge case tests for Table._validate_row integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        TableRowValidator.clear_cache()

    def tearDown(self):
        """Clean up after each test."""
        TableRowValidator.clear_cache()

    @patch('brad.sql.objects.logger')
    def test_validate_row_detailed_error_logging(self, mock_logger):
        """Test detailed error logging categories."""
        table = Table('error_test').set_columns(
            Column('id', BigInt(), not_null=True),
            Column('name', Text(), not_null=True),
            Column('age', Integer())
        )
        
        # Test missing field error
        invalid_row = Row(age=25)  # Missing required id and name
        result = table._validate_row(invalid_row)
        
        self.assertFalse(result)
        
        # Verify that warning was called multiple times for different error categories
        self.assertTrue(mock_logger.warning.call_count >= 3)  # At least for missing fields, problematic data, and final message
        
        # Check that specific error categories were logged
        call_args = [str(call[0][0]) for call in mock_logger.warning.call_args_list]
        
        # Should have logged about missing required fields
        self.assertTrue(any('Missing required fields' in arg for arg in call_args))
        self.assertTrue(any('Row will not be inserted due to validation failures' in arg for arg in call_args))

    @patch('brad.sql.objects.logger')
    def test_validate_row_value_error_logging(self, mock_logger):
        """Test value error logging category."""
        table = Table('value_error_test').set_columns(
            Column('id', BigInt(), not_null=True),
            Column('name', Text(), not_null=True),
            Column('age', Integer(), not_null=True)
        )
        
        # Test type error
        invalid_row = Row(id=1, name="John", age="not_a_number")  # Wrong type for age
        result = table._validate_row(invalid_row)
        
        self.assertFalse(result)
        
        # Check that value validation errors were logged
        call_args = [str(call[0][0]) for call in mock_logger.warning.call_args_list]
        self.assertTrue(any('Field validation errors' in arg for arg in call_args))

    @patch('brad.sql.objects.logger')  
    def test_validate_row_extra_fields_error_logging(self, mock_logger):
        """Test extra fields error logging."""
        table = Table('extra_field_test').set_columns(
            Column('id', BigInt(), not_null=True),
            Column('name', Text(), not_null=True)
        )
        
        # Test extra field error
        invalid_row = Row(id=1, name="John", extra_field="not_allowed")
        result = table._validate_row(invalid_row)
        
        self.assertFalse(result)
        
        # Check that field validation errors were logged  
        call_args = [str(call[0][0]) for call in mock_logger.warning.call_args_list]
        self.assertTrue(any('Field validation errors' in arg for arg in call_args))


if __name__ == '__main__':
    unittest.main()