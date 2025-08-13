import unittest
from unittest.mock import patch

from brad.data.reference import get_label_map, get_account_label_map, get_financial_product_label_map

@patch('brad.data.reference.REFERENCE_DATA', {
        'accounts': [
            {'_historylabel': 'account1', 'name': 'Account One'},
            {'_historylabel': 'account2', 'name': 'Account Two'},
            {'name': 'No Label'}
        ],
        'financial_products': [
            {'_historylabel': 'product1', 'name': 'Product One'},
            {'_historylabel': 'product2', 'name': 'Product Two'},
            {'name': 'No Label'}
        ]
})
class TestReference(unittest.TestCase):
    """Test cases for reference data functions."""
    
    def test_get_label_map(self):
        """Test that get_label_map returns a correct mapping."""
        reference_data = [
            {'_historylabel': 'account1', 'name': 'Account One'},
            {'_historylabel': 'account2', 'name': 'Account Two'},
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
        result = get_account_label_map()
        self.assertEqual(expected, result)
        
    def test_get_financial_product_label_map(self):
        """Test that get_financial_product_label_map returns a correct mapping."""
        expected = {
            'product1': 'Product One',
            'product2': 'Product Two'
        }
        result = get_financial_product_label_map()
        self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()