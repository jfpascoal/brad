import pandas as pd
import re
from typing import List, Dict
from decimal import Decimal
from collections import defaultdict, namedtuple
from logging import getLogger

from brad.data import TABS, HISTORY_FILE
from brad.data.reference import get_account_label_map, get_financial_product_label_map
from brad.data.backup import backup_data

logger = getLogger(__name__)

HISTORY_LBL = 'history'

BalanceRow = namedtuple('BalanceRow', ['date', 'balance'])
ValueRow = namedtuple('ValueRow', ['date', 'units', 'invested_value', 'current_value'])


def parse_accounts(history_file: str, tabs: List[str]) -> Dict[str, List[BalanceRow]]:
    """
    Parse account balances from Excel tabs and return all balances for each account.

    :param history_file: Path to the Excel file containing historical account data
    :param tabs: List of sheet names to process
    :return: Dictionary mapping account names to list of (date, balance) tuples
    """
    balances = defaultdict(list)

    for tab in tabs:
        df = pd.read_excel(history_file, sheet_name=tab, parse_dates=[0])

        date_col = df.columns[0]
        for acct in df.columns[1:]:
            # Get all entries for this account
            for _, row in df.iterrows():
                date_val = row[date_col]
                balance_val = row[acct]

                # Skip if balance is missing or zero
                if pd.isna(balance_val) or balance_val == 0:
                    continue

                date_val = date_val.to_pydatetime()
                balance_val = Decimal(str(balance_val))

                balances[acct.strip()].append(BalanceRow(date=date_val, balance=balance_val))

    return dict(balances)


def parse_financial_products(history_file: str, tabs: List[str]) -> Dict[str, List[ValueRow]]:
    """
    Parse product values from Excel tabs and return all values for each product.

    :param history_file: Path to the Excel file containing historical product data
    :param tabs: List of sheet names to process
    :return: Dictionary mapping product names to list of (date, units, investment, value) tuples
    """
    units_lbl = {'Unidades', 'U.P.'}
    investment_lbl = {'Valor investido'}
    value_lbl = {'Valor actual', 'Valor'}
    pat = re.compile('|'.join(list(units_lbl) + list(investment_lbl) + list(value_lbl)))
    values = defaultdict(list)

    for tab in tabs:
        logger.debug(f"Parsing tab '{tab}'...")
        df = pd.read_excel(history_file, sheet_name=tab, parse_dates=[0])

        date_col = df.columns[0]
        col_map = defaultdict(dict)

        # Get column map for each product
        for col in df.columns[1:]:
            match = re.search(pat, col)
            if not match:
                logger.warning(f"Could not parse name of column '{col}' in tab '{tab}'.")
                continue
            lbl = match.group(0)
            prod_name = col[:match.start(0) - 1].strip()
            if lbl in units_lbl:
                col_map[prod_name]['units'] = col
            elif lbl in investment_lbl:
                col_map[prod_name]['investment'] = col
            elif lbl in value_lbl:
                col_map[prod_name]['value'] = col

        # Get values for each product
        for prod in col_map:
            logger.debug(f"Parsing product '{prod}' with columns: {col_map[prod]}")
            for _, row in df.iterrows():
                date = row[date_col]
                units = row[col_map[prod]['units']] if 'units' in col_map[prod] else None
                investment = row[col_map[prod]['investment']] if 'investment' in col_map[prod] else None
                value = row[col_map[prod]['value']] if 'value' in col_map[prod] else None

                # Skip if value is missing or zero
                if pd.isna(value) or value == 0:
                    continue

                values[prod].append(ValueRow(
                    date=date.to_pydatetime(),
                    units=Decimal(str(units)) if units is not None else units,
                    invested_value=Decimal(str(investment)) if investment is not None else investment,
                    current_value=Decimal(str(value)) if value is not None else value
                ))

    return dict(values)


def ingest_from_excel(history_file: str = HISTORY_FILE, tabs: Dict[str, List[str]] = TABS):
    data = defaultdict(list)

    # Process account balances
    account_labels = get_account_label_map()
    accounts = parse_accounts(history_file, tabs['accounts'])
    for account_lbl, balances in accounts.items():
        account_name = account_labels.get(account_lbl)
        if not account_name:
            logger.warning(f"Account label not found in reference data: '{account_lbl}'. Skipping account.")
            continue

        for balance in balances:
            balance_dict = balance._asdict() | {'account_name': account_name}
            data['account_balance'].append(balance_dict)

    # Process financial product values
    product_labels = get_financial_product_label_map()
    financial_products = parse_financial_products(history_file, tabs['financial_products'])
    for product_lbl, values in financial_products.items():
        product_name = product_labels.get(product_lbl)
        if not product_name:
            logger.warning(f"Product label not found in reference data: '{product_lbl}'. Skipping product.")
            continue
        
        for value in values:
            value_dict = value._asdict() | {'financial_product_name': product_name}
            data['product_value'].append(value_dict)

    # Backup the processed data
    backup_data('history', data=data, source='excel', fmt='json')
