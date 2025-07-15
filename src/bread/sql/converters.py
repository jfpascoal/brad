from datetime import date
from decimal import Decimal


def decimal_adapter(val: Decimal) -> bytes:
    """
    Adapts a Python Decimal object to a bytes string for SQLite storage.
    :param val: The Decimal object to adapt.
    :return: The bytes representation of the decimal's string value.
    """
    return str(val).encode()


def decimal_converter(val: bytes) -> Decimal:
    """
    Converts a bytes string from SQLite back into a Python Decimal object.
    :param val: The bytes value from the database.
    :return: The corresponding Decimal object.
    """
    return Decimal(val.decode())


def date_adapter(val: date) -> str:
    """
    Adapts a Python date object to an ISO 8601 formatted string for SQLite.
    :param val: The date object to adapt.
    :return: The ISO 8601 string representation of the date.
    """
    return val.isoformat()


def date_converter(val: bytes) -> date:
    """
    Converts a bytes string (from an ISO date) from SQLite back into a Python date object.
    :param val: The bytes value from the database.
    :return: The corresponding date object.
    """
    return date.fromisoformat(val.decode())
