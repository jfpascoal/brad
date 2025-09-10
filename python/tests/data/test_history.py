import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock

import pandas as pd

from brad.data.history import (
    parse_accounts,
    parse_financial_products,
    ingest_from_excel,
    BalanceRow,
    ValueRow,
    HISTORY,
    ACCOUNT_BALANCE,
    FINANCIAL_PRODUCT_VALUE
)


class TestBalanceRow(unittest.TestCase):
    """Test cases for the BalanceRow namedtuple."""

    def test_balance_row_creation(self):
        """Test BalanceRow can be created with correct fields."""
        date = datetime(2023, 1, 1)
        balance = Decimal('1000.50')

        row = BalanceRow(date=date, balance=balance)

        self.assertEqual(date, row.date)
        self.assertEqual(balance, row.balance)

    def test_balance_row_as_dict(self):
        """Test BalanceRow can be converted to dictionary."""
        date = datetime(2023, 1, 1)
        balance = Decimal('1000.50')

        row = BalanceRow(date=date, balance=balance)
        result = row._asdict()

        expected = {'date': date, 'balance': balance}
        self.assertEqual(expected, result)


class TestValueRow(unittest.TestCase):
    """Test cases for the ValueRow namedtuple."""

    def test_value_row_creation(self):
        """Test ValueRow can be created with correct fields."""
        date = datetime(2023, 1, 1)
        units = Decimal('100')
        current_value = Decimal('1200.00')

        row = ValueRow(date=date, units=units, current_value=current_value)

        self.assertEqual(date, row.date)
        self.assertEqual(units, row.units)
        self.assertEqual(current_value, row.current_value)

    def test_value_row_with_none_values(self):
        """Test ValueRow can be created with None values."""
        date = datetime(2023, 1, 1)

        row = ValueRow(date=date, units=None, current_value=Decimal('1200.00'))

        self.assertEqual(date, row.date)
        self.assertIsNone(row.units)
        self.assertEqual(Decimal('1200.00'), row.current_value)

    def test_value_row_as_dict(self):
        """Test ValueRow can be converted to dictionary."""
        date = datetime(2023, 1, 1)
        units = Decimal('100')
        current_value = Decimal('1200.00')

        row = ValueRow(date=date, units=units, current_value=current_value)
        result = row._asdict()

        expected = {
            'date': date,
            'units': units,
            'current_value': current_value
        }
        self.assertEqual(expected, result)


@patch('brad.data.history.pd.read_excel')
class TestParseAccounts(unittest.TestCase):
    """Test cases for the parse_accounts function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_file = 'test_history.ods'
        self.test_tabs = ['tab1', 'tab2']

        # Create mock DataFrame data
        self.mock_df1 = pd.DataFrame({
            'Date': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-02-01')],
            'Account A': [1000.0, 1050.0],
            'Account B': [2000.0, 0.0],  # Second value is zero, should be skipped
            'Account C': [None, 500.0]  # First value is None, should be skipped
        })

        self.mock_df2 = pd.DataFrame({
            'Date': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-02-01')],
            'Account D': [3000.0, 3100.0],
            'Account E': [4000.0, 4200.0]
        })

    def test_parse_accounts_success(self, mock_read_excel):
        """Test successful parsing of account balances."""
        mock_read_excel.side_effect = [self.mock_df1, self.mock_df2]

        result = parse_accounts(self.test_file, self.test_tabs)

        # Check that pd.read_excel was called correctly
        self.assertEqual(2, mock_read_excel.call_count)
        mock_read_excel.assert_any_call(self.test_file, sheet_name='tab1', parse_dates=[0])
        mock_read_excel.assert_any_call(self.test_file, sheet_name='tab2', parse_dates=[0])

        # Check the results
        self.assertIsInstance(result, dict)
        self.assertIn('Account A', result)
        self.assertIn('Account B', result)
        self.assertIn('Account C', result)
        self.assertIn('Account D', result)
        self.assertIn('Account E', result)

        # Check Account A data
        account_a_data = result['Account A']
        self.assertEqual(2, len(account_a_data))
        self.assertEqual(datetime(2023, 1, 1), account_a_data[0].date)
        self.assertEqual(Decimal('1000.0'), account_a_data[0].balance)
        self.assertEqual(datetime(2023, 2, 1), account_a_data[1].date)
        self.assertEqual(Decimal('1050.0'), account_a_data[1].balance)

        # Check Account B data (should only have one entry due to zero filtering)
        account_b_data = result['Account B']
        self.assertEqual(1, len(account_b_data))
        self.assertEqual(datetime(2023, 1, 1), account_b_data[0].date)
        self.assertEqual(Decimal('2000.0'), account_b_data[0].balance)

        # Check Account C data (should only have one entry due to None filtering)
        account_c_data = result['Account C']
        self.assertEqual(1, len(account_c_data))
        self.assertEqual(datetime(2023, 2, 1), account_c_data[0].date)
        self.assertEqual(Decimal('500.0'), account_c_data[0].balance)

    def test_parse_accounts_empty_tabs(self, mock_read_excel):
        """Test parsing with empty tabs list."""
        result = parse_accounts(self.test_file, [])

        mock_read_excel.assert_not_called()
        self.assertEqual({}, result)

    def test_parse_accounts_whitespace_in_account_names(self, mock_read_excel):
        """Test that account names with whitespace are stripped."""
        df_with_whitespace = pd.DataFrame({
            'Date': [pd.Timestamp('2023-01-01')],
            '  Account A  ': [1000.0],
            '\tAccount B\n': [2000.0]
        })
        mock_read_excel.return_value = df_with_whitespace

        result = parse_accounts(self.test_file, ['tab1'])

        self.assertIn('Account A', result)
        self.assertIn('Account B', result)
        self.assertNotIn('  Account A  ', result)
        self.assertNotIn('\tAccount B\n', result)

    def test_parse_accounts_file_error(self, mock_read_excel):
        """Test handling of file reading errors."""
        mock_read_excel.side_effect = FileNotFoundError("File not found")

        with self.assertRaises(FileNotFoundError):
            parse_accounts(self.test_file, self.test_tabs)

@patch('brad.data.history.FINANCIAL_PRODUCT_LABELS', {
        'units': ['Units', 'U.P.'],
        'investment': ['Invested value'],
        'value': ['Current value', 'Value']
    })

@patch('brad.data.history.logger')
@patch('brad.data.history.pd.read_excel')
class TestParseFinancialProducts(unittest.TestCase):
    """Test cases for the parse_financial_products function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_file = 'test_history.ods'
        self.test_tabs = ['products1', 'products2']

        # Create mock DataFrame with various column patterns
        self.mock_df1 = pd.DataFrame({
            'Date': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-02-01')],
            'Product A Units': [100.0, 105.0],
            'Product A Invested value': [1000.0, 1000.0],
            'Product A Current value': [1200.0, 1300.0],
            'Product B U.P.': [50.0, 55.0],
            'Product B Value': [2000.0, 0.0]  # Second value is zero, should be skipped
        })

        self.mock_df2 = pd.DataFrame({
            'Date': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-02-01')],
            'Product C Units': [200.0, 210.0],
            'Product C Value': [3000.0, None]  # Second value is None, should be skipped
        })

    def test_parse_financial_products_success(self, mock_read_excel, mock_logger):
        """Test successful parsing of financial product values."""
        mock_read_excel.side_effect = [self.mock_df1, self.mock_df2]

        result = parse_financial_products(self.test_file, self.test_tabs)

        # Check that pd.read_excel was called correctly
        self.assertEqual(2, mock_read_excel.call_count)
        mock_read_excel.assert_any_call(self.test_file, sheet_name='products1', parse_dates=[0])
        mock_read_excel.assert_any_call(self.test_file, sheet_name='products2', parse_dates=[0])

        # Check the results
        self.assertIsInstance(result, dict)
        self.assertIn('Product A', result)
        self.assertIn('Product B', result)
        self.assertIn('Product C', result)

        # Check Product A data (should have complete data)
        product_a_data = result['Product A']
        self.assertEqual(2, len(product_a_data))

        first_entry = product_a_data[0]
        self.assertEqual(datetime(2023, 1, 1), first_entry.date)
        self.assertEqual(Decimal('100.0'), first_entry.units)
        self.assertEqual(Decimal('1200.0'), first_entry.current_value)

        # Check Product B data (should only have one entry due to zero filtering)
        product_b_data = result['Product B']
        self.assertEqual(1, len(product_b_data))
        self.assertEqual(datetime(2023, 1, 1), product_b_data[0].date)
        self.assertEqual(Decimal('50.0'), product_b_data[0].units)
        self.assertEqual(Decimal('2000.0'), product_b_data[0].current_value)

        # Check Product C data (should only have one entry due to None filtering)
        product_c_data = result['Product C']
        self.assertEqual(1, len(product_c_data))
        self.assertEqual(datetime(2023, 1, 1), product_c_data[0].date)

    def test_parse_financial_products_unrecognized_columns(self, mock_read_excel, mock_logger):
        """Test handling of unrecognized column patterns."""
        df_with_bad_columns = pd.DataFrame({
            'Date': [pd.Timestamp('2023-01-01')],
            'Product A Something': [1000.0],  # Unrecognized pattern
            'Random Column': [2000.0]  # Unrecognized pattern
        })
        mock_read_excel.return_value = df_with_bad_columns

        result = parse_financial_products(self.test_file, ['tab1'])

        # Should log warnings for unrecognized columns
        self.assertEqual(2, mock_logger.warning.call_count)

        # Should return empty dict since no valid columns found
        self.assertEqual({}, result)

    def test_parse_financial_products_partial_columns(self, mock_read_excel, mock_logger):
        """Test handling of products with only some column types."""
        df_partial = pd.DataFrame({
            'Date': [pd.Timestamp('2023-01-01')],
            'Product A Value': [1000.0]  # Only value column, no units or investment
        })
        mock_read_excel.return_value = df_partial

        result = parse_financial_products(self.test_file, ['tab1'])

        # Should still parse the product
        self.assertIn('Product A', result)
        product_data = result['Product A']
        self.assertEqual(1, len(product_data))

        entry = product_data[0]
        self.assertIsNone(entry.units)
        self.assertEqual(Decimal('1000.0'), entry.current_value)

    def test_parse_financial_products_empty_tabs(self, mock_read_excel, mock_logger):
        """Test parsing with empty tabs list."""
        result = parse_financial_products(self.test_file, [])

        mock_read_excel.assert_not_called()
        self.assertEqual({}, result)

@patch('brad.data.history.get_financial_product_label_map')
@patch('brad.data.history.get_account_label_map')
@patch('brad.data.history.parse_financial_products')
@patch('brad.data.history.parse_accounts')
class TestIngestFromExcel(unittest.TestCase):
    """Test cases for the ingest_from_excel function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_history_file = 'test_historical.ods'
        self.test_tabs = {
            'accounts': ['accounts_tab1', 'accounts_tab2'],
            'financial_products': ['products_tab1', 'products_tab2']
        }

        self.mock_accounts_data = {
            'Account A Label': [
                BalanceRow(date=datetime(2023, 1, 1), balance=Decimal('1000')),
                BalanceRow(date=datetime(2023, 2, 1), balance=Decimal('1100'))
            ],
            'Account B Label': [
                BalanceRow(date=datetime(2023, 1, 1), balance=Decimal('2000'))
            ]
        }

        self.mock_products_data = {
            'Product A Label': [
                ValueRow(
                    date=datetime(2023, 1, 1),
                    units=Decimal('100'),
                    current_value=Decimal('1200')
                )
            ],
            'Product B Label': [
                ValueRow(
                    date=datetime(2023, 1, 1),
                    units=Decimal('50'),
                    current_value=Decimal('2000')
                )
            ]
        }

        self.mock_account_labels = {
            'Account A Label': 'Account A Name',
            'Account B Label': 'Account B Name'
        }

        self.mock_product_labels = {
            'Product A Label': 'Product A Name',
            'Product B Label': 'Product B Name'
        }

    def test_ingest_from_excel_success(self, mock_parse_accounts, mock_parse_products,
                                       mock_get_account_labels, mock_get_product_labels):
        """Test successful data ingestion from Excel."""
        # Setup mocks
        mock_parse_accounts.return_value = self.mock_accounts_data
        mock_parse_products.return_value = self.mock_products_data
        mock_get_account_labels.return_value = self.mock_account_labels
        mock_get_product_labels.return_value = self.mock_product_labels

        # Call the function
        result = ingest_from_excel(self.test_history_file, self.test_tabs)

        # Verify parse functions were called correctly
        mock_parse_accounts.assert_called_once_with(
            self.test_history_file,
            self.test_tabs['accounts']
        )
        mock_parse_products.assert_called_once_with(
            self.test_history_file,
            self.test_tabs['financial_products']
        )

        # Verify label mapping functions were called
        mock_get_account_labels.assert_called_once()
        mock_get_product_labels.assert_called_once()

        # Verify returned data structure
        self.assertIsInstance(result, dict)
        self.assertIn(ACCOUNT_BALANCE, result)
        self.assertIn(FINANCIAL_PRODUCT_VALUE, result)

        # Check account balance data
        account_balances = result[ACCOUNT_BALANCE]
        self.assertEqual(3, len(account_balances))  # 2 + 1 from mock data

        # Check first account balance entry
        first_balance = account_balances[0]
        self.assertEqual(datetime(2023, 1, 1), first_balance['date'])
        self.assertEqual(Decimal('1000'), first_balance['balance'])
        self.assertEqual('Account A Name', first_balance['account_name'])

        # Check product value data
        product_values = result[FINANCIAL_PRODUCT_VALUE]
        self.assertEqual(2, len(product_values))

        # Check first product value entry
        first_value = product_values[0]
        self.assertEqual(datetime(2023, 1, 1), first_value['date'])
        self.assertEqual(Decimal('100'), first_value['units'])
        self.assertEqual(Decimal('1200'), first_value['current_value'])
        self.assertEqual('Product A Name', first_value['financial_product_name'])

    @patch('brad.data.history.logger')
    def test_ingest_from_excel_missing_account_labels(self, mock_logger, mock_parse_accounts, mock_parse_products,
                                                      mock_get_account_labels, mock_get_product_labels):
        """Test handling of missing account labels."""
        # Setup mocks with missing labels
        mock_accounts_with_missing = {
            'Account A Label': [BalanceRow(date=datetime(2023, 1, 1), balance=Decimal('1000'))],
            'Missing Account Label': [BalanceRow(date=datetime(2023, 1, 1), balance=Decimal('2000'))]
        }

        mock_parse_accounts.return_value = mock_accounts_with_missing
        mock_parse_products.return_value = {}
        mock_get_account_labels.return_value = {'Account A Label': 'Account A Name'}  # Missing second label
        mock_get_product_labels.return_value = {}

        result = ingest_from_excel(self.test_history_file, self.test_tabs)

        # Should log warning for missing label
        mock_logger.warning.assert_called_with(
            "Account label not found in reference data: 'Missing Account Label'. Skipping account."
        )

        # Verify returned data structure
        self.assertIsInstance(result, dict)

        # Should only have data for the account with valid label
        account_balances = result[ACCOUNT_BALANCE]
        self.assertEqual(1, len(account_balances))
        self.assertEqual('Account A Name', account_balances[0]['account_name'])

    @patch('brad.data.history.logger')
    def test_ingest_from_excel_missing_product_labels(self, mock_logger, mock_parse_accounts, mock_parse_products,
                                                      mock_get_account_labels, mock_get_product_labels):
        """Test handling of missing product labels."""
        # Setup mocks with missing labels
        mock_products_with_missing = {
            'Product A Label': [ValueRow(
                date=datetime(2023, 1, 1),
                units=Decimal('100'),
                current_value=Decimal('1200')
            )],
            'Missing Product Label': [ValueRow(
                date=datetime(2023, 1, 1),
                units=Decimal('50'),
                current_value=Decimal('2000')
            )]
        }

        mock_parse_accounts.return_value = {}
        mock_parse_products.return_value = mock_products_with_missing
        mock_get_account_labels.return_value = {}
        mock_get_product_labels.return_value = {'Product A Label': 'Product A Name'}  # Missing second label

        result = ingest_from_excel(self.test_history_file, self.test_tabs)

        # Should log warning for missing label
        mock_logger.warning.assert_called_with(
            "Product label not found in reference data: 'Missing Product Label'. Skipping product."
        )

        # Verify returned data structure
        self.assertIsInstance(result, dict)

        # Should only have data for the product with valid label
        product_values = result[FINANCIAL_PRODUCT_VALUE]
        self.assertEqual(1, len(product_values))
        self.assertEqual('Product A Name', product_values[0]['financial_product_name'])

    def test_ingest_from_excel_with_explicit_parameters(self, mock_parse_accounts, mock_parse_products,
                                                        mock_get_account_labels, mock_get_product_labels):
        """Test ingest with explicit parameters."""
        mock_parse_accounts.return_value = {}
        mock_parse_products.return_value = {}
        mock_get_account_labels.return_value = {}
        mock_get_product_labels.return_value = {}

        test_file = 'explicit_test.ods'
        test_tabs = {'accounts': ['explicit_accounts'], 'financial_products': ['explicit_products']}

        # Call with explicit parameters
        result = ingest_from_excel(test_file, test_tabs)

        # Should use the provided values
        mock_parse_accounts.assert_called_once_with(
            test_file,
            test_tabs['accounts']
        )
        mock_parse_products.assert_called_once_with(
            test_file,
            test_tabs['financial_products']
        )

    def test_ingest_from_excel_returns_data(self, mock_parse_accounts, mock_parse_products,
                                          mock_get_account_labels, mock_get_product_labels):
        """Test that ingest_from_excel returns the processed data."""
        # Setup mocks
        mock_parse_accounts.return_value = self.mock_accounts_data
        mock_parse_products.return_value = self.mock_products_data
        mock_get_account_labels.return_value = self.mock_account_labels
        mock_get_product_labels.return_value = self.mock_product_labels
        
        # Call the function
        result = ingest_from_excel(self.test_history_file, self.test_tabs)
        
        # Verify return value structure
        self.assertIsInstance(result, dict)
        self.assertIn(ACCOUNT_BALANCE, result)
        self.assertIn(FINANCIAL_PRODUCT_VALUE, result)
        
        # Verify account balance data
        account_balances = result[ACCOUNT_BALANCE]
        self.assertEqual(3, len(account_balances))  # 2 + 1 from mock data
        
        # Verify product value data
        product_values = result[FINANCIAL_PRODUCT_VALUE]
        self.assertEqual(2, len(product_values))
        
        # Verify specific data structure
        first_balance = account_balances[0]
        self.assertIn('date', first_balance)
        self.assertIn('balance', first_balance)
        self.assertIn('account_name', first_balance)
        
        first_value = product_values[0]
        self.assertIn('date', first_value)
        self.assertIn('units', first_value)
        self.assertIn('current_value', first_value)
        self.assertIn('financial_product_name', first_value)


class TestHistoryIntegration(unittest.TestCase):
    """Integration tests for the history module."""

    @patch('brad.data.history.FINANCIAL_PRODUCT_LABELS', {
        'units': ['Units', 'U.P.'],
        'investment': ['Invested Value'],
        'value': ['Current Value', 'Value']
    })
    @patch('brad.data.history.get_financial_product_label_map')
    @patch('brad.data.history.get_account_label_map')
    @patch('brad.data.history.pd.read_excel')
    def test_full_integration_workflow(self, mock_read_excel, mock_get_account_labels,
                                       mock_get_product_labels):
        """Test the complete workflow from Excel parsing to data backup."""
        # Setup realistic mock data
        accounts_df = pd.DataFrame({
            'Date': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-02-01')],
            'Checking Account': [1500.0, 1600.0],
            'Savings Account': [5000.0, 5200.0]
        })

        products_df = pd.DataFrame({
            'Date': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-02-01')],
            'Stock Fund A Units': [100.0, 105.0],
            'Stock Fund A Invested Value': [1000.0, 1000.0],
            'Stock Fund A Current Value': [1100.0, 1200.0],
            'Bond Fund B U.P.': [200.0, 200.0],
            'Bond Fund B Value': [2000.0, 1950.0]
        })

        # Mock read_excel to return different DataFrames for different tabs
        def mock_read_excel_side_effect(file, sheet_name, parse_dates):
            if sheet_name in ['accounts_tab']:
                return accounts_df
            elif sheet_name in ['products_tab']:
                return products_df
            else:
                raise ValueError(f"Unexpected sheet_name: {sheet_name}")

        mock_read_excel.side_effect = mock_read_excel_side_effect

        # Setup label mappings
        mock_get_account_labels.return_value = {
            'Checking Account': 'Primary Checking',
            'Savings Account': 'High Yield Savings'
        }

        mock_get_product_labels.return_value = {
            'Stock Fund A': 'Equity Growth Fund',
            'Bond Fund B': 'Corporate Bond Fund'
        }

        # Setup test parameters
        history_file = 'integration_test.ods'
        tabs = {
            'accounts': ['accounts_tab'],
            'financial_products': ['products_tab']
        }

        # Execute the integration
        result = ingest_from_excel(history_file, tabs)

        # Verify the complete workflow
        self.assertEqual(2, mock_read_excel.call_count)
        mock_get_account_labels.assert_called_once()
        mock_get_product_labels.assert_called_once()

        # Verify the final data structure
        self.assertIsInstance(result, dict)

        # Check account balances
        account_balances = result[ACCOUNT_BALANCE]
        self.assertEqual(4, len(account_balances))  # 2 accounts × 2 dates

        # Verify specific account balance entries
        checking_entries = [entry for entry in account_balances if entry['account_name'] == 'Primary Checking']
        self.assertEqual(2, len(checking_entries))
        self.assertEqual(Decimal('1500.0'), checking_entries[0]['balance'])
        self.assertEqual(Decimal('1600.0'), checking_entries[1]['balance'])

        # Check product values
        product_values = result[FINANCIAL_PRODUCT_VALUE]
        self.assertEqual(4, len(product_values))  # 2 products × 2 dates

        # Verify specific product value entries
        equity_entries = [entry for entry in product_values if entry['financial_product_name'] == 'Equity Growth Fund']
        self.assertEqual(2, len(equity_entries))
        self.assertEqual(Decimal('100.0'), equity_entries[0]['units'])
        self.assertEqual(Decimal('1100.0'), equity_entries[0]['current_value'])


if __name__ == '__main__':
    unittest.main()
