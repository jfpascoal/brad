from datetime import date
from decimal import Decimal
from typing import Type


class SqlType:
    """
    Base class for SQL data type mapping to Python types.
    
    Provides a foundation for mapping SQL data types to their corresponding
    Python types and generating SQL type names for DDL statements.
    """

    def __init__(self, name: str, python_type: Type):
        """
        Initializes a SQL type mapping to a Python type.
        
        :param name: The SQL type name (e.g., 'INTEGER', 'TEXT').
        :param python_type: The corresponding Python type class.
        """
        self.name = name
        self.python_type = python_type

    def py(self) -> Type:
        """
        Returns the Python type for this SQL type.
        
        :return: The Python type class corresponding to this SQL type.
        """
        return self.python_type

    def sql(self) -> str:
        """
        Returns the SQL type name as a string.
        
        :return: The SQL type name suitable for use in DDL statements.
        """
        return self.name


class Integer(SqlType):
    """Represents an INTEGER SQL type mapping to Python int."""

    def __init__(self):
        """Initializes an INTEGER SQL type."""
        super().__init__("INTEGER", int)


class BigInt(SqlType):
    """Represents a BIGINT SQL type mapping to Python int."""

    def __init__(self):
        """Initializes a BIGINT SQL type."""
        super().__init__("BIGINT", int)


class Numeric(SqlType):
    """Represents a NUMERIC SQL type with precision and scale mapping to Python Decimal."""

    def __init__(self, precision: int = 19, scale: int = 4):
        """
        Initializes a NUMERIC SQL type with precision and scale.
        
        :param precision: Total number of digits (default: 19).
        :param scale: Number of digits after decimal point (default: 4).
        """
        super().__init__(f"NUMERIC({precision}, {scale})", Decimal)


class Boolean(SqlType):
    """Represents a BOOLEAN SQL type mapping to Python bool."""

    def __init__(self):
        """Initializes a BOOLEAN SQL type."""
        super().__init__("BOOLEAN", bool)


class Date(SqlType):
    """Represents a DATE SQL type mapping to Python date."""

    def __init__(self):
        """Initializes a DATE SQL type."""
        super().__init__("DATE", date)


class Text(SqlType):
    """Represents a TEXT SQL type mapping to Python str."""

    def __init__(self):
        """Initializes a TEXT SQL type."""
        super().__init__("TEXT", str)
