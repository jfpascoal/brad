from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from brad.core.models.base import Base, CreatedAtMixin, TimestampMixin
from brad.core.models.reference import AccountType, ProductType


class Provider(TimestampMixin, Base):
    """Financial service provider (bank, broker, etc.)."""

    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False)

    # Relationships
    accounts: Mapped[list["Account"]] = relationship(back_populates="provider")
    financial_products: Mapped[list["FinancialProduct"]] = relationship(
        back_populates="provider"
    )


class Holder(TimestampMixin, Base):
    """Person who holds accounts or financial products."""

    __tablename__ = "holders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    tax_bracket: Mapped[str | None] = mapped_column(String(100))

    # Relationships
    account_links: Mapped[list["AccountHolder"]] = relationship(back_populates="holder")
    product_links: Mapped[list["ProductHolder"]] = relationship(back_populates="holder")


class AccountHolder(Base):
    """Junction table: which holders are on which accounts."""

    __tablename__ = "account_holders"
    __table_args__ = (UniqueConstraint("account_id", "holder_id"),)

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True
    )
    holder_id: Mapped[int] = mapped_column(
        ForeignKey("holders.id", ondelete="CASCADE"), primary_key=True
    )
    ordinal: Mapped[int] = mapped_column(default=1)

    # Relationships
    account: Mapped["Account"] = relationship(back_populates="holder_links")
    holder: Mapped["Holder"] = relationship(back_populates="account_links")


class ProductHolder(Base):
    """Junction table: which holders are on which financial products."""

    __tablename__ = "product_holders"
    __table_args__ = (UniqueConstraint("product_id", "holder_id"),)

    product_id: Mapped[int] = mapped_column(
        ForeignKey("financial_products.id", ondelete="CASCADE"), primary_key=True
    )
    holder_id: Mapped[int] = mapped_column(
        ForeignKey("holders.id", ondelete="CASCADE"), primary_key=True
    )
    ordinal: Mapped[int] = mapped_column(default=1)

    # Relationships
    product: Mapped["FinancialProduct"] = relationship(back_populates="holder_links")
    holder: Mapped["Holder"] = relationship(back_populates="product_links")


class Account(TimestampMixin, Base):
    """Bank account, credit card, savings account, etc."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False, unique=True)
    account_type_id: Mapped[int] = mapped_column(
        ForeignKey("account_types.id"), nullable=False
    )
    currency_code: Mapped[str] = mapped_column(
        ForeignKey("currencies.code"), nullable=False
    )
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"), nullable=False)
    account_number: Mapped[str | None] = mapped_column(String(50))
    sort_code: Mapped[str | None] = mapped_column(String(20))
    iban: Mapped[str | None] = mapped_column(String(34))
    swift_code: Mapped[str | None] = mapped_column(String(11))
    opening_date: Mapped[date | None] = mapped_column(Date)
    closing_date: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    provider: Mapped["Provider"] = relationship(back_populates="accounts")
    type_link: Mapped["AccountType"] = relationship()
    holder_links: Mapped[list["AccountHolder"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    balances: Mapped[list["AccountBalance"]] = relationship(back_populates="account")
    transactions: Mapped[list["AccountTransaction"]] = relationship(
        back_populates="account"
    )
    linked_products: Mapped[list["FinancialProduct"]] = relationship(
        back_populates="linked_account"
    )


class FinancialProduct(TimestampMixin, Base):
    """Investment fund, bond, ISA, P2P lending, etc."""

    __tablename__ = "financial_products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False, unique=True)
    product_type_id: Mapped[int] = mapped_column(
        ForeignKey("product_types.id"), nullable=False
    )
    currency_code: Mapped[str] = mapped_column(
        ForeignKey("currencies.code"), nullable=False
    )
    linked_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"), nullable=False)
    ticker: Mapped[str | None] = mapped_column(String(20))
    isin: Mapped[str | None] = mapped_column(String(12))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    provider: Mapped["Provider"] = relationship(back_populates="financial_products")
    type_link: Mapped["ProductType"] = relationship()
    linked_account: Mapped["Account | None"] = relationship(
        back_populates="linked_products"
    )
    holder_links: Mapped[list["ProductHolder"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    values: Mapped[list["ProductValue"]] = relationship(back_populates="product")
    transactions: Mapped[list["ProductTransaction"]] = relationship(
        back_populates="product"
    )


class AccountBalance(CreatedAtMixin, Base):
    """Point-in-time balance snapshot for an account."""

    __tablename__ = "account_balances"

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), primary_key=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(19, 5), nullable=False)

    # Relationships
    account: Mapped["Account"] = relationship(back_populates="balances")


class AccountTransaction(CreatedAtMixin, Base):
    """Individual transaction on an account."""

    __tablename__ = "account_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    transaction_type_id: Mapped[int] = mapped_column(
        ForeignKey("transaction_types.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 5), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))

    # Relationships
    account: Mapped["Account"] = relationship(back_populates="transactions")


class ProductValue(CreatedAtMixin, Base):
    """Point-in-time valuation snapshot for a financial product."""

    __tablename__ = "product_values"

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("financial_products.id"), primary_key=True
    )
    current_value: Mapped[Decimal] = mapped_column(Numeric(19, 5), nullable=False)
    units: Mapped[Decimal | None] = mapped_column(Numeric(19, 5))
    unit_value: Mapped[Decimal | None] = mapped_column(Numeric(19, 5))

    # Relationships
    product: Mapped["FinancialProduct"] = relationship(back_populates="values")


class ProductTransaction(CreatedAtMixin, Base):
    """Transaction on a financial product (buy, sell, dividend, etc.)."""

    __tablename__ = "product_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("financial_products.id"), nullable=False
    )
    transaction_type_id: Mapped[int] = mapped_column(
        ForeignKey("transaction_types.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 5), nullable=False)
    amount_base_currency: Mapped[Decimal | None] = mapped_column(Numeric(19, 5))
    units: Mapped[Decimal | None] = mapped_column(Numeric(19, 5))
    unit_value: Mapped[Decimal | None] = mapped_column(Numeric(19, 5))

    # Relationships
    product: Mapped["FinancialProduct"] = relationship(back_populates="transactions")
