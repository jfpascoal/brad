from decimal import Decimal

import pandas as pd
from unittest.mock import patch

from brad.services.ingestion import _parse_account_balances


def test_parse_account_balances_skips_empty_and_zero():
    """Verify that empty, NaT, or zero values are skipped."""
    mock_df = pd.DataFrame(
        {
            "Date": [
                pd.Timestamp("2024-01-01"),
                pd.Timestamp("2024-01-02"),
                pd.NaT,  # NaT date should be skipped
            ],
            "My Account": [100.50, 0, 50.0],  # zero should be skipped
        }
    )

    with patch("pandas.read_excel", return_value=mock_df):
        balances = _parse_account_balances("fake_file.ods", ["Tab 1"])

        # Only 1 valid row: 2024-01-01 / 100.50. The zero and NaT rows are skipped.
        assert len(balances["My Account"]) == 1
        assert balances["My Account"][0]["balance"] == Decimal("100.5")


def test_parse_account_balances_multiple_tabs():
    """Ensure data is loaded across multiple tab names."""
    df1 = pd.DataFrame(
        {"Date": [pd.Timestamp("2024-01-01")], "Acct1": [50.0], "Acct2": [70.0]}
    )
    df2 = pd.DataFrame({"Date": [pd.Timestamp("2024-01-02")], "Acct1": [60.0]})

    def mock_read_excel(*args, **kwargs):
        return df1 if kwargs.get("sheet_name") == "Tab 1" else df2

    with patch("pandas.read_excel", side_effect=mock_read_excel):
        balances = _parse_account_balances("fake_file.ods", ["Tab 1", "Tab 2"])

        assert len(balances["Acct1"]) == 2
        assert len(balances["Acct2"]) == 1
