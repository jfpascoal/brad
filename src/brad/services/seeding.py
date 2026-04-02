import logging
from datetime import date
from decimal import Decimal
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from brad.core.models.base import Base
from brad.core.models.operational import (
    Account,
    AccountHolder,
    FinancialProduct,
    Holder,
    ProductHolder,
    ProductTransaction,
    Provider,
)
from brad.core.models.reference import (
    AccountType,
    Currency,
    ProductType,
    TransactionType,
)

logger = logging.getLogger(__name__)


def _load_yaml(path: Path) -> list[dict]:
    """Load a YAML fixture file."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return data if data else []


def _resolve_name(session: Session, model: type[Base], name: str) -> int:
    """Look up an entity by name and return its ID."""
    stmt = select(model).where(model.name == name)  # type: ignore
    entity = session.scalars(stmt).first()
    if entity is None:
        raise ValueError(f"{model.__name__} with name '{name}' not found")
    return entity.id  # type: ignore


def _seed_simple(session: Session, model: type[Base], items: list[dict]) -> int:
    """Insert or update simple entities using natural key de-duplication."""
    count = 0
    # Determine the natural key: 'code' for Currency, 'name' for everything else
    key_attr = "code" if hasattr(model, "code") else "name"
    for item in items:
        key_val = item.get(key_attr)
        stmt = select(model).where(getattr(model, key_attr) == key_val)
        existing = session.scalars(stmt).first()
        if existing:
            for k, v in item.items():
                setattr(existing, k, v)
        else:
            session.add(model(**item))
        count += 1
    session.flush()
    return count


def _seed_accounts(session: Session, items: list[dict]) -> int:
    """Seed accounts with holder junction and FK resolution."""
    count = 0
    for item in items:
        holder_names = item.pop("holder_names", [])
        item.pop("_history_label", None)

        # Resolve FKs
        item["account_type_id"] = _resolve_name(
            session, AccountType, item.pop("account_type")
        )
        item["provider_id"] = _resolve_name(
            session, Provider, item.pop("provider_name")
        )

        # Parse dates
        for date_field in ("opening_date", "closing_date"):
            val = item.get(date_field)
            if isinstance(val, str):
                item[date_field] = date.fromisoformat(val)

        # Check if account already exists by name
        existing = session.scalars(
            select(Account).where(Account.name == item["name"])
        ).first()
        if existing:
            count += 1
            continue

        account = Account(**item)
        session.add(account)
        session.flush()  # get account.id

        # Create holder links
        for ordinal, name in enumerate(holder_names, start=1):
            holder_id = _resolve_name(session, Holder, name)
            link = AccountHolder(
                account_id=account.id, holder_id=holder_id, ordinal=ordinal
            )
            session.add(link)
        count += 1

    session.flush()
    return count


def _seed_financial_products(session: Session, items: list[dict]) -> int:
    """Seed financial products with holder junction, linked account, and history transactions."""
    count = 0
    txn_count = 0

    for item in items:
        holder_names = item.pop("holder_names", [])
        history_txns = item.pop("_history_transactions", [])
        item.pop("_history_label", None)

        # Resolve FKs
        item["product_type_id"] = _resolve_name(
            session, ProductType, item.pop("product_type")
        )
        item["provider_id"] = _resolve_name(
            session, Provider, item.pop("provider_name")
        )

        # Resolve linked account (optional)
        linked_account_name = item.pop("linked_account_name", None)
        if linked_account_name:
            item["linked_account_id"] = _resolve_name(
                session, Account, linked_account_name
            )

        # Check if product already exists by name
        existing = session.scalars(
            select(FinancialProduct).where(FinancialProduct.name == item.get("name"))
        ).first()
        if existing:
            count += 1
            continue

        product = FinancialProduct(**item)
        session.add(product)
        session.flush()  # get product.id

        # Create holder links
        for ordinal, name in enumerate(holder_names, start=1):
            holder_id = _resolve_name(session, Holder, name)
            link = ProductHolder(
                product_id=product.id, holder_id=holder_id, ordinal=ordinal
            )
            session.add(link)

        # Seed historical transactions
        for txn in history_txns:
            txn_type_id = _resolve_name(
                session, TransactionType, txn["transaction_type"]
            )
            pt = ProductTransaction(
                date=date.fromisoformat(txn["date"]),
                product_id=product.id,
                transaction_type_id=txn_type_id,
                amount=Decimal(str(txn["amount"])),
                amount_base_currency=(
                    Decimal(str(txn["amount_base_currency"]))
                    if txn.get("amount_base_currency")
                    else None
                ),
                units=(Decimal(str(txn["units"])) if txn.get("units") else None),
                unit_value=(
                    Decimal(str(txn["unit_value"])) if txn.get("unit_value") else None
                ),
            )
            session.add(pt)
            txn_count += 1

        count += 1

    session.flush()
    logger.info(f"Seeded {txn_count} product transactions from fixtures")
    return count


def seed_all(session: Session, seed_dir: Path) -> dict[str, int]:
    """Load all initial data files into the database in dependency order.

    Returns a dict of {entity_name: count_seeded}.
    """
    results: dict[str, int] = {}

    # 1. Reference/dimension tables (no FK dependencies)
    for filename, model in [
        ("currencies.yaml", Currency),
        ("account_types.yaml", AccountType),
        ("product_types.yaml", ProductType),
        ("transaction_types.yaml", TransactionType),
    ]:
        path = seed_dir / filename
        if path.exists():
            items = _load_yaml(path)
            results[filename] = _seed_simple(session, model, items)
            logger.info(f"Imported {results[filename]} items from {filename}")

    # 2. Entities with no FK to other operational tables
    for filename, model in [
        ("providers.yaml", Provider),
        ("holders.yaml", Holder),
    ]:
        path = seed_dir / filename
        if path.exists():
            items = _load_yaml(path)
            results[filename] = _seed_simple(session, model, items)
            logger.info(f"Imported {results[filename]} items from {filename}")

    # 3. Accounts (depends on types, providers, holders)
    path = seed_dir / "accounts.yaml"
    if path.exists():
        items = _load_yaml(path)
        results["accounts.yaml"] = _seed_accounts(session, items)
        logger.info(f"Imported {results['accounts.yaml']} accounts")

    # 4. Financial products (depends on types, providers, holders, accounts)
    path = seed_dir / "financial_products.yaml"
    if path.exists():
        items = _load_yaml(path)
        results["financial_products.yaml"] = _seed_financial_products(session, items)
        logger.info(f"Imported {results['financial_products.yaml']} financial products")

    return results
