import logging
from typing import Any, Optional, List, Dict, Self, Type, Union
from functools import lru_cache

from psycopg import Connection
from pydantic import BaseModel, Field, ValidationError, ConfigDict, create_model, field_validator, model_validator

from .types import SqlType, Integer, BigInt, Boolean, Date, Text

logger = logging.getLogger(__name__)


class Row(BaseModel):
    """
    Represents a row of data that can be inserted into a database table.
    
    Uses Pydantic BaseModel for automatic validation, serialization,
    and better error handling. Supports both dictionary and keyword initialization.
    """

    model_config = ConfigDict(
        extra='allow',  # Allow dynamic fields for database rows
        arbitrary_types_allowed=True,
        validate_assignment=True
    )

    def __init__(self, data: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initializes a Row object with validation.
        
        :param data: Optional dictionary containing column-value pairs.
        :param kwargs: Column-value pairs as keyword arguments.
        """
        if data:
            super().__init__(**data)
        else:
            super().__init__(**kwargs)

    def __getitem__(self, item) -> Any:
        """
        Returns the value for the given column name.

        :param item: The column name to retrieve.
        :return: The value for the specified column.
        :raises AttributeError: If the column does not exist in the Row.
        """
        try:
            return getattr(self, item)
        except AttributeError:
            logger.error(f"Column '{item}' does not exist in Row.")
            raise  # Re-raise the original AttributeError

    def columns(self) -> List[str]:
        """
        Returns a list of column names in the row.
        
        :return: List of column names as strings.
        """
        return list(self.model_dump().keys())

    def get_dict(self) -> Dict[str, Any]:
        """
        Returns the row data as a dictionary.
        
        :return: Dictionary mapping column names to their values.
        """
        return self.model_dump()


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
        self.columns = columns  # Store columns for validation
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
        self.columns = columns  # Store columns for validation
        cols_str = ", ".join(f'"{c}"' for c in columns)
        super().__init__(f'UNIQUE ({cols_str})', name)


class Schema:
    """Represents a database schema, which is a collection of tables and other database objects."""
    def __init__(self, name: str):
        """
        Initializes a Schema object representing a database schema.
        
        :param name: The name of the database schema.
        """
        self.name = name
        
    def drop(self, conn: Connection) -> Self:
        """
        Drops the schema from the database.
        :param conn: A psycopg Connection instance.
        :return: The Schema instance to allow for method chaining.
        """
        sql = f'DROP SCHEMA IF EXISTS "{self.name}" CASCADE;'
        logger.info(f"Dropping schema '{self.name}': {sql}")
        with conn.cursor() as cursor:
            cursor.execute(sql)
        return self
    
    def create(self, conn: Connection) -> Self:
        """
        Creates the schema in the database.
        :param conn: A psycopg Connection instance.
        :return: The Schema instance to allow for method chaining.
        """
        sql = f'CREATE SCHEMA IF NOT EXISTS "{self.name}";'
        logger.info(f"Creating schema '{self.name}': {sql}")
        with conn.cursor() as cursor:
            cursor.execute(sql)
        return self


class TableRowValidator:
    """
    Factory class for creating and caching Pydantic models for table row validation.
    
    This class dynamically generates table-specific Pydantic models based on table schema
    definitions, providing robust validation with proper error messages and type safety.
    """
    
    _model_cache: Dict[str, Type[BaseModel]] = {}
    
    @classmethod
    def create_table_model(cls, table: 'Table') -> Type[BaseModel]:
        """
        Create a Pydantic model for validating rows against a table schema.
        
        :param table: Table instance to create validation model for
        :return: Pydantic model class for validation
        """
        # Check cache first
        cache_key = f"{table.qualified_name}_{hash(str(table.columns))}"
        if cache_key in cls._model_cache:
            return cls._model_cache[cache_key]
        
        # Build field definitions
        fields = {}
        validators = {}
        
        # Get writable columns (exclude generated identity columns)
        writable_columns = set(table.get_writable_columns())
        
        for col in table.columns:
            # Skip non-writable columns
            if col.name not in writable_columns:
                continue
                
            field_type = col.sql_type.py()
            
            # Handle optional/nullable fields
            if not col.not_null:
                field_type = Optional[field_type]
            
            # Set up field constraints
            field_kwargs = {}
            
            # Handle field requirements:
            # - Columns with defaults are always optional
            # - Generated identity BY_DEFAULT columns are optional (can be provided or auto-generated)
            # - NOT NULL columns without defaults are required
            # - Nullable columns are optional
            if col.default is not None:
                # Column has a default value
                field_kwargs['default'] = col.default
            elif col.generated_identity == GeneratedIdOptions.BY_DEFAULT:
                # BY_DEFAULT allows explicit values but makes the field optional
                field_kwargs['default'] = None
            elif col.not_null:
                # Required field with no default
                field_kwargs['default'] = ...
            else:
                # Nullable field with no default
                field_kwargs['default'] = None
            
            # Add description for better error messages
            field_kwargs['description'] = f"Column {col.name} of type {col.sql_type.__class__.__name__}"
            
            fields[col.name] = (field_type, Field(**field_kwargs))
        
        # Create the dynamic model
        model_name = f"{table.name.title()}RowModel"
        
        # Create model with extra='forbid' to prevent unknown columns
        DynamicModel = create_model(
            model_name,
            __config__=ConfigDict(
                extra='forbid',
                arbitrary_types_allowed=True,
                str_strip_whitespace=True
            ),
            **fields
        )
        
        # Add custom validation methods to the model
        cls._add_table_validators(DynamicModel, table)
        
        # Cache the model
        cls._model_cache[cache_key] = DynamicModel
        
        return DynamicModel
    
    @classmethod
    def _add_table_validators(cls, model_class: Type[BaseModel], table: 'Table') -> None:
        """
        Add table-specific validators to the dynamic model.
        
        :param model_class: The dynamically created model class
        :param table: Table instance for validation rules
        """
        # Add field validators for specific constraints
        for col in table.columns:
            if col.not_null:
                # Create a validator for not-null constraints
                validator_name = f"validate_{col.name}_not_null"
                validator_func = cls._create_not_null_validator(col.name)
                setattr(model_class, validator_name, validator_func)
        
        # Add model validators for cross-field validation based on table constraints
        cls._add_constraint_validators(model_class, table)
    
    @staticmethod
    def _create_not_null_validator(column_name: str):
        """Create a field validator for not-null constraints."""
        @field_validator(column_name)
        @classmethod
        def validate_not_null(cls, v, info):
            if v is None:
                raise ValueError(f"Column '{column_name}' cannot be None")
            return v
        return validate_not_null
    
    @classmethod
    def _add_constraint_validators(cls, model_class: Type[BaseModel], table: 'Table') -> None:
        """
        Add model validators for table constraints that require cross-field validation.
        
        :param model_class: The dynamically created model class
        :param table: Table instance for constraint validation rules
        """
        # Check if there are constraints that need cross-field validation
        constraint_validators = []
        
        for constraint in table.constraints:
            if hasattr(constraint, 'columns') and len(constraint.columns) > 1:
                # Multi-column constraints need model-level validation
                if constraint.__class__.__name__ == 'PrimaryKey':
                    constraint_validators.append(
                        cls._create_primary_key_validator(constraint.columns)
                    )
                elif constraint.__class__.__name__ == 'Unique':
                    constraint_validators.append(
                        cls._create_unique_constraint_validator(constraint.columns)
                    )
        
        # Add composite model validator if we have any constraint validators
        if constraint_validators:
            composite_validator = cls._create_composite_constraint_validator(constraint_validators, table.name)
            setattr(model_class, 'validate_table_constraints', composite_validator)
    
    @staticmethod
    def _create_primary_key_validator(pk_columns: List[str]):
        """Create a validator function for primary key constraints."""
        def validate_pk(values: Dict[str, Any]) -> str:
            pk_values = [values.get(col) for col in pk_columns]
            if any(v is None for v in pk_values):
                missing_cols = [col for col, val in zip(pk_columns, pk_values) if val is None]
                return f"Primary key columns cannot be None: {missing_cols}"
            return None
        return validate_pk
    
    @staticmethod
    def _create_unique_constraint_validator(unique_columns: List[str]):
        """Create a validator function for unique constraints."""
        def validate_unique(values: Dict[str, Any]) -> str:
            # Note: This validates the structure but cannot check uniqueness against database
            # Actual uniqueness validation would require database access
            unique_values = [values.get(col) for col in unique_columns]
            if all(v is None for v in unique_values):
                return f"At least one value in unique constraint columns must be non-null: {unique_columns}"
            return None
        return validate_unique
    
    @staticmethod
    def _create_composite_constraint_validator(validators: List, table_name: str):
        """Create a composite model validator that runs all constraint validators."""
        @model_validator(mode='after')
        @classmethod
        def validate_constraints(cls, values):
            errors = []
            
            # Convert model instance to dict for validation functions
            if hasattr(values, 'model_dump'):
                values_dict = values.model_dump()
            else:
                values_dict = dict(values)  # Fallback for dict-like objects
            
            # Run all constraint validators
            for validator_func in validators:
                error = validator_func(values_dict)
                if error:
                    errors.append(error)
            
            if errors:
                constraint_errors = '; '.join(errors)
                raise ValueError(f"Table constraint violations in '{table_name}': {constraint_errors}")
            
            return values
        
        return validate_constraints
    
    @classmethod
    def clear_cache(cls):
        """Clear the model cache. Useful for testing or schema changes."""
        cls._model_cache.clear()


class Table:
    """
    Represents a database table schema definition with columns, constraints, and seed data.
    
    This class provides a fluent interface for defining table structure and supports
    generating SQL DDL statements, validating data, and performing database operations.
    """

    def __init__(self, name: str, db_schema: Schema = None):
        """
        Initializes a Table object representing a database table schema.
        
        :param name: The name of the database table.
        :param db_schema: The schema of the database table.
        """
        self.name = name
        self.db_schema = db_schema
        self.columns: List[Column] = []
        self.constraints: List[Constraint] = []
        self.seed: List[Row] = []
        
    @property
    def qualified_name(self):
        return f'"{self.db_schema.name}"."{self.name}"' if self.db_schema else f'"{self.name}"'

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
        sql = f'CREATE TABLE IF NOT EXISTS {self.qualified_name} ({body});'
        logger.info(f"Creating table {self.qualified_name}: {sql}")
        with connection.cursor() as cursor:
            cursor.execute(sql)
        return self

    def drop(self, conn: Connection) -> Self:
        """
        Drops the table from the database.
        :param conn: A psycopg Connection instance.
        :return: The Table instance to allow for method chaining.
        """
        sql = f'DROP TABLE IF EXISTS {self.qualified_name} CASCADE;'
        logger.info(f"Dropping table {self.qualified_name}: {sql}")
        with conn.cursor() as cursor:
            cursor.execute(sql)
        return self

    def _validate_row(self, row: Row) -> bool:
        """
        Validates a Row object against the table's schema using Pydantic dynamic models.
        :param row: A Row object to validate.
        :return: True if the row is valid, False otherwise.
        """
        try:
            # Create or get cached Pydantic model for this table
            table_model = TableRowValidator.create_table_model(self)
            
            # Validate the row data using the Pydantic model
            validated_data = table_model(**row.get_dict())
            return True
            
        except ValidationError as e:
            # Log detailed validation errors with enhanced formatting
            logger.warning(f"Row validation failed for table {self.qualified_name}")
            logger.warning(f"Problematic row data: {row.get_dict()}")
            
            # Group errors by type for better readability
            field_errors = []
            value_errors = []
            missing_errors = []
            
            for error in e.errors():
                error_type = error.get('type', 'unknown')
                field = error.get('loc', ['unknown'])[0] if error.get('loc') else 'unknown'
                msg = error.get('msg', 'unknown error')
                input_value = error.get('input', 'N/A')
                
                if error_type == 'missing':
                    missing_errors.append(f"  ❌ Missing required field '{field}': {msg}")
                elif error_type in ('type_error', 'value_error'):
                    value_errors.append(f"  ❌ Field '{field}' (value: {input_value}): {msg}")
                else:
                    field_errors.append(f"  ❌ Field '{field}': {msg} (type: {error_type}, input: {input_value})")
            
            # Log errors in organized groups
            if missing_errors:
                logger.warning("Missing required fields:")
                for error in missing_errors:
                    logger.warning(error)
            
            if value_errors:
                logger.warning("Value validation errors:")
                for error in value_errors:
                    logger.warning(error)
            
            if field_errors:
                logger.warning("Field validation errors:")
                for error in field_errors:
                    logger.warning(error)
            
            logger.warning("Row will not be inserted due to validation failures.")
            return False
        except Exception as e:
            # Log any unexpected errors during validation
            logger.error(f"Unexpected error during row validation for table {self.qualified_name}: {e}")
            logger.warning(f"Row will not be inserted: {row.get_dict()}")
            return False

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
            sql = f'INSERT INTO {self.qualified_name} ({col_str}) VALUES ({placeholders});'
            logger.info(f"Inserting rows into table {self.qualified_name}")
            with conn.cursor() as cursor:
                try:
                    cursor.executemany(sql, vals)
                except Exception as e:
                    logger.error(f"Error inserting rows into table {self.qualified_name}: {e}")
                    raise
        else:
            logger.warning(f"No valid rows to insert into table {self.qualified_name}.")
        return self
