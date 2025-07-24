import logging
from typing import Any, Optional, List, Dict, Self

from psycopg import Connection

from brad.sql.types import SqlType, Integer, BigInt, Boolean, Date, Text

logger = logging.getLogger(__name__)


class Row:
    """
    Represents a row of data that can be inserted into a database table.
    
    A Row object can be initialized with a dictionary or keyword arguments,
    providing both attribute-based and dictionary-style access to the data.
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initializes a Row object with data from a dictionary or keyword arguments.
        
        :param data: Optional dictionary containing column-value pairs.
        """
        if data:
            self._dict = data
        else:
            self._dict = kwargs

        self._columns = list(self._dict.keys())
        for k, v in self._dict.items():
            setattr(self, k, v)

    def __getitem__(self, item) -> Any:
        """
        Returns the value for the given column name.

        :param item: The column name to retrieve.
        :return: The value for the specified column, or None if the column doesn't exist.
        :raises AttributeError: If the column does not exist in the Row.
        """
        try:
            value = getattr(self, item)
        except AttributeError:
            logger.error(f"Column '{item}' does not exist in Row.")
            raise
        return value

    def columns(self) -> List[str]:
        """
        Returns a list of column names in the row.
        
        :return: List of column names as strings.
        """
        return self._columns

    def get_dict(self) -> Dict[str, Any]:
        """
        Returns the row data as a dictionary.
        
        :return: Dictionary mapping column names to their values.
        """
        return {c: self[c] for c in self.columns()}


class GeneratedIdOptions:
    """Options for generated identity columns in PostgreSQL."""
    ALWAYS = "ALWAYS"
    BY_DEFAULT = "BY DEFAULT"


class Column:
    """
    Represents a database table column definition with type, constraints, and defaults.
    
    This class encapsulates all the information needed to define a column in a CREATE TABLE
    statement, including data type, nullability, default values, and identity generation.
    """

    def __init__(self, name: str, sql_type: SqlType, generated_identity: Optional[str] = None,
                 not_null: Optional[bool] = None, default: Optional[Any] = None):
        """
        Initializes a Column object for a table schema.
        
        :param name: Column name.
        :param sql_type: SqlType instance for the column.
        :param generated_identity: Specifies if the column is generated with identity and whether it's always or by default.
        :param not_null: If True, column is NOT NULL.
        :param default: Default value for the column.
        :raises TypeError: If generated_identity is used with non-Integer/BigInt types or default type doesn't match sql_type.
        """
        # Validate that generated_identity is only used with Integer or BigInt types
        if generated_identity and not isinstance(sql_type, (Integer, BigInt)):
            raise TypeError(f"Generated identity column {name} must be a BIGINT or INTEGER type."
                            f" {sql_type.__class__.__name__} is not allowed.")
        self.name = name
        self.sql_type = sql_type
        self.generated_identity = generated_identity
        # If generated_identity is not null, not_null is automatically set to True
        self.not_null = not_null if not generated_identity else True
        if default is None:
            self.default = None
        elif not isinstance(default, sql_type.py()):
            raise TypeError(f"Default value {default} is not of type {sql_type.py().__name__}.")
        elif isinstance(sql_type, Text):
            self.default = f"'{default}'"
        elif isinstance(sql_type, Boolean):
            self.default = str(default).upper()
        elif isinstance(sql_type, Date):
            self.default = default.isoformat()
        else:
            self.default = str(default)

    def to_sql(self) -> str:
        """
        Returns the SQL definition string for this column.
        
        :return: Complete SQL column definition suitable for CREATE TABLE statements.
        """
        col_def = f'"{self.name}" {self.sql_type.sql()}'
        if self.generated_identity:
            return col_def + f" GENERATED {self.generated_identity} AS IDENTITY"
        if self.not_null:
            col_def += " NOT NULL"
        if self.default is not None:
            col_def += f" DEFAULT {self.default}"
        return col_def


class Constraint:
    """
    Base class for SQL table constraints.
    
    Provides a foundation for implementing various types of table constraints
    such as primary keys, foreign keys, unique constraints, and check constraints.
    """

    def __init__(self, sql: str, name: Optional[str] = None):
        """
        Initializes a generic SQL constraint.
        
        :param sql: SQL constraint definition.
        :param name: Optional constraint name.
        """
        self.name = name
        self.sql = sql

    def to_sql(self):
        """
        Returns the SQL string for this constraint.
        
        :return: Complete SQL constraint definition.
        """
        if self.name:
            return f'CONSTRAINT "{self.name}" {self.sql}'
        else:
            return f'{self.sql}'


class Check(Constraint):
    """Represents a CHECK constraint that validates column values against a condition."""

    def __init__(self, condition: str, name: Optional[str] = None):
        """
        Initializes a CHECK constraint with a condition.
        
        :param condition: SQL condition expression for the CHECK constraint.
        :param name: Optional constraint name.
        """
        super().__init__(f'CHECK ({condition})', name)


class PrimaryKey(Constraint):
    """Represents a PRIMARY KEY constraint for one or more table columns."""

    def __init__(self, columns: List[str], name: Optional[str] = None):
        """
        Initializes a PRIMARY KEY constraint for given columns.
        
        :param columns: List of column names that form the primary key.
        :param name: Optional constraint name.
        """
        cols_str = ", ".join(f'"{c}"' for c in columns)
        super().__init__(f'PRIMARY KEY ({cols_str})', name)


class FkActions:
    """Constants for foreign key constraint actions on DELETE and UPDATE operations."""
    CASCADE = "CASCADE"
    SET_NULL = "SET NULL"
    SET_DEFAULT = "SET DEFAULT"
    RESTRICT = "RESTRICT"
    NO_ACTION = "NO ACTION"


class ForeignKey(Constraint):
    """Represents a FOREIGN KEY constraint that enforces referential integrity between tables."""

    def __init__(self, columns: List[str], ref_table: str, ref_columns: List[str],
                 on_delete: str = FkActions.RESTRICT, on_update: str = FkActions.CASCADE, name: Optional[str] = None):
        """
        Initializes a FOREIGN KEY constraint.
        
        :param columns: Local columns that reference the foreign table.
        :param ref_table: Referenced table name.
        :param ref_columns: Referenced columns in the foreign table.
        :param on_delete: Action to take when referenced row is deleted (default: RESTRICT).
        :param on_update: Action to take when referenced row is updated (default: CASCADE).
        :param name: Optional constraint name.
        """
        cols_str = ", ".join(f'"{c}"' for c in columns)
        ref_cols_str = ", ".join(f'"{c}"' for c in ref_columns)
        sql = (f'FOREIGN KEY ({cols_str}) REFERENCES "{ref_table}" ({ref_cols_str})'
               f" ON DELETE {on_delete} ON UPDATE {on_update}")
        super().__init__(sql, name)


class Unique(Constraint):
    """Represents a UNIQUE constraint that ensures column value uniqueness."""

    def __init__(self, columns: List[str], name: Optional[str] = None):
        """
        Initializes a UNIQUE constraint for given columns.
        
        :param columns: List of column names that must have unique values.
        :param name: Optional constraint name.
        """
        cols_str = ", ".join(f'"{c}"' for c in columns)
        super().__init__(f'UNIQUE ({cols_str})', name)


class Table:
    """
    Represents a database table schema definition with columns, constraints, and seed data.
    
    This class provides a fluent interface for defining table structure and supports
    generating SQL DDL statements, validating data, and performing database operations.
    """

    def __init__(self, name: str):
        """
        Initializes a Table object representing a database table schema.
        
        :param name: The name of the database table.
        """
        self.name = name
        self.columns: List[Column] = []
        self.constraints: List[Constraint] = []
        self.seed: List[Row] = []

    def set_columns(self, *cols: Column) -> Self:
        """
        Sets the columns for the table. Supports chaining.
        :param cols: Column objects that make up the table.
        :return: The Table instance to allow for method chaining.
        """
        self.columns = list(cols)
        return self

    def set_constraint(self, constraint: Constraint) -> Self:
        """
        Adds a constraint to the table. Supports chaining.
        :param constraint: A Constraint object (e.g., PrimaryKey, ForeignKey).
        :return: The Table instance to allow for method chaining.
        """
        self.constraints.append(constraint)
        return self

    def set_seed(self, *data: Row) -> Self:
        """
        Attaches seed data to the table definition. Supports chaining.
        :param data: Row objects representing the data to be inserted on creation.
        :return: The Table instance to allow for method chaining.
        """
        self.seed = list(data)
        return self

    def get_writable_columns(self) -> List[str]:
        """
        Returns a list of column names that can be written to during INSERT operations.
        
        Excludes columns with GENERATED ALWAYS AS IDENTITY since they cannot be
        explicitly provided values during insertion.
        
        Returns:
            List of column names that accept explicit values during INSERT.
        """
        return [col.name for col in self.columns
                if col.generated_identity in (None, GeneratedIdOptions.BY_DEFAULT)]

    def create(self, connection: Connection) -> Self:
        """
        Creates the table in the database.
        :param connection: A psycopg Connection instance.
        :return: The Table instance to allow for method chaining.
        """
        parts = []
        for col in self.columns:
            parts.append(col.to_sql())
        for constraint in self.constraints:
            parts.append(constraint.to_sql())
        body = ", ".join(parts)
        sql = f'CREATE TABLE IF NOT EXISTS "{self.name}" ({body});'
        logger.info(f"Creating table '{self.name}': {sql}")
        with connection.cursor() as cursor:
            cursor.execute(sql)
        return self

    def drop(self, conn: Connection) -> Self:
        """
        Drops the table from the database.
        :param conn: A psycopg Connection instance.
        :return: The Table instance to allow for method chaining.
        """
        sql = f'DROP TABLE IF EXISTS "{self.name}" CASCADE;'
        logger.info(f"Dropping table '{self.name}': {sql}")
        with conn.cursor() as cursor:
            cursor.execute(sql)
        return self

    def _validate_row(self, row: Row) -> bool:
        """
        Validates a Row object against the table's schema.
        :param row: A Row object to validate.
        :return: True if the row is valid, False otherwise.
        """
        row_columns = row.columns()
        table_cols = {col.name for col in self.columns}
        writable_cols = set(self.get_writable_columns())
        for row_col in row_columns:
            if row_col not in writable_cols:
                if row_col not in table_cols:
                    logger.warning(f"Column '{row_col}' is not part of the table '{self.name}'."
                                   f" Row will not be inserted: {row.get_dict()}")
                    return False
                else:
                    logger.warning(f"Column '{row_col}' was provided, but is autogenerated in table '{self.name}'."
                                   f" Row will not be inserted: {row.get_dict()}")
                    return False

        for col in self.columns:
            column_name = col.name
            if column_name not in row_columns:
                if (col.generated_identity in (GeneratedIdOptions.ALWAYS, GeneratedIdOptions.BY_DEFAULT)
                        or col.default is not None):
                    continue
                if col.not_null:
                    logger.warning(f"Column '{column_name}' is required in table '{self.name}'"
                                   f" but was not provided. Row will not be inserted: {row.get_dict()}")
                    return False
                continue

            value = row[column_name]
            if col.not_null and value is None:
                logger.warning(f"Column '{column_name}' in table '{self.name}' is NOT NULL"
                               f" but was provided as None. Row will not be inserted: {row.get_dict()}")
                return False
            if not isinstance(value, col.sql_type.py()):
                logger.warning(
                    f"Column '{column_name}' in table '{self.name}' expects type {col.sql_type.py().__name__}"
                    f" but received {type(value).__name__}. Row will not be inserted: {row.get_dict()}")
                return False
        return True

    def insert(self, conn: Connection, rows: List[Row]) -> Self:
        """
        Inserts rows into the table.
        :param conn: A psycopg Connection instance.
        :param rows: A list of Row objects to insert.
        :return: The Table instance to allow for method chaining.
        """
        if not rows:
            logger.info(f"No rows to insert into table '{self.name}'.")
            return self

        columns = rows[0].columns()
        col_str = ', '.join(f'"{col}"' for col in columns)
        placeholders = ', '.join(['%s'] * len(columns))
        vals = []
        for row in rows:
            if self._validate_row(row):
                vals.append(tuple(row[col] for col in columns))
        if vals:
            sql = f'INSERT INTO "{self.name}" ({col_str}) VALUES ({placeholders});'
            logger.info(f"Inserting rows into table '{self.name}'")
            with conn.cursor() as cursor:
                try:
                    cursor.executemany(sql, vals)
                except Exception as e:
                    logger.error(f"Error inserting rows into table '{self.name}': {e}")
                    raise
        else:
            logger.warning(f"No valid rows to insert into table '{self.name}'.")
        return self
