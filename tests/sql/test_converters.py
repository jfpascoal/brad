import unittest
from datetime import date
from decimal import Decimal

from bread.sql.converters import decimal_adapter, decimal_converter, date_adapter, date_converter


class TestSqlConverters(unittest.TestCase):
    """
    Unit tests for the SQLite type converter functions.
    """

    def test_decimal_round_trip(self):
        """
        Tests that a Decimal object can be adapted and converted back to its
        original value.
        """
        test_cases = [
            Decimal('123.4567'),
            Decimal('-99.99'),
            Decimal('0.00'),
            Decimal('500'),
        ]

        for original_decimal in test_cases:
            with self.subTest(decimal=original_decimal):
                # Adapt the decimal to bytes for DB storage
                adapted_value = decimal_adapter(original_decimal)
                self.assertIsInstance(adapted_value, bytes)
                self.assertEqual(adapted_value, str(original_decimal).encode())

                # Convert the bytes back to a Decimal object
                converted_value = decimal_converter(adapted_value)
                self.assertIsInstance(converted_value, Decimal)
                self.assertEqual(original_decimal, converted_value)

    def test_date_round_trip(self):
        """
        Tests that a date object can be adapted and converted back to its
        original value.
        """
        test_cases = [
            date(2023, 10, 27),
            date(1999, 1, 1),
            date(2024, 2, 29),  # Leap year
        ]

        for original_date in test_cases:
            with self.subTest(date=original_date):
                # Adapt the date to a string for DB storage
                adapted_value = date_adapter(original_date)
                self.assertIsInstance(adapted_value, str)
                self.assertEqual(adapted_value, original_date.isoformat())

                # Convert the string (as bytes) back to a date object
                # The sqlite3 library passes the value from the DB as bytes.
                converted_value = date_converter(adapted_value.encode())
                self.assertIsInstance(converted_value, date)
                self.assertEqual(original_date, converted_value)


if __name__ == '__main__':
    unittest.main(verbosity=2)