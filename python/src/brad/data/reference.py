from typing import List, Dict

from brad.data import REFERENCE_DATA



def get_label_map(reference_data: List[Dict]) -> Dict[str, str]:
    return {ref.get('_historylabel'): ref.get('name')
            for ref in reference_data
            if '_historylabel' in ref}


def get_account_label_map() -> Dict[str, str]:
    accounts = REFERENCE_DATA.get('accounts')
    return get_label_map(accounts) if accounts else {}


def get_financial_product_label_map() -> Dict[str, str]:
    financial_products = REFERENCE_DATA.get('financial_products')
    return get_label_map(financial_products) if financial_products else {}
