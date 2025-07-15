from datetime import date
from decimal import Decimal
from typing import Any, Optional, List, Dict, Tuple, Type


class Row:
    def __init__(self, data: Optional[Dict[str, Any]] = None, **kwargs):
        if data:
            self._dict = data
        else:
            self._dict = kwargs

        self._columns = list(self._dict.keys())
        for k, v in self._dict.items():
            setattr(self, k, v)

    def __getitem__(self, item) -> Any:
        return getattr(self, item) if hasattr(self, item) else None

    def columns(self) -> List[str]:
        return self._columns

    def get_dict(self) -> Dict[str, Any]:
        return {c: self[c] for c in self.columns()}


class Column:
    # A mapping from Python types to their corresponding SQL types.
    _DEFAULT_DECIMAL_PRECISION = 19
    _DEFAULT_DECIMAL_SCALE = 4
    _PY_TO_SQL_TYPE: Dict[Type, str] = {
        int: "INTEGER",
        str: "TEXT",
        Decimal: f"DECIMAL({_DEFAULT_DECIMAL_PRECISION}, {_DEFAULT_DECIMAL_SCALE})",
        date: "DATE",
        float: "REAL"
    }

    def __init__(self, name: str, typ: type, row_id: bool = False, autoincrement: bool = False,
                 not_null: Optional[bool] = None, default: Optional[Any] = None):
        if autoincrement and typ != int:
            raise TypeError(f"Autoincrement columns must be of type int. Column '{name}' is of type {typ.__name__}")
        if default is not None and not isinstance(default, typ):
            raise TypeError(f"Column '{name}' is of type {typ.__name__} "
                            f"but provided default value is {type(default).__name__}: {default}")
        self.name = name
        self.typ = typ
        self.row_id = row_id
        self.autoincrement = autoincrement
        self.not_null = not_null
        self.default = default

    def to_sql(self) -> str:
        col_def = f'"{self.name}" {self._PY_TO_SQL_TYPE[self.typ]}'
        if self.row_id:
            col_def += f" PRIMARY KEY"
            if self.autoincrement:
                col_def += " AUTOINCREMENT"
            return col_def
        if self.not_null:
            col_def += " NOT NULL"
        if self.default is not None:
            col_def += f" DEFAULT {self.default}"
        return col_def


class Constraint:
    def __init__(self, name: Optional[str] = None, sql: Optional[str] = None):
        self.name = name
        self.sql = sql

    def to_sql(self):
        return f'CONSTRAINT "{self.name}" {self.sql}'


class PrimaryKey(Constraint):
    def __init__(self, columns: List[str], name: Optional[str] = None):
        super().__init__(name)
        self.columns = columns

    def to_sql(self):
        if self.name:
            pk_def = f'CONSTRAINT "{self.name}" '
        else:
            pk_def = ""
        cols_str = ", ".join(f'"{c}"' for c in self.columns)
        return pk_def + f"PRIMARY KEY ({cols_str})"


class ForeignKey(Constraint):
    CASCADE = "CASCADE"
    SET_NULL = "SET NULL"
    SET_DEFAULT = "SET DEFAULT"
    RESTRICT = "RESTRICT"
    NO_ACTION = "NO ACTION"

    def __init__(self, columns: List[str], ref_table: str, ref_columns: List[str],
                 on_delete: str = NO_ACTION, on_update: str = NO_ACTION, name: Optional[str] = None):
        super().__init__(name)
        self.columns = columns
        self.ref_table = ref_table
        self.ref_columns = ref_columns
        self.on_delete = on_delete
        self.on_update = on_update

    def to_sql(self):
        if self.name:
            fk_def = f'CONSTRAINT "{self.name}" '
        else:
            fk_def = ""
        cols_str = ", ".join(f'"{c}"' for c in self.columns)
        ref_cols_str = ", ".join(f'"{c}"' for c in self.ref_columns)
        return fk_def + (f'FOREIGN KEY ({cols_str}) REFERENCES "{self.ref_table}" ({ref_cols_str})'
                         f" ON DELETE {self.on_delete} ON UPDATE {self.on_update}")


class Unique(Constraint):
    def __init__(self, columns: List[str], name: Optional[str] = None):
        super().__init__(name)
        self.columns = columns

    def to_sql(self):
        if self.name:
            unique_def = f'CONSTRAINT "{self.name}" '
        else:
            unique_def = ""
        cols_str = ", ".join(f'"{c}"' for c in self.columns)
        return unique_def + f"UNIQUE ({cols_str})"


class Table:
    def __init__(self, name: str):
        """
        Initializes a Table object.
        :param name: The name of the database table.
        """
        self.name = name
        self.columns: List[Column] = []
        self.constraints: List[Constraint] = []
        self.data = []

    def set_columns(self, *cols: Column):
        """
        Sets the columns for the table. Supports chaining.
        :param cols: the column objects that make up the table.
        :return: the Table instance to allow for method chaining.
        """
        self.columns = list(cols)
        return self

    def set_constraint(self, constraint: Constraint):
        """
        Adds a constraint to the table. Supports chaining.
        :param constraint: a Constraint object (e.g., PrimaryKey, ForeignKey).
        :return: the Table instance to allow for method chaining.
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
        Generates the 'CREATE TABLE' SQL statement from the table's definition.
        :return: A string containing the full CREATE TABLE statement.
        """
        parts = []
        for col in self.columns:
            parts.append(col.to_sql())
        for constraint in self.constraints:
            parts.append(constraint.to_sql())
        body = ",\n  ".join(parts)
        return f'CREATE TABLE IF NOT EXISTS "{self.name}" (\n  {body}\n);'

    def get_insert_statement(self) -> Optional[Tuple[str, List[Tuple[Any, ...]]]]:
        """
        Generates an SQL INSERT statement and corresponding data for seeding.
        :return: A tuple containing the SQL string and a list of data tuples, or None.
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
        vals_str = ", ".join("?" * len(columns))
        sql = f'INSERT INTO "{self.name}" ({cols_str}) VALUES ({vals_str})'
        return sql, rows
