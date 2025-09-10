from collections import defaultdict
import os
import json
from typing import List, Dict, Any

from brad.data import BACKUP_DIR
from brad.sql.schema import ACCOUNTS, FINANCIAL_PRODUCTS, ACCOUNT_TRANSACTIONS, PRODUCT_TRANSACTIONS


HISTORY_LBL = "_history_label"
HISTORY_TXNS = "_history_transactions"
REFERENCE_PATH = os.path.join(BACKUP_DIR, "reference.json")


def get_data() -> Dict[str, Any]:
    """Get the reference data."""
    with open(REFERENCE_PATH, 'rb') as f:
        return json.load(f).get("data", {})


def get_label_map(reference_data: List[Dict]) -> Dict[str, str]:
    """Get a mapping of historical labels to their names."""
    return {ref.get(HISTORY_LBL): ref.get('name')
            for ref in reference_data
            if HISTORY_LBL in ref}


def get_account_label_map() -> Dict[str, str]:
    """Get a mapping of account labels to their names."""
    accounts = get_data().get(ACCOUNTS)
    return get_label_map(accounts) if accounts else {}


def get_financial_product_label_map() -> Dict[str, str]:
    """Get a mapping of financial product labels to their names."""
    financial_products = get_data().get(FINANCIAL_PRODUCTS)
    return get_label_map(financial_products) if financial_products else {}


def get_history_transactions(data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get history transactions from reference data.
    
    :param data: Reference data.
    :return: Dictionary with account and product transactions.
    """
    transactions = defaultdict(list)

    for acct in data.get(ACCOUNTS, []):
        account_name = acct.get('name')
        account_transactions = acct.get(HISTORY_TXNS)
        if account_transactions:
            transactions[ACCOUNT_TRANSACTIONS] += (
                [{"account_name": account_name} | tx for tx in account_transactions]
            )

    for product in data.get(FINANCIAL_PRODUCTS, []):
        product_name = product.get('name')
        product_transactions = product.get(HISTORY_TXNS)
        if product_transactions:
            transactions[PRODUCT_TRANSACTIONS] += (
                [{"financial_product_name": product_name} | tx for tx in product_transactions]
            )

    return dict(transactions)


def remove_historical_attributes(data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Remove historical attributes from reference data. Removal is done in place.
    
    :param data: Reference data with potential historical attributes
    :return: Reference data without historical attributes
    """
    for _, entity in data.items():
        for element in entity:
            if HISTORY_LBL in element:
                element.pop(HISTORY_LBL)
            if HISTORY_TXNS in element:
                element.pop(HISTORY_TXNS)
    return data