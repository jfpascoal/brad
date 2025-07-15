from typing import List, Dict, Any

from bread.sql.objects import Table
from bread.sql.tables import TABLES


class DataValidator:
    """Validates incoming data against the defined table schemas."""

    def __init__(self, tables: List[Table] = TABLES):
        """
        Initializes the DataValidator.
        :param tables: A list of Table objects to validate against. Defaults to the global TABLES list.
        """
        self.tables = {tbl.name: tbl for tbl in tables}

    def validate(self, table_name: str, data: Dict[str, Any]) -> bool:
        """
        Validates a dictionary of data against a specific table's schema.

        Performs checks for table existence, valid column names (ensuring no
        autoincrement keys are provided), non-nullable constraints, and
        correct data types.

        :param table_name: The name of the table to validate against.
        :param data: A dictionary where keys are column names and values are the data.
        :return: True if the data is valid, False otherwise.
        """
        tbl = self.tables.get(table_name)
        if not tbl:
            print(f"Invalid table name: '{table_name}'")
            return False

        allowed_cols = {col.name for col in tbl.columns if not col.autoincrement}
        provided_cols = set(data.keys())

        # Check for any provided columns that are not allowed (e.g., autoincrement keys)
        if not provided_cols <= allowed_cols:
            extra_cols = provided_cols - allowed_cols
            print(f"Invalid column name(s) provided: {extra_cols}")
            return False

        # Iterate through the table's schema to check all constraints
        for col in tbl.columns:
            column_name = col.name

            # Skip autoincrement columns as they are handled by the check above
            if col.autoincrement:
                continue

            # Check 1: Presence. A non-nullable column with no set default value must be in the provided data.
            if col.not_null and col.default is not None and column_name not in provided_cols:
                print(f"Required column '{column_name}' was not provided.")
                return False

            # If a column is not provided, skip further checks for it.
            if column_name not in provided_cols:
                continue

            value = data[column_name]

            # Check 2: Nullability. A non-nullable column cannot have a value of None.
            if col.not_null and col.default is None and value is None:
                print(f"Non-nullable column '{column_name}' cannot be None.")
                return False

            # Check 3: Data type. If a value is provided, it must match the expected type.
            if value is not None and not isinstance(value, col.typ):
                print(
                    f"Invalid data type for column '{column_name}': "
                    f"expected {col.typ.__name__}, got {type(value).__name__}")
                return False
        return True
