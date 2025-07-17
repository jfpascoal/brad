from bread.sql.objects import Table, Column, PrimaryKey, Unique, BigInt, Text, Integer, Numeric, \
    GeneratedIdentityOptions


TEST_TABLES = [
    Table('users').set_columns(
        Column('id', BigInt(), generated_identity=GeneratedIdentityOptions.ALWAYS),
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
    )
]