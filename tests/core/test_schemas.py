from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from brad.core.models.operational import Account
from brad.core.schemas import AccountCreate, AccountRead, AccountBalanceCreate


def test_account_create_schema_validation():
    """Test standard Pydantic validation rules."""
    # Valid schema creation
    valid_data = {
        "name": "Test Account",
        "account_type_id": 1,
        "currency_code": "GBP",
        "provider_id": 2,
    }
    account = AccountCreate(**valid_data)
    assert account.name == "Test Account"
    assert account.is_active is True  # Defaults to True

    # Invalid - missing required
    with pytest.raises(ValidationError):
        AccountCreate(name="Missing stuff")

    # Invalid - exceeding string limits (currency_code > 3 chars)
    with pytest.raises(ValidationError):
        AccountCreate(**{**valid_data, "currency_code": "GBPX"})


def test_account_read_from_attributes():
    """Test `from_attributes=True` bridge correctly converts a mocked SQLAlchemy object into a Pydantic record."""

    # We create a pseudo-SQLAlchemy object. It doesn't need a real DB session for this mapping test.
    mock_db_account = Account(
        id=99,
        name="ORM Account",
        account_type_id=1,
        currency_code="EUR",
        provider_id=5,
        is_active=False,
    )

    # Validate parsing
    read_schema = AccountRead.model_validate(mock_db_account)

    # Ensure it translated correctly
    assert read_schema.id == 99
    assert read_schema.name == "ORM Account"
    assert read_schema.currency_code == "EUR"
    assert read_schema.is_active is False


def test_decimal_conversion():
    """Ensure decimal parsing is strictly handled for financial amounts."""
    # Integers and valid strings are coerced to Decimal
    bal1 = AccountBalanceCreate(date=date.today(), account_id=1, balance="100.50")
    bal2 = AccountBalanceCreate(date=date.today(), account_id=1, balance=50)

    assert isinstance(bal1.balance, Decimal)
    assert bal1.balance == Decimal("100.50")
    assert isinstance(bal2.balance, Decimal)
