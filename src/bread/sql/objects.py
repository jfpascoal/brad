from datetime import date
from decimal import Decimal
from typing import Any, Optional, List, Dict, Tuple, Type


class Row:
    def __init__(self, data: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initializes a Row object with data from a dict or keyword arguments.
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
        Returns the value for the given column name, or None if not present.
        """
        return getattr(self, item) if hasattr(self, item) else None

    def columns(self) -> List[str]:
        """
        Returns a list of column names in the row.
        """
        return self._columns

    def get_dict(self) -> Dict[str, Any]:
        """
        Returns the row data as a dictionary.
        """
        return {c: self[c] for c in self.columns()}
    
    
class SqlType:
    def __init__(self, name: str, python_type: Type):
        """
        Initializes a SQL type mapping to a Python type.
        """
        self.name = name
        self.python_type = python_type
    
    def py(self) -> Type:
        """
        Returns the Python type for this SQL type.
        """
        return self.python_type
    
    def sql(self) -> str:
        """
        Returns the SQL type name as a string.
        """
        return self.name


class Integer(SqlType):
    def __init__(self):
        """
        Represents an INTEGER SQL type.
        """
        super().__init__("INTEGER", int)


class BigInt(SqlType):
    def __init__(self):
        """
        Represents a BIGINT SQL type.
        """
        super().__init__("BIGINT", int)


class Numeric(SqlType):
    def __init__(self, precision: int = 19, scale: int = 4):
        """
        Represents a NUMERIC SQL type with precision and scale.
        """
        super().__init__(f"NUMERIC({precision}, {scale})", Decimal)


class Boolean(SqlType):
    def __init__(self):
        """
        Represents a BOOLEAN SQL type.
        """
        super().__init__("BOOLEAN", bool)


class Date(SqlType):
    def __init__(self):
        """
        Represents a DATE SQL type.
        """
        super().__init__("DATE", date)


class Text(SqlType):
    def __init__(self):
        """
        Represents a TEXT SQL type.
        """
        super().__init__("TEXT", str)


class GeneratedIdentityOptions:
    """
    Options for generated identity columns in PostgreSQL.
    """
    ALWAYS = "ALWAYS"
    BY_DEFAULT = "BY DEFAULT"


class Column:
    def __init__(self, name: str, sql_type: SqlType, generated_identity: Optional[str] = None,
                 not_null: Optional[bool] = None, default: Optional[Any] = None):
        """
        Initializes a Column object for a table schema.
        :param name: Column name.
        :param sql_type: SqlType instance for the column.
        :param generated_identity: Specifies if the column is generated with identity and whether it's
            always or by default.
        :param not_null: If True, column is NOT NULL.
        :param default: Default value for the column.
        """
        # Validate that generated_identity is only used with Integer or BigInt types
        if generated_identity and not isinstance(sql_type, (Integer, BigInt)):
            raise TypeError("Generated identity can only be used with Integer or BigInt types.")
        self.name = name
        self.sql_type = sql_type
        self.generated_identity = generated_identity
        # If generated_identity is not null, not_null is automatically set to True
        self.not_null = not_null if not generated_identity else True
        if default is None:
            self.default = None
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
        """
        if self.name:
            return f'CONSTRAINT "{self.name}" {self.sql}'
        else:
            return f'{self.sql}'


class Check(Constraint):
    def __init__(self, condition: str, name: Optional[str] = None):
        """
        Initializes a CHECK constraint with a condition.
        """
        super().__init__(f'CHECK ({condition})', name)


class PrimaryKey(Constraint):
    def __init__(self, columns: List[str], name: Optional[str] = None):
        """
        Initializes a PRIMARY KEY constraint for given columns.
        """
        cols_str = ", ".join(f'"{c}"' for c in columns)
        super().__init__(f'PRIMARY KEY ({cols_str})', name)


class FkActions:
    """Defines actions for foreign key constraints."""
    CASCADE = "CASCADE"
    SET_NULL = "SET NULL"
    SET_DEFAULT = "SET DEFAULT"
    RESTRICT = "RESTRICT"
    NO_ACTION = "NO ACTION"


class ForeignKey(Constraint):
    """
    Represents a FOREIGN KEY constraint.
    """
    def __init__(self, columns: List[str], ref_table: str, ref_columns: List[str],
                 on_delete: str = FkActions.RESTRICT, on_update: str = FkActions.CASCADE, name: Optional[str] = None):
        """
        Initializes a FOREIGN KEY constraint.
        :param columns: Local columns.
        :param ref_table: Referenced table name.
        :param ref_columns: Referenced columns.
        :param on_delete: ON DELETE action.
        :param on_update: ON UPDATE action.
        :param name: Optional constraint name.
        """
        cols_str = ", ".join(f'"{c}"' for c in columns)
        ref_cols_str = ", ".join(f'"{c}"' for c in ref_columns)
        sql = (f'FOREIGN KEY ({cols_str}) REFERENCES "{ref_table}" ({ref_cols_str})'
               f" ON DELETE {on_delete} ON UPDATE {on_update}")
        super().__init__(sql, name)


class Unique(Constraint):
    def __init__(self, columns: List[str], name: Optional[str] = None):
        """
        Initializes a UNIQUE constraint for given columns.
        """
        cols_str = ", ".join(f'"{c}"' for c in columns)
        super().__init__(f'UNIQUE ({cols_str})', name)


class Table:
    def __init__(self, name: str):
        """
        Initializes a Table object representing a database table schema.
        :param name: The name of the database table.
        """
        self.name = name
        self.columns: List[Column] = []
        self.constraints: List[Constraint] = []
        self.data = []

    def set_columns(self, *cols: Column):
        """
        Sets the columns for the table. Supports chaining.
        :param cols: Column objects that make up the table.
        :return: The Table instance to allow for method chaining.
        """
        self.columns = list(cols)
        return self

    def set_constraint(self, constraint: Constraint):
        """
        Adds a constraint to the table. Supports chaining.
        :param constraint: A Constraint object (e.g., PrimaryKey, ForeignKey).
        :return: The Table instance to allow for method chaining.
        """
        self.constraints.append(constraint)
        return self

    def insert_data(self, *data: Row):
        """
        Attaches seed data to the table definition. Supports chaining.
        :param data: Row objects representing the data to be inserted on creation.
        :return: The Table instance to allow for method chaining.
        """
        self.data = data
        return self

    def get_create_statement(self) -> str:
        """
        Generates the CREATE TABLE SQL statement for this table.
        :return: A string containing the full CREATE TABLE statement.
        """
        parts = []
        for col in self.columns:
            parts.append(col.to_sql())
        for constraint in self.constraints:
            parts.append(constraint.to_sql())
        body = ", ".join(parts)
        return f'CREATE TABLE IF NOT EXISTS "{self.name}" ({body});'

    def get_insert_statement(self) -> Optional[Tuple[str, List[Tuple[Any, ...]]]]:
        """
        Generates an SQL INSERT statement and corresponding data for seeding.
        :return: A tuple containing the SQL string and a list of data tuples, or None if no data.
        """
        if not self.data:
            return None
        # Filter table columns to only include those present in the data
        data_columns = set(col for row in self.data for col in row.columns())
        columns = [c for c in self.columns if c.name in data_columns]
        rows = []
        for row in self.data:
            # Ensure the order of values matches the order of columns_to_insert
            values = [row[col.name] for col in columns]
            rows.append(tuple(values))

        cols_str = ", ".join(f'"{c.name}"' for c in columns)
        vals_str = ", ".join(('%s',) * len(columns))
        sql = f'INSERT INTO "{self.name}" ({cols_str}) VALUES ({vals_str})'
        return sql, rows
