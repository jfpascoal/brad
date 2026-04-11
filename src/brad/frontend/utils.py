"""
Frontend utility functions for data transformation and display.

This module provides helper functions used across the frontend components,
including delta calculation display, formatting, and data transformation.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional


def format_currency(value: Decimal, currency: str = '') -> str:
    """
    Formats a decimal value as a currency string.

    :param value: The decimal value to format.
    :param currency: Optional currency code to prepend (e.g., 'GBP', 'EUR').
    :return: Formatted string with thousands separator and 2 decimal places.
    """
    if value is None:
        return '-'
    formatted = f'{value:,.2f}'
    if currency:
        return f'{currency} {formatted}'
    return formatted


def format_delta(absolute: Optional[Decimal], percentage: Optional[Decimal]) -> str:
    """
    Formats delta values for display with sign and percentage.

    :param absolute: Absolute change value.
    :param percentage: Percentage change value.
    :return: Formatted string showing change (e.g., '+£250.00 (+5.2%)').
    """
    if absolute is None:
        return 'N/A (first entry)'

    sign = '+' if absolute >= 0 else ''
    abs_str = f'{sign}{absolute:,.2f}'

    if percentage is not None:
        pct_str = f'{sign}{percentage:.1f}%'
        return f'{abs_str} ({pct_str})'
    return abs_str


def get_entity_names(entities: List[Dict[str, Any]], name_field: str = 'name') -> List[str]:
    """
    Extracts a list of names from entity dictionaries.

    :param entities: List of entity dictionaries.
    :param name_field: The field name containing the entity name (default: 'name').
    :return: List of entity names as strings.
    """
    return [entity[name_field] for entity in entities]


def create_entity_map(
    entities: List[Dict[str, Any]],
    key_field: str = 'name',
    value_field: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a mapping from entity names to full entity data or a specific field.

    :param entities: List of entity dictionaries.
    :param key_field: Field to use as the dictionary key (default: 'name').
    :param value_field: Optional field to use as value; if None, entire entity is used.
    :return: Dictionary mapping keys to values or full entity dictionaries.
    """
    if value_field:
        return {entity[key_field]: entity[value_field] for entity in entities}
    return {entity[key_field]: entity for entity in entities}


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Validates that all required fields are present and non-empty.

    :param data: Dictionary containing form data.
    :param required_fields: List of field names that must be present and non-empty.
    :return: List of error messages for missing/empty fields (empty if all valid).
    """
    errors = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            errors.append(f'{field.replace("_", " ").title()} is required.')
    return errors


def calculate_delta(
    current_value: Decimal,
    previous_value: Optional[Decimal]
) -> Dict[str, Any]:
    """
    Calculates the absolute and percentage change between two values.

    :param current_value: The new/current value.
    :param previous_value: The previous value (can be None if no prior data).
    :return: Dictionary with 'absolute' and 'percentage' keys.
             If previous_value is None, both will be None.
    """
    if previous_value is None:
        return {'absolute': None, 'percentage': None}

    absolute = current_value - previous_value
    if previous_value == 0:
        percentage = None  # Avoid division by zero
    else:
        percentage = (absolute / previous_value) * 100

    return {'absolute': absolute, 'percentage': percentage}
