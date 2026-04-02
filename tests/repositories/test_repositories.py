from datetime import date
from decimal import Decimal

import pytest

from brad.core.models.reference import Currency, AccountType, ProductType
from brad.core.models.operational import (
    Account,
    FinancialProduct,
    AccountBalance,
    Provider,
)
from brad.repositories.accounts import AccountRepository, AccountBalanceRepository
from brad.repositories.products import ProductRepository


@pytest.fixture
def seed_references(db_session):
    """Seed necessary lookup data before testing operational inserts."""
    provider = Provider(id=1, name="Test Provider", country="GB")
    currency = Currency(code="GBP", name="Pounds")
    acct_type = AccountType(id=1, name="Current Account")
    prod_type = ProductType(id=1, name="ETF")

    db_session.add_all([provider, currency, acct_type, prod_type])
    db_session.commit()
    return provider, currency, acct_type, prod_type


def test_base_repository_crud(db_session, seed_references):
    """Test BaseRepository CRUD operations efficiently via parametrisation setup."""
    repo = AccountRepository(db_session)

    # 1. Create
    new_account = Account(
        name="Checking", account_type_id=1, currency_code="GBP", provider_id=1
    )
    saved = repo.create(new_account)

    assert saved.id is not None
    assert saved.name == "Checking"

    # 2. Get By ID
    fetched = repo.get_by_id(saved.id)
    assert fetched == saved

    # 3. Update (SQLAlchemy tracks changes automatically)
    saved.name = "Updated Checking"
    db_session.flush()
    updated = repo.get_by_id(saved.id)
    assert updated.name == "Updated Checking"

    # 4. Delete
    repo.delete(updated)
    assert repo.get_by_id(updated.id) is None


def test_account_repository_get_by_name(db_session, seed_references):
    """Integration style test for custom repository fetch calls."""
    repo = AccountRepository(db_session)
    repo.create(
        Account(
            name="Unique Name XYZ",
            account_type_id=1,
            currency_code="GBP",
            provider_id=1,
        )
    )

    fetched = repo.get_by_name("Unique Name XYZ")
    assert fetched is not None
    assert fetched.name == "Unique Name XYZ"

    missing = repo.get_by_name("Does not exist")
    assert missing is None


def test_account_balance_repository_queries(db_session, seed_references):
    """Test specialized balance querying."""
    account = Account(
        name="Test Balances", account_type_id=1, currency_code="GBP", provider_id=1
    )
    db_session.add(account)
    db_session.commit()

    repo = AccountBalanceRepository(db_session)

    # Add scattered balances
    repo.create(
        AccountBalance(
            account_id=account.id, date=date(2023, 1, 1), balance=Decimal("10.00")
        )
    )
    repo.create(
        AccountBalance(
            account_id=account.id, date=date(2023, 2, 1), balance=Decimal("50.00")
        )
    )
    repo.create(
        AccountBalance(
            account_id=account.id, date=date(2023, 3, 1), balance=Decimal("20.00")
        )
    )

    # 1. Get Latest
    latest = repo.get_latest(account.id)
    assert latest.date == date(2023, 3, 1)
    assert latest.balance == Decimal("20.00")

    # 2. Get Range
    range_bals = repo.get_by_date_range(
        account.id, date(2023, 1, 15), date(2023, 2, 15)
    )
    assert len(range_bals) == 1
    assert range_bals[0].date == date(2023, 2, 1)


def test_product_repository_get_by_name(db_session, seed_references):
    """Verify product repository specific logic behaves identicall to accounts."""
    repo = ProductRepository(db_session)
    repo.create(
        FinancialProduct(
            name="Vanguard S&P", product_type_id=1, currency_code="GBP", provider_id=1
        )
    )

    assert repo.get_by_name("Vanguard S&P") is not None
    assert repo.get_by_name("Fake") is None
