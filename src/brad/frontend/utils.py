"""
Frontend utility functions for data transformation and display.

This module provides helper functions used across the frontend components,
including delta calculation display, formatting, and data transformation.
"""

from __future__ import annotations

import contextlib
from collections.abc import Generator, Sequence
from decimal import Decimal
from typing import Any

import streamlit as st
from sqlalchemy.orm import Session

from brad.core.db import get_session_factory
from brad.frontend.constants import StateKeys


@contextlib.contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Provides a transactional scope around a series of database operations.

    Uses the session_factory stored in Streamlit session state.
    """
    factory = st.session_state.get(StateKeys.SESSION_FACTORY)
    if factory is None:
        factory = get_session_factory()
        st.session_state[StateKeys.SESSION_FACTORY] = factory

    with factory() as session:
        yield session


def format_currency(value: Decimal, currency: str = "") -> str:
    """
    Formats a decimal value as a currency string.

    :param value: The decimal value to format.
    :param currency: Optional currency code to prepend (e.g., 'GBP', 'EUR').
    :return: Formatted string with thousands separator and 2 decimal places.
    """
    if value is None:
        return "-"
    formatted = f"{value:,.2f}"
    if currency:
        return f"{currency} {formatted}"
    return formatted


def format_delta(absolute: Decimal | None, percentage: Decimal | None) -> str:
    """
    Formats delta values for display with sign and percentage.

    :param absolute: Absolute change value.
    :param percentage: Percentage change value.
    :return: Formatted string showing change (e.g., '+£250.00 (+5.2%)').
    """
    if absolute is None:
        return "N/A (first entry)"

    sign = "+" if absolute >= 0 else ""
    abs_str = f"{sign}{absolute:,.2f}"

    if percentage is not None:
        pct_str = f"{sign}{percentage:.1f}%"
        return f"{abs_str} ({pct_str})"
    return abs_str


def get_entity_names(entities: Sequence[Any], name_field: str = "name") -> list[str]:
    """
    Extracts a list of names from a sequence of SQLAlchemy models.

    :param entities: Sequence of SQLAlchemy models.
    :param name_field: The attribute name containing the entity name (default: 'name').
    :return: List of entity names as strings.
    """
    return [getattr(entity, name_field) for entity in entities]


def create_entity_map(
    entities: Sequence[Any], key_field: str = "name", value_field: str | None = None
) -> dict[str, Any]:
    """
    Creates a mapping from entity attributes to full entity models or a specific field.

    :param entities: Sequence of SQLAlchemy models.
    :param key_field: Attribute to use as the dictionary key (default: 'name').
    :param value_field: Optional attribute to use as value; if None, entire model is used.
    :return: Dictionary mapping keys to values or full entity models.
    """
    if value_field:
        return {
            getattr(entity, key_field): getattr(entity, value_field)
            for entity in entities
        }
    return {getattr(entity, key_field): entity for entity in entities}


def validate_required_fields(
    data: dict[str, Any], required_fields: list[str]
) -> list[str]:
    """
    Validates that all required fields are present and non-empty.

    :param data: Dictionary containing form data.
    :param required_fields: List of field names that must be present and non-empty.
    :return: List of error messages for missing/empty fields (empty if all valid).
    """
    errors = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            errors.append(f"{field.replace('_', ' ').title()} is required.")
    return errors


def calculate_delta(
    current_value: Decimal, previous_value: Decimal | None
) -> dict[str, Any]:
    """
    Calculates the absolute and percentage change between two values.

    :param current_value: The new/current value.
    :param previous_value: The previous value (can be None if no prior data).
    :return: Dictionary with 'absolute' and 'percentage' keys.
             If previous_value is None, both will be None.
    """
    if previous_value is None:
        return {"absolute": None, "percentage": None}

    absolute = current_value - previous_value
    if previous_value == 0:
        percentage = None  # Avoid division by zero
    else:
        percentage = (absolute / previous_value) * 100

    return {"absolute": absolute, "percentage": percentage}
