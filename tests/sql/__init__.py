from decimal import Decimal
from bread.sql.objects import Table, Column, PrimaryKey, Unique

# A standardized set of table definitions used across different test files.
# This ensures consistency and avoids code duplication.
TEST_TABLES = [
    Table('users').set_columns(
        Column('id', int, row_id=True, autoincrement=True),
        Column('name', str, not_null=True),
        Column('age', int)  # Nullable column
    ).set_constraint(
        Unique(['name'])
    ),
    Table('products').set_columns(
        Column('sku', str, not_null=True),
        Column('name', str, not_null=True),
        Column('price', Decimal, not_null=True)
    ).set_constraint(
        PrimaryKey(['sku'])
    )
]