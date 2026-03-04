from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CurrencySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str = Field(max_length=3, description="ISO 4217 currency code")
    name: str = Field(max_length=50)
    symbol: str | None = Field(default=None, max_length=5)


class TypeSchema(BaseModel):
    """Shared schema for account_types, product_types, transaction_types."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    name: str = Field(max_length=100)
    name_pt: str | None = Field(default=None, max_length=100)


class ProviderCreate(BaseModel):
    name: str = Field(max_length=200)
    country: str = Field(max_length=2, description="ISO alpha-2 country code")


class HolderCreate(BaseModel):
    name: str = Field(max_length=200)
    tax_bracket: str | None = None


class AccountCreate(BaseModel):
    name: str = Field(max_length=300)
    account_type_id: int
    currency_code: str = Field(max_length=3)
    provider_id: int
    holder_ids: list[int] = Field(
        default_factory=list,
        description="Ordered list of holder IDs (first = primary)",
    )
    account_number: str | None = None
    sort_code: str | None = None
    iban: str | None = None
    swift_code: str | None = None
    opening_date: date | None = None
    closing_date: date | None = None
    is_active: bool = True


class FinancialProductCreate(BaseModel):
    name: str = Field(max_length=300)
    product_type_id: int
    currency_code: str = Field(max_length=3)
    linked_account_id: int | None = None
    provider_id: int
    holder_ids: list[int] = Field(
        default_factory=list,
        description="Ordered list of holder IDs",
    )
    ticker: str | None = None
    isin: str | None = None
    is_active: bool = True


class AccountBalanceCreate(BaseModel):
    date: date
    account_id: int
    balance: Decimal


class AccountTransactionCreate(BaseModel):
    date: date
    account_id: int
    transaction_type_id: int
    amount: Decimal
    description: str | None = None


class ProductValueCreate(BaseModel):
    date: date
    product_id: int
    current_value: Decimal
    units: Decimal | None = None
    unit_value: Decimal | None = None


class ProductTransactionCreate(BaseModel):
    date: date
    product_id: int
    transaction_type_id: int
    amount: Decimal
    amount_base_currency: Decimal | None = None
    units: Decimal | None = None
    unit_value: Decimal | None = None


class ProviderRead(ProviderCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class HolderRead(HolderCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    account_type_id: int
    currency_code: str
    provider_id: int
    account_number: str | None
    sort_code: str | None
    iban: str | None
    swift_code: str | None
    opening_date: date | None
    closing_date: date | None
    is_active: bool


class FinancialProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    product_type_id: int
    currency_code: str
    linked_account_id: int | None
    provider_id: int
    ticker: str | None
    isin: str | None
    is_active: bool
