from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from brad.core.models.operational import Account, Provider, Holder, FinancialProduct
from brad.core.models.reference import Currency, AccountType
from brad.core.schemas import (
    AccountCreate,
    AccountRead,
    AccountBalanceCreate,
    CurrencySchema,
    TypeSchema,
    AccountTransactionCreate,
    ProductValueCreate,
    ProductTransactionCreate,
    ProviderRead,
    HolderRead,
    FinancialProductRead,
)


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


@pytest.mark.parametrize(
    "SchemaClass, ORMClass, mock_kwargs",
    [
        (CurrencySchema, Currency, {"code": "USD", "name": "Dollar", "symbol": "$"}),
        (TypeSchema, AccountType, {"id": 1, "name": "Current", "name_pt": "Corrente"}),
        (ProviderRead, Provider, {"id": 1, "name": "Bank", "country": "GB"}),
        (HolderRead, Holder, {"id": 2, "name": "John", "tax_bracket": "High"}),
        (
            FinancialProductRead,
            FinancialProduct,
            {
                "id": 10,
                "name": "ETF",
                "product_type_id": 1,
                "currency_code": "GBP",
                "provider_id": 1,
                "is_active": True,
            },
        ),
    ],
)
def test_read_schemas_from_attributes(SchemaClass, ORMClass, mock_kwargs):
    """Test all remaining Read schemas map ORM objects correctly."""
    # Build pseudo-ORM instance
    orm_obj = ORMClass(**mock_kwargs)

    # Parse via Pydantic model_validate
    parsed = SchemaClass.model_validate(orm_obj)

    # Spot check properties match the kwargs dynamically
    for key, val in mock_kwargs.items():
        assert getattr(parsed, key) == val


@pytest.mark.parametrize(
    "SchemaClass, mock_kwargs",
    [
        (
            AccountTransactionCreate,
            {
                "date": date.today(),
                "account_id": 1,
                "transaction_type_id": 2,
                "amount": "100.50",
            },
        ),
        (
            ProductValueCreate,
            {"date": date.today(), "product_id": 1, "current_value": "5000"},
        ),
        (
            ProductTransactionCreate,
            {
                "date": date.today(),
                "product_id": 2,
                "transaction_type_id": 1,
                "amount": "200",
            },
        ),
    ],
)
def test_create_schemas_parsing(SchemaClass, mock_kwargs):
    """Ensure creation schemas properly parse simple dictionaries."""
    parsed = SchemaClass(**mock_kwargs)
    # Check at least one financial field properly coerced to Decimal
    amount_field = getattr(parsed, "amount", None) or getattr(
        parsed, "current_value", None
    )
    assert isinstance(amount_field, Decimal)
