"""Ingestion service for importing historical data from Excel."""

import logging
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

# TODO(refactor): Replace `pandas` with a lighter library like `openpyxl` or `pyexcel-ods`.
# pandas is an extremely heavy dependency (>30MB) just to read basic spreadsheet tabs.
# Since we only consume flat data and aren't doing complex DataFrame aggregations here,
# a dedicated excel reader would significantly reduce environment bloat and install time.
import pandas as pd
import yaml
from sqlalchemy.orm import Session

from brad.core.config import get_settings
from brad.core.models.operational import AccountBalance, ProductValue
from brad.core.utils import load_yaml
from brad.repositories.accounts import AccountRepository
from brad.repositories.products import ProductRepository

logger = logging.getLogger(__name__)


def _build_history_map(seed_dir: Path) -> tuple[dict, dict]:
    """Build mapping from _history_label to entity name from seed files.

    Returns:
        tuple containing (account_label_map, product_label_map)
    """
    account_map = {}
    for item in load_yaml(seed_dir / "accounts.yaml"):
        label = item.get("_history_label")
        name = item.get("name")
        if label and name:
            account_map[label] = name

    product_map = {}
    for item in load_yaml(seed_dir / "financial_products.yaml"):
        label = item.get("_history_label")
        name = item.get("name")
        if label and name:
            product_map[label] = name

    return account_map, product_map


def _parse_account_balances(history_file: str, tabs: list) -> dict:
    """Parse account balances from Excel tabs."""
    balances = defaultdict(list)

    for tab in tabs:
        try:
            df = pd.read_excel(history_file, sheet_name=tab, parse_dates=[0])
        except ValueError as e:
            logger.warning(f"Failed to read sheet '{tab}': {e}")
            continue

        date_col = df.columns[0]
        for acct in df.columns[1:]:
            for _, row in df.iterrows():
                date_val = row[date_col]
                balance_val = row[acct]

                if pd.isna(date_val) or pd.isna(balance_val) or balance_val == 0:
                    continue

                balances[acct.strip()].append(
                    {
                        "date": date_val.to_pydatetime().date(),
                        "balance": Decimal(str(balance_val)),
                    }
                )

    return dict(balances)


def _parse_product_values(
    history_file: str,
    tabs: list,
    labels_config: dict,
) -> dict:
    """Parse financial product values from Excel tabs."""
    units_lbl = labels_config.get("units", [])
    investment_lbl = labels_config.get("investment", [])
    value_lbl = labels_config.get("value", [])

    all_lbls = units_lbl + investment_lbl + value_lbl
    if not all_lbls:
        return {}

    pat = re.compile("|".join(re.escape(lbl) for lbl in all_lbls))
    values = defaultdict(list)

    for tab in tabs:
        try:
            df = pd.read_excel(history_file, sheet_name=tab, parse_dates=[0])
        except ValueError as e:
            logger.warning(f"Failed to read sheet '{tab}': {e}")
            continue

        date_col = df.columns[0]
        col_map = defaultdict(dict)

        for col in df.columns[1:]:
            match = re.search(pat, col)
            if not match:
                logger.warning(
                    f"Could not parse name of column '{col}' in tab '{tab}'."
                )
                continue
            lbl = match.group(0)
            prod_name = col[: match.start(0) - 1].strip()
            if lbl in units_lbl:
                col_map[prod_name]["units"] = col
            elif lbl in investment_lbl:
                col_map[prod_name]["investment"] = col
            elif lbl in value_lbl:
                col_map[prod_name]["value"] = col

        for prod, cols in col_map.items():
            for _, row in df.iterrows():
                date_val = row[date_col]
                units_val = row[cols["units"]] if "units" in cols else None
                value_val = row[cols["value"]] if "value" in cols else None

                if pd.isna(date_val) or pd.isna(value_val) or value_val == 0:
                    continue

                values[prod].append(
                    {
                        "date": date_val.to_pydatetime().date(),
                        "units": Decimal(str(units_val))
                        if pd.notna(units_val)
                        else None,
                        "current_value": Decimal(str(value_val))
                        if pd.notna(value_val)
                        else None,
                    }
                )

    return dict(values)


def ingest_from_excel(session: Session, history_file: Path) -> dict:
    """Ingest historical data from an Excel file into the database.

    :param session: SQLAlchemy session
    :param history_file: Path to the Excel file
    :return: Dictionary with ingestion counts
    """
    settings = get_settings()

    config_path = settings.config_dir / "history.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing history config at: {config_path}")

    with config_path.open() as f:
        config = yaml.safe_load(f) or {}
        tabs_config = config.get("tabs", {})
        labels_config = config.get("financial_product_labels", {})

    logger.info(f"Loading historical data from '{history_file}'...")

    account_lbl_map, product_lbl_map = _build_history_map(settings.seed_dir)
    account_repo = AccountRepository(session)
    product_repo = ProductRepository(session)

    results = {"account_balances": 0, "product_values": 0}

    # Process account balances
    acct_tabs = tabs_config.get("accounts", [])
    if acct_tabs:
        accounts_data = _parse_account_balances(str(history_file), acct_tabs)
        for lbl, balances in accounts_data.items():
            name = account_lbl_map.get(lbl)
            if not name:
                logger.warning(f"Label '{lbl}' not in seed data. Skipping.")
                continue

            entity = account_repo.get_by_name(name)
            if not entity:
                logger.warning(f"Account '{name}' not found in DB. Skipping.")
                continue

            for bal in balances:
                record = AccountBalance(account_id=entity.id, **bal)
                session.merge(record)
                results["account_balances"] += 1

    # Process financial products
    prod_tabs = tabs_config.get("financial_products", [])
    if prod_tabs:
        products_data = _parse_product_values(
            str(history_file), prod_tabs, labels_config
        )
        for lbl, values in products_data.items():
            name = product_lbl_map.get(lbl)
            if not name:
                logger.warning(f"Label '{lbl}' not in seed data. Skipping.")
                continue

            entity = product_repo.get_by_name(name)
            if not entity:
                logger.warning(f"Product '{name}' not found in DB. Skipping.")
                continue

            for val in values:
                record = ProductValue(product_id=entity.id, **val)
                session.merge(record)
                results["product_values"] += 1

    session.flush()
    return results
