import os
import sqlite3
from datetime import date
from decimal import Decimal
from typing import Dict, Any

from bread.sql import DB_PATH
from bread.sql.converters import decimal_adapter, decimal_converter, date_adapter, date_converter
from bread.sql.tables import TABLES
from bread.sql.validation import DataValidator


def _register_custom_types():
    """Registers custom type adapters and converters for SQLite."""
    sqlite3.register_adapter(Decimal, decimal_adapter)
    sqlite3.register_adapter(date, date_adapter)
    sqlite3.register_converter('decimal', decimal_converter)
    sqlite3.register_converter('date', date_converter)


class DatabaseManager:
    """
    Manages all database operations including connection, schema creation,
    and data manipulation (insert, select, etc.).
    """

    def __init__(self, db_path: str = DB_PATH):
        """
        Initializes the DatabaseManager.
        :param db_path: The path to the SQLite database file.
        """
        self.db_path = db_path
        self.validator = DataValidator(TABLES)
        _register_custom_types()

    def get_connection(self, enforce_fk: bool = True) -> sqlite3.Connection:
        """
        Establishes a new database connection and optionally enables foreign keys.
        The 'PRAGMA foreign_keys' command is connection-specific in SQLite.

        :param enforce_fk: If True, enables foreign key constraint checks for this connection.
        :return: A new sqlite3.Connection object.
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        if enforce_fk:
            conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def initialize_schema(self, force: bool = False):
        """
        Creates all tables and seeds them with initial data from the Python schema.

        This process is robust against table definition order. It first creates all
        tables, then inserts all data. If `force` is True, it drops the
        database file before recreating.

        :param force: If True, drops and recreates the DB. For development only.
        """
        if force and os.path.exists(self.db_path):
            os.remove(self.db_path)
        elif os.path.exists(self.db_path):
            return

        try:
            with self.get_connection() as conn:

                # 1. Create all tables first
                for tbl in TABLES:
                    conn.execute(tbl.get_create_statement())

                # 2. Collect all seed data
                seed_data = [statement for tbl in TABLES
                             if (statement := tbl.get_insert_statement()) is not None]

                # 3. Insert all seed data in a single transaction
                if seed_data:
                    for sql, rows in seed_data:
                        conn.executemany(sql, rows)

            print("Database schema and seed data initialized successfully.")
        except (sqlite3.Error, TypeError) as e:
            print(f"An error occurred during schema initialization: {e}")
            # Clean up partially created DB file on error
            if os.path.exists(self.db_path):
                os.remove(self.db_path)

    def insert(self, table_name: str, data: Dict[str, Any], enforce_fk: bool = True) -> bool:
        """
        Validates and inserts a new row into the specified table.

        :param table_name: The name of the table to insert into.
        :param data: A dictionary of column names and values.
        :param enforce_fk: If True, enforces foreign key constraints for this transaction.
        :return: True if insertion was successful, False otherwise.
        """
        if not self.validator.validate(table_name, data):
            # The validator prints detailed error messages.
            return False

        columns = tuple(data.keys())
        values = tuple(data.values())

        # Quoting column names is a safer practice
        column_names_str = ', '.join(f'"{col}"' for col in columns)
        placeholders = ', '.join('?' * len(values))
        sql = f"INSERT INTO \"{table_name}\" ({column_names_str}) VALUES ({placeholders})"

        try:
            with self.get_connection(enforce_fk) as conn:
                conn.execute(sql, values)
            return True
        except sqlite3.Error as e:
            print(f"Database error on insert into '{table_name}': {e}")
            return False
