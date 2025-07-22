from typing import Dict, Any, Optional

import psycopg2

from brad.sql.config import get_connection_string
from brad.sql.tables import TABLES
from brad.sql.validation import DataValidator


class DatabaseManager:
    """
    Manages all database operations including connection, schema creation,
    and data manipulation (insert, select, etc.) for PostgreSQL.
    """

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initializes the DatabaseManager.
        :param connection_string: PostgreSQL connection string. If None, uses default config.
        """
        self.connection_string = connection_string or get_connection_string()
        self.validator = DataValidator(TABLES)

    def get_connection(self) -> psycopg2.extensions.connection:
        """
        Establishes a new PostgreSQL database connection.

        :return: A new psycopg2 Connection object.
        """
        return psycopg2.connect(self.connection_string)

    def initialize_schema(self, force: bool = False, seed: bool = True) -> bool:
        """
        Creates all tables and optionally seeds them with initial data from the Python schema.

        This process is robust against table definition order. It first creates all
        tables, then inserts all data if seeding is enabled. If `force` is True,
        it drops all tables before recreating them.

        :param force: If True, drops and recreates all tables.
        :param seed: If True, inserts seed data after creating tables. Defaults to True.
        :return: True if schema initialization was successful, False otherwise.
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:

                    if force:
                        # Drop all tables in reverse order to handle foreign key dependencies
                        for tbl in reversed(TABLES):
                            cursor.execute(f'DROP TABLE IF EXISTS "{tbl.name}" CASCADE;')

                    # 1. Create all tables first
                    for tbl in TABLES:
                        cursor.execute(tbl.get_create_statement())

                    # 2. Collect and insert seed data if seeding is enabled
                    if seed:
                        seed_data = [statement for tbl in TABLES
                                     if (statement := tbl.get_insert_statement()) is not None]

                        # 3. Insert all seed data in a single transaction
                        if seed_data:
                            for sql, rows in seed_data:
                                cursor.executemany(sql, rows)

            print("Database schema initialized successfully.")
            if seed:
                print("Seed data inserted successfully.")
        except (psycopg2.Error, TypeError) as e:
            print(f"An error occurred during schema initialization: {e}")
            return False
        return True

    def insert(self, table_name: str, data: Dict[str, Any]) -> bool:
        """
        Validates and inserts a new row into the specified table.

        :param table_name: The name of the table to insert into.
        :param data: A dictionary of column names and values.
        :return: True if insertion was successful, False otherwise.
        """
        if not self.validator.validate(table_name, data):
            # The validator prints detailed error messages.
            return False

        columns = tuple(data.keys())
        values = tuple(data.values())

        # Using PostgreSQL-style parameter placeholders
        column_names_str = ', '.join(f'"{col}"' for col in columns)
        placeholders = ', '.join(['%s'] * len(values))
        sql = f"INSERT INTO \"{table_name}\" ({column_names_str}) VALUES ({placeholders})"

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, values)
            return True
        except psycopg2.Error as e:
            print(f"Database error on insert into '{table_name}': {e}")
            return False
