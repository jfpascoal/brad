from math import e
import unittest
import json
from unittest.mock import patch

from brad.data.reference import (
    get_data,
    get_label_map,
    get_account_label_map,
    get_financial_product_label_map,
    get_history_transactions,
    remove_historical_attributes,
    HISTORY_LBL,
    HISTORY_TXNS
)
from brad.sql.schema import ACCOUNTS, FINANCIAL_PRODUCTS, PRODUCT_TRANSACTIONS



class TestReference(unittest.TestCase):
    """Test cases for reference data functions."""
    
    @classmethod
    def setUpClass(cls):
        cls.mock_reference_data = {
            ACCOUNTS: [
                {HISTORY_LBL: 'account1', 'name': 'Account One'},
                {HISTORY_LBL: 'account2', 'name': 'Account Two'}
            ],
            FINANCIAL_PRODUCTS: [
                {HISTORY_LBL: 'product1', 'name': 'Product One'},
                {HISTORY_LBL: 'product2', 'name': 'Product Two',
                 HISTORY_TXNS: [
                    {
                        "date": "2025-01-01",
                        "transaction_type": "purchase",
                        "transaction_amount": 100.0,
                        "transaction_amount_eur": 100.0,
                        "units": 1.0,
                        "unit_value": 100.0
                    }
                ]}
            ]
        }
        
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data=json.dumps({"data": {"key": "value"}}))
    def test_get_data(self, mock_file):
        """Test that get_data reads and parses the reference data correctly."""
        data = get_data()
        self.assertEqual(data, {"key": "value"})
        mock_file.assert_called_once()

    def test_get_label_map(self):
        """Test that get_label_map returns a correct mapping."""
        reference_data = [
            {HISTORY_LBL: 'account1', 'name': 'Account One'},
            {HISTORY_LBL: 'account2', 'name': 'Account Two'},
            {'name': 'No Label'}  # This should be ignored
        ]
        expected_map = {
            'account1': 'Account One',
            'account2': 'Account Two'
        }
        result = get_label_map(reference_data)
        self.assertEqual(expected_map, result)

    def test_get_label_map_empty(self):
        """Test that get_label_map returns an empty dict for empty input."""
        reference_data = []
        result = get_label_map(reference_data)
        self.assertEqual({}, result)

    
    def test_get_account_label_map(self):
        """Test that get_account_label_map returns a correct mapping."""
        expected = {
            'account1': 'Account One',
            'account2': 'Account Two'
        }
        with patch('brad.data.reference.get_data', return_value=self.mock_reference_data):
            result = get_account_label_map()
        self.assertEqual(expected, result)

    def test_get_financial_product_label_map(self):
        """Test that get_financial_product_label_map returns a correct mapping."""
        expected = {
            'product1': 'Product One',
            'product2': 'Product Two'
        }
        with patch('brad.data.reference.get_data', return_value=self.mock_reference_data):
            result = get_financial_product_label_map()
        self.assertEqual(expected, result)
        
    def test_get_history_transactions(self):
        """Test that get_history_transactions returns correct transactions."""
        expected = {
            PRODUCT_TRANSACTIONS: [
                {
                    'financial_product_name': 'Product Two',
                    'date': '2025-01-01',
                    'transaction_type': 'purchase',
                    'transaction_amount': 100.0,
                    'transaction_amount_eur': 100.0,
                    'units': 1.0,
                    'unit_value': 100.0
                }
            ]
        }
        result = get_history_transactions(self.mock_reference_data)
        self.assertEqual(expected, result)
        
    def test_remove_historical_attributes(self):
        """Test that remove_historical_attributes removes history fields."""
        input_data = self.mock_reference_data.copy()
        expected = {
            ACCOUNTS: [
                {'name': 'Account One'},
                {'name': 'Account Two'}
            ],
            FINANCIAL_PRODUCTS: [
                {'name': 'Product One'},
                {'name': 'Product Two'}
            ]
        }
        self.assertNotEqual(expected, input_data)
        
        remove_historical_attributes(input_data)
        self.assertEqual(expected, input_data)

if __name__ == '__main__':
    unittest.main()
