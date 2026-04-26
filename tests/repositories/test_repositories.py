from datetime import date
from decimal import Decimal

import pytest

from brad.core.models.reference import (
    Currency,
    AccountType,
    ProductType,
    TransactionType,
)
from brad.core.models.operational import (
    Account,
    FinancialProduct,
    AccountBalance,
    Provider,
    Holder,
    AccountHolder,
    ProductHolder,
    AccountTransaction,
    ProductValue,
    ProductTransaction,
)
from brad.repositories.accounts import (
    AccountRepository,
    AccountBalanceRepository,
    AccountTransactionRepository,
)
from brad.repositories.products import (
    ProductRepository,
    ProductValueRepository,
    ProductTransactionRepository,
)


@pytest.fixture
def seed_references(db_session):
    provider = Provider(id=1, name="Test Provider", country="GB")
    currency = Currency(code="GBP", name="Pounds")
    acct_type = AccountType(id=1, name="Current Account", name_pt="Conta Corrente")
    prod_type = ProductType(id=1, name="ETF", name_pt="Fundo de Índice")
    txn_type = TransactionType(id=1, name="Deposit", name_pt="Depósito")

    db_session.add_all([provider, currency, acct_type, prod_type, txn_type])
    db_session.flush()
    return provider, currency, acct_type, prod_type, txn_type


@pytest.fixture
def seed_holders(db_session):
    h1 = Holder(id=1, name="João Ninguém")
    h2 = Holder(id=2, name="Maria Conceição")
    db_session.add_all([h1, h2])
    db_session.flush()
    return h1, h2


def test_base_repository_crud(db_session, seed_references):
    repo = AccountRepository(db_session)

    # 1. Create Many
    acc1 = Account(
        name="Checking João", account_type_id=1, currency_code="GBP", provider_id=1
    )
    acc2 = Account(
        name="Poupança Maria", account_type_id=1, currency_code="GBP", provider_id=1
    )

    saved = repo.create_many([acc1, acc2])
    assert len(saved) == 2
    assert saved[0].id is not None
    assert saved[1].name == "Poupança Maria"

    # 2. List All
    all_accs = repo.list_all()
    assert len(all_accs) >= 2

    # 3. Get By ID
    fetched = repo.get_by_id(saved[0].id)
    assert fetched == saved[0]

    # 4. Update
    saved[0].name = "Checking Atualizada"
    db_session.flush()
    updated = repo.get_by_id(saved[0].id)
    assert updated.name == "Checking Atualizada"

    # 5. Delete
    repo.delete(updated)
    assert repo.get_by_id(updated.id) is None


def test_account_repository_get_by_name(db_session, seed_references):
    repo = AccountRepository(db_session)
    repo.create(
        Account(
            name="Ações Ação", account_type_id=1, currency_code="GBP", provider_id=1
        )
    )

    fetched = repo.get_by_name("Ações Ação")
    assert fetched is not None
    assert fetched.name == "Ações Ação"

    missing = repo.get_by_name("Não Existe")
    assert missing is None


def test_product_repository_get_by_name(db_session, seed_references):
    repo = ProductRepository(db_session)
    repo.create(
        FinancialProduct(
            name="Fundo Imobiliário",
            product_type_id=1,
            currency_code="GBP",
            provider_id=1,
        )
    )

    assert repo.get_by_name("Fundo Imobiliário") is not None
    assert repo.get_by_name("Fake") is None


@pytest.mark.parametrize(
    "RepositoryClass, EntityClass, parent_id_kwarg",
    [
        (AccountRepository, Account, {"account_type_id": 1}),
        (ProductRepository, FinancialProduct, {"product_type_id": 1}),
    ],
)
def test_repository_get_active(
    db_session, seed_references, RepositoryClass, EntityClass, parent_id_kwarg
):
    repo = RepositoryClass(db_session)
    active_ent = EntityClass(
        name="Ativo",
        currency_code="GBP",
        provider_id=1,
        is_active=True,
        **parent_id_kwarg,
    )
    inactive_ent = EntityClass(
        name="Inativo",
        currency_code="GBP",
        provider_id=1,
        is_active=False,
        **parent_id_kwarg,
    )

    repo.create_many([active_ent, inactive_ent])

    actives = repo.get_active()
    assert len(actives) == 1
    assert actives[0].name == "Ativo"


@pytest.mark.parametrize(
    "RepositoryClass, EntityClass, LinkClass, parent_id_kwarg, fk",
    [
        (
            AccountRepository,
            Account,
            AccountHolder,
            {"account_type_id": 1},
            "account_id",
        ),
        (
            ProductRepository,
            FinancialProduct,
            ProductHolder,
            {"product_type_id": 1},
            "product_id",
        ),
    ],
)
def test_repository_set_holders(
    db_session,
    seed_references,
    seed_holders,
    RepositoryClass,
    EntityClass,
    LinkClass,
    parent_id_kwarg,
    fk,
):
    repo = RepositoryClass(db_session)
    ent = repo.create(
        EntityClass(
            name="Titularidade", currency_code="GBP", provider_id=1, **parent_id_kwarg
        )
    )

    h1, h2 = seed_holders

    # Set initially to h2 then h1
    repo.set_holders(ent, [h2.id, h1.id])
    db_session.flush()

    links = db_session.query(LinkClass).filter(getattr(LinkClass, fk) == ent.id).all()
    assert len(links) == 2
    # Check ordinals map correctly
    link_map = {link.holder_id: link.ordinal for link in links}
    assert link_map[h2.id] == 1
    assert link_map[h1.id] == 2

    # Overwrite just to h1
    repo.set_holders(ent, [h1.id])
    db_session.flush()

    links = db_session.query(LinkClass).filter(getattr(LinkClass, fk) == ent.id).all()
    assert len(links) == 1
    assert links[0].holder_id == h1.id
    assert links[0].ordinal == 1


@pytest.mark.parametrize(
    "RepositoryClass, EntityClass, fk_kwarg",
    [
        (AccountTransactionRepository, AccountTransaction, "account_id"),
        (ProductTransactionRepository, ProductTransaction, "product_id"),
    ],
)
def test_repository_get_transactions(
    db_session, seed_references, RepositoryClass, EntityClass, fk_kwarg
):
    # Setup parent
    if fk_kwarg == "account_id":
        parent = AccountRepository(db_session).create(
            Account(
                name="ParentAcc", account_type_id=1, currency_code="GBP", provider_id=1
            )
        )
    else:
        parent = ProductRepository(db_session).create(
            FinancialProduct(
                name="ParentProd", product_type_id=1, currency_code="GBP", provider_id=1
            )
        )

    repo = RepositoryClass(db_session)

    kw = {fk_kwarg: parent.id, "transaction_type_id": 1, "amount": Decimal("100.00")}
    t1 = EntityClass(date=date(2023, 1, 10), **kw)
    t2 = EntityClass(date=date(2023, 1, 15), **kw)
    t3 = EntityClass(date=date(2023, 1, 5), **kw)

    repo.create_many([t1, t2, t3])

    # It should return in descending order
    if hasattr(repo, "get_by_account"):
        res = repo.get_by_account(parent.id)
    else:
        res = repo.get_by_product(parent.id)

    assert len(res) == 3
    assert res[0].date == date(2023, 1, 15)
    assert res[1].date == date(2023, 1, 10)
    assert res[2].date == date(2023, 1, 5)


def test_account_balance_repository_queries(db_session, seed_references):
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

    # 2. Get Range
    range_bals = repo.get_by_date_range(
        account.id, date(2023, 1, 15), date(2023, 2, 15)
    )
    assert len(range_bals) == 1


def test_product_value_repository_get_latest(db_session, seed_references):
    product = FinancialProduct(
        name="ProdValTeste", product_type_id=1, currency_code="GBP", provider_id=1
    )
    db_session.add(product)
    db_session.commit()

    repo = ProductValueRepository(db_session)

    repo.create(
        ProductValue(
            product_id=product.id,
            date=date(2023, 1, 1),
            current_value=Decimal("100.00"),
        )
    )
    repo.create(
        ProductValue(
            product_id=product.id,
            date=date(2023, 4, 1),
            current_value=Decimal("120.00"),
        )
    )
    repo.create(
        ProductValue(
            product_id=product.id,
            date=date(2023, 2, 1),
            current_value=Decimal("110.00"),
        )
    )

    latest = repo.get_latest(product.id)
    assert latest.date == date(2023, 4, 1)
