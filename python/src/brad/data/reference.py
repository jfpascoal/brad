from collections import defaultdict
from email.policy import default
import os
import json
from typing import List, Dict, Any

from brad.data import BACKUP_DIR


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
    accounts = get_data().get('accounts')
    return get_label_map(accounts) if accounts else {}


def get_financial_product_label_map() -> Dict[str, str]:
    """Get a mapping of financial product labels to their names."""
    financial_products = get_data().get('financial_products')
    return get_label_map(financial_products) if financial_products else {}


def get_history_transactions() -> Dict[str, List[Dict[str, Any]]]:
    """Get history transactions from reference data."""
    transactions = defaultdict(list)
    data = get_data()
    
    for acct in data.get('accounts', []):
        account_name = acct.get('name')
        account_transactions = acct.get(HISTORY_TXNS)
        if account_transactions:
            transactions['account_transaction'] += (
                [{"account_name": account_name} | tx for tx in account_transactions]
            )
    
    for product in data.get('financial_products', []):
        product_name = product.get('name')
        product_transactions = product.get(HISTORY_TXNS)
        if product_transactions:
            transactions['product_transaction'] += (
                [{"financial_product_name": product_name} | tx for tx in product_transactions]
            )

    return dict(transactions)


def get_reference_data_without_history() -> Dict[str, List[Dict]]:
    """Get the reference data with history labels and transactions removed."""
    data = get_data().copy()
    
    for e in data.get('accounts', []) + data.get('financial_products', []):
        if HISTORY_LBL in e:
            e.pop(HISTORY_LBL)
        if HISTORY_TXNS in e:
            e.pop(HISTORY_TXNS)
        
    return data