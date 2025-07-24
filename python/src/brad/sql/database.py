from typing import Any, Optional, List, Tuple

import psycopg

from brad.sql.config import get_connection_string


class DatabaseManager:
    """
    Manages all database operations including connection, schema creation,
    and data manipulation (insert, select, etc.) for PostgreSQL.
    
    This class provides a simple interface for executing SQL queries and managing
    database connections using psycopg for PostgreSQL databases.
    """

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initializes the DatabaseManager.
        
        :param connection_string: PostgreSQL connection string. If None, uses default config.
        """
        self.connection_string = connection_string or get_connection_string()

    def get_connection(self) -> psycopg.Connection:
        """
        Establishes a new PostgreSQL database connection.
        
        :return: A new psycopg Connection object.
        """
        return psycopg.connect(self.connection_string)

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> None:
        """
        Executes a SQL query against the database.
        
        :param query: The SQL query to execute.
        :param params: Optional parameters for the query.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)

    def execute_many(self, query: str, data: List[Tuple[Any, ...]]) -> None:
        """
        Executes a SQL query against the database with multiple sets of parameters.
        
        :param query: The SQL query to execute.
        :param data: A list of tuples containing parameters for each execution.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(query, data)

    def execute_as_transaction(self, queries: List[Tuple[str, Optional[Tuple[Any, ...]]]]) -> None:
        """
        Executes multiple SQL queries as a single transaction.
        
        :param queries: A list of tuples where each tuple contains a SQL query and its parameters.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                for query, params in queries:
                    cursor.execute(query, params)
