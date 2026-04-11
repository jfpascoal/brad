"""
Unit tests for the brad.frontend.utils module.

Tests the utility functions used across the frontend components,
including formatting, validation, and data transformation.
"""

import unittest
from decimal import Decimal

from brad.frontend.utils import (
    format_currency,
    format_delta,
    get_entity_names,
    create_entity_map,
    validate_required_fields,
    calculate_delta,
)


class TestFormatCurrency(unittest.TestCase):
    """Tests for the format_currency function."""

    def test_format_currency_with_currency_code(self):
        """Test formatting with currency code."""
        result = format_currency(Decimal('1234.56'), 'GBP')
        self.assertEqual('GBP 1,234.56', result)

    def test_format_currency_without_currency_code(self):
        """Test formatting without currency code."""
        result = format_currency(Decimal('1234.56'))
        self.assertEqual('1,234.56', result)

    def test_format_currency_large_number(self):
        """Test formatting with large numbers."""
        result = format_currency(Decimal('1234567.89'), 'EUR')
        self.assertEqual('EUR 1,234,567.89', result)

    def test_format_currency_small_number(self):
        """Test formatting with small numbers."""
        result = format_currency(Decimal('0.50'), 'USD')
        self.assertEqual('USD 0.50', result)

    def test_format_currency_zero(self):
        """Test formatting zero."""
        result = format_currency(Decimal('0'), 'GBP')
        self.assertEqual('GBP 0.00', result)

    def test_format_currency_none(self):
        """Test formatting None value."""
        result = format_currency(None)
        self.assertEqual('-', result)


class TestFormatDelta(unittest.TestCase):
    """Tests for the format_delta function."""

    def test_format_delta_positive(self):
        """Test formatting positive delta."""
        result = format_delta(Decimal('100.00'), Decimal('5.0'))
        self.assertEqual('+100.00 (+5.0%)', result)

    def test_format_delta_negative(self):
        """Test formatting negative delta."""
        result = format_delta(Decimal('-100.00'), Decimal('-5.0'))
        self.assertEqual('-100.00 (-5.0%)', result)

    def test_format_delta_zero(self):
        """Test formatting zero delta."""
        result = format_delta(Decimal('0.00'), Decimal('0.0'))
        self.assertEqual('+0.00 (+0.0%)', result)

    def test_format_delta_no_percentage(self):
        """Test formatting when percentage is None."""
        result = format_delta(Decimal('100.00'), None)
        self.assertEqual('+100.00', result)

    def test_format_delta_no_absolute(self):
        """Test formatting when absolute is None (first entry)."""
        result = format_delta(None, None)
        self.assertEqual('N/A (first entry)', result)


class TestGetEntityNames(unittest.TestCase):
    """Tests for the get_entity_names function."""

    def test_get_entity_names_default_field(self):
        """Test extracting names with default 'name' field."""
        entities = [
            {'id': 1, 'name': 'Entity A', 'type': 'foo'},
            {'id': 2, 'name': 'Entity B', 'type': 'bar'},
        ]
        result = get_entity_names(entities)
        self.assertEqual(['Entity A', 'Entity B'], result)

    def test_get_entity_names_custom_field(self):
        """Test extracting names with custom field."""
        entities = [
            {'id': 1, 'title': 'Title A'},
            {'id': 2, 'title': 'Title B'},
        ]
        result = get_entity_names(entities, name_field='title')
        self.assertEqual(['Title A', 'Title B'], result)

    def test_get_entity_names_empty_list(self):
        """Test extracting names from empty list."""
        result = get_entity_names([])
        self.assertEqual([], result)


class TestCreateEntityMap(unittest.TestCase):
    """Tests for the create_entity_map function."""

    def test_create_entity_map_full_entity(self):
        """Test creating map with full entity as value."""
        entities = [
            {'id': 1, 'name': 'Entity A', 'type': 'foo'},
            {'id': 2, 'name': 'Entity B', 'type': 'bar'},
        ]
        result = create_entity_map(entities)
        self.assertEqual({'id': 1, 'name': 'Entity A', 'type': 'foo'}, result['Entity A'])
        self.assertEqual({'id': 2, 'name': 'Entity B', 'type': 'bar'}, result['Entity B'])

    def test_create_entity_map_specific_value(self):
        """Test creating map with specific field as value."""
        entities = [
            {'id': 1, 'name': 'Entity A', 'type': 'foo'},
            {'id': 2, 'name': 'Entity B', 'type': 'bar'},
        ]
        result = create_entity_map(entities, value_field='id')
        self.assertEqual(1, result['Entity A'])
        self.assertEqual(2, result['Entity B'])

    def test_create_entity_map_custom_key(self):
        """Test creating map with custom key field."""
        entities = [
            {'id': 1, 'code': 'A', 'name': 'Entity A'},
            {'id': 2, 'code': 'B', 'name': 'Entity B'},
        ]
        result = create_entity_map(entities, key_field='code', value_field='name')
        self.assertEqual('Entity A', result['A'])
        self.assertEqual('Entity B', result['B'])

    def test_create_entity_map_empty_list(self):
        """Test creating map from empty list."""
        result = create_entity_map([])
        self.assertEqual({}, result)


class TestValidateRequiredFields(unittest.TestCase):
    """Tests for the validate_required_fields function."""

    def test_validate_all_fields_present(self):
        """Test validation when all required fields are present."""
        data = {'name': 'Test', 'type': 'foo', 'value': 123}
        errors = validate_required_fields(data, ['name', 'type'])
        self.assertEqual([], errors)

    def test_validate_missing_fields(self):
        """Test validation when required fields are missing."""
        data = {'name': 'Test'}
        errors = validate_required_fields(data, ['name', 'type', 'value'])
        self.assertEqual(2, len(errors))
        self.assertIn('Type is required.', errors)
        self.assertIn('Value is required.', errors)

    def test_validate_empty_string_field(self):
        """Test validation when required field is empty string."""
        data = {'name': '', 'type': 'foo'}
        errors = validate_required_fields(data, ['name', 'type'])
        self.assertEqual(1, len(errors))
        self.assertIn('Name is required.', errors)

    def test_validate_none_value(self):
        """Test validation when required field is None."""
        data = {'name': None, 'type': 'foo'}
        errors = validate_required_fields(data, ['name', 'type'])
        self.assertEqual(1, len(errors))
        self.assertIn('Name is required.', errors)

    def test_validate_underscore_field_names(self):
        """Test that field names with underscores are formatted correctly."""
        data = {'account_name': '', 'provider_name': 'Test'}
        errors = validate_required_fields(data, ['account_name', 'provider_name'])
        self.assertEqual(1, len(errors))
        self.assertIn('Account Name is required.', errors)

    def test_validate_no_required_fields(self):
        """Test validation with no required fields."""
        data = {'name': 'Test'}
        errors = validate_required_fields(data, [])
        self.assertEqual([], errors)


class TestCalculateDelta(unittest.TestCase):
    """Tests for the delta calculation utility function."""

    def test_calculate_delta_positive_change(self):
        """Test delta calculation with a positive change."""
        result = calculate_delta(
            current_value=Decimal('1200.00'),
            previous_value=Decimal('1000.00')
        )

        self.assertEqual(Decimal('200.00'), result['absolute'])
        self.assertEqual(Decimal('20.0'), result['percentage'])

    def test_calculate_delta_negative_change(self):
        """Test delta calculation with a negative change."""
        result = calculate_delta(
            current_value=Decimal('800.00'),
            previous_value=Decimal('1000.00')
        )

        self.assertEqual(Decimal('-200.00'), result['absolute'])
        self.assertEqual(Decimal('-20.0'), result['percentage'])

    def test_calculate_delta_no_change(self):
        """Test delta calculation with no change."""
        result = calculate_delta(
            current_value=Decimal('1000.00'),
            previous_value=Decimal('1000.00')
        )

        self.assertEqual(Decimal('0.00'), result['absolute'])
        self.assertEqual(Decimal('0.0'), result['percentage'])

    def test_calculate_delta_no_previous_value(self):
        """Test delta calculation when there is no previous value."""
        result = calculate_delta(
            current_value=Decimal('1000.00'),
            previous_value=None
        )

        self.assertIsNone(result['absolute'])
        self.assertIsNone(result['percentage'])

    def test_calculate_delta_previous_value_zero(self):
        """Test delta calculation when previous value is zero (avoid division by zero)."""
        result = calculate_delta(
            current_value=Decimal('100.00'),
            previous_value=Decimal('0')
        )

        self.assertEqual(Decimal('100.00'), result['absolute'])
        self.assertIsNone(result['percentage'])  # Cannot calculate percentage from zero


if __name__ == '__main__':
    unittest.main()
