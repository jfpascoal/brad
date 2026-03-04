from decimal import Decimal

from sqlalchemy import Date, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from brad.core.models.base import Base


class Currency(Base):
    """ISO 4217 currency codes."""

    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(5))


class AccountType(Base):
    """Account type dimension (Current, Savings, Credit Card, …)."""

    __tablename__ = "account_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name_pt: Mapped[str | None] = mapped_column(String(100))


class ProductType(Base):
    """Financial product type dimension (Stock, Bond, ETF, …)."""

    __tablename__ = "product_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name_pt: Mapped[str | None] = mapped_column(String(100))


class TransactionType(Base):
    """Transaction type dimension (Purchase, Sale, Dividend, …)."""

    __tablename__ = "transaction_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name_pt: Mapped[str | None] = mapped_column(String(100))


class ExchangeRate(Base):
    """Daily exchange rates between currency pairs."""

    __tablename__ = "exchange_rates"
    __table_args__ = (UniqueConstraint("date", "base_currency", "target_currency"),)

    date: Mapped["Date"] = mapped_column(Date, primary_key=True)
    base_currency: Mapped[str] = mapped_column(
        String(3),
        primary_key=True,
    )
    target_currency: Mapped[str] = mapped_column(
        String(3),
        primary_key=True,
    )
    rate: Mapped[Decimal] = mapped_column(Numeric(19, 5), nullable=False)
