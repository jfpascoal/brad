import unittest
from datetime import date
from decimal import Decimal

from brad.sql.types import SqlType, Integer, BigInt, Numeric, Boolean, Date, Text


class TestSqlType(unittest.TestCase):
    """Tests for the base SqlType class."""

    def test_sql_type_initialization(self):
        """Test that SqlType initializes correctly with name and python_type."""
        sql_type = SqlType("INTEGER", int)
        self.assertEqual("INTEGER", sql_type.name)
        self.assertEqual(int, sql_type.python_type)

    def test_py_method(self):
        """Test that py() returns the correct Python type."""
        sql_type = SqlType("TEXT", str)
        self.assertEqual(str, sql_type.py())

    def test_sql_method(self):
        """Test that sql() returns the correct SQL type name."""
        sql_type = SqlType("BOOLEAN", bool)
        self.assertEqual("BOOLEAN", sql_type.sql())


class TestIntegerType(unittest.TestCase):
    """Tests for the Integer SQL type."""

    def test_integer_initialization(self):
        """Test that Integer type initializes with correct SQL name and Python type."""
        integer_type = Integer()
        self.assertEqual("INTEGER", integer_type.sql())
        self.assertEqual(int, integer_type.py())


class TestBigIntType(unittest.TestCase):
    """Tests for the BigInt SQL type."""

    def test_bigint_initialization(self):
        """Test that BigInt type initializes with correct SQL name and Python type."""
        bigint_type = BigInt()
        self.assertEqual("BIGINT", bigint_type.sql())
        self.assertEqual(int, bigint_type.py())


class TestNumericType(unittest.TestCase):
    """Tests for the Numeric SQL type."""

    def test_numeric_default_precision_scale(self):
        """Test that Numeric uses default precision and scale when not specified."""
        numeric_type = Numeric()
        self.assertEqual("NUMERIC(19, 4)", numeric_type.sql())
        self.assertEqual(Decimal, numeric_type.py())

    def test_numeric_custom_precision_scale(self):
        """Test that Numeric accepts custom precision and scale values."""
        numeric_type = Numeric(10, 2)
        self.assertEqual("NUMERIC(10, 2)", numeric_type.sql())
        self.assertEqual(Decimal, numeric_type.py())

    def test_numeric_large_precision_scale(self):
        """Test Numeric with large precision and scale values."""
        numeric_type = Numeric(38, 15)
        self.assertEqual("NUMERIC(38, 15)", numeric_type.sql())
        self.assertEqual(Decimal, numeric_type.py())


class TestBooleanType(unittest.TestCase):
    """Tests for the Boolean SQL type."""

    def test_boolean_initialization(self):
        """Test that Boolean type initializes with correct SQL name and Python type."""
        boolean_type = Boolean()
        self.assertEqual("BOOLEAN", boolean_type.sql())
        self.assertEqual(bool, boolean_type.py())


class TestDateType(unittest.TestCase):
    """Tests for the Date SQL type."""

    def test_date_initialization(self):
        """Test that Date type initializes with correct SQL name and Python type."""
        date_type = Date()
        self.assertEqual("DATE", date_type.sql())
        self.assertEqual(date, date_type.py())


class TestTextType(unittest.TestCase):
    """Tests for the Text SQL type."""

    def test_text_initialization(self):
        """Test that Text type initializes with correct SQL name and Python type."""
        text_type = Text()
        self.assertEqual("TEXT", text_type.sql())
        self.assertEqual(str, text_type.py())


if __name__ == "__main__":
    unittest.main()
