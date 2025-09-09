import unittest
import json
from unittest.mock import patch

from brad.data.reference import (
    get_data,
    get_label_map,
    get_account_label_map,
    get_financial_product_label_map,
    get_history_transactions,
    get_reference_data_without_history,
    HISTORY_LBL,
    HISTORY_TXNS
)



class TestReference(unittest.TestCase):
    """Test cases for reference data functions."""
    
    @classmethod
    def setUpClass(cls):
        cls.mock_reference_data = {
            "accounts": [
                {HISTORY_LBL: 'account1', 'name': 'Account One'},
                {HISTORY_LBL: 'account2', 'name': 'Account Two'}
            ],
            "financial_products": [
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
            'product_transaction': [
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
        with patch('brad.data.reference.get_data', return_value=self.mock_reference_data):
            result = get_history_transactions()
        self.assertEqual(expected, result)
        
    def test_get_reference_data_without_history(self):
        """Test that get_reference_data_without_history removes history fields."""
        expected = {
            "accounts": [
                {'name': 'Account One'},
                {'name': 'Account Two'}
            ],
            "financial_products": [
                {'name': 'Product One'},
                {'name': 'Product Two'}
            ]
        }
        with patch('brad.data.reference.get_data', return_value=self.mock_reference_data):
            result = get_reference_data_without_history()
        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main()
