from brad.sql.objects import Table, Column, PrimaryKey, Unique, GeneratedIdOptions
from brad.sql.types import Integer, BigInt, Numeric, Text

TEST_TABLES = [
    Table('users').set_columns(
        Column('id', BigInt(), generated_identity=GeneratedIdOptions.ALWAYS),
        Column('name', Text(), not_null=True),
        Column('age', Integer())
    ).set_constraint(
        Unique(['name'])
    ),
    Table('products').set_columns(
        Column('sku', Text(), not_null=True),
        Column('name', Text(), not_null=True),
        Column('price', Numeric(19, 2), not_null=True)
    ).set_constraint(
        PrimaryKey(['sku'])
    ),
    Table('product_types').set_columns(
        Column('id', BigInt(), generated_identity=GeneratedIdOptions.BY_DEFAULT),
        Column('type', Text(), not_null=True),
    )
]
