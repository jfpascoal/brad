from datetime import date
from decimal import Decimal

from bread.sql.objects import Row, Column, PrimaryKey, ForeignKey, Unique, Table

TABLES = [
    Table('exchange_rate').set_columns(
        Column('date', date, not_null=True),
        Column('base_currency', str, not_null=True),
        Column('target_currency', str, not_null=True),
        Column('exchange_rate', Decimal, not_null=True)
    ).set_constraint(
        PrimaryKey(['date', 'base_currency', 'target_currency'])
    ),

    Table('account_type').set_columns(
        Column('id', int, row_id=True),
        Column('name', str, not_null=True)
    ).set_constraint(
        Unique(['name'])
    ).insert_data(
        Row(id=-1, name='Unknown'),
        Row(id=1, name='Checking'),
        Row(id=2, name='Savings'),
        Row(id=3, name='Credit Card'),
        Row(id=4, name='Investment'),
        Row(id=5, name='Loan'),
        Row(id=6, name='Mortgage'),
        Row(id=7, name='Cash'),
        Row(id=8, name='Other')
    ),

    Table('financial_product_type').set_columns(
        Column('id', int, row_id=True),
        Column('name', str, not_null=True)
    ).set_constraint(
        Unique(['name'])
    ).insert_data(
        Row(id=-1, name='Unknown'),
        Row(id=1, name='Stock'),
        Row(id=2, name='Bond'),
        Row(id=3, name='Investment Fund'),
        Row(id=4, name='Exchange-Traded Fund (ETF)'),
        Row(id=5, name='Real Estate Investment Trust (REIT)'),
        Row(id=6, name='Cryptocurrency')
    ),

    Table('transaction_type').set_columns(
        Column('id', int, row_id=True),
        Column('name', str, not_null=True)
    ).set_constraint(
        Unique(['name'])
    ).insert_data(
        Row(id=-1, name='Unknown'),
        Row(id=1, name='Purchase'),
        Row(id=2, name='Sale'),
        Row(id=3, name='Dividend'),
        Row(id=4, name='Interest'),
        Row(id=5, name='Fee'),
        Row(id=6, name='Transfer')
    ),

    Table('holder').set_columns(
        Column('id', int, row_id=True),
        Column('name', str, not_null=True),
        Column('tax_bracket', str)
    ).set_constraint(
        Unique(['name'])
    ).insert_data(
        Row(id=-1, name='Unknown')
    ),

    Table('provider').set_columns(
        Column('id', int, row_id=True),
        Column('name', str, not_null=True)
    ).set_constraint(
        Unique(['name'])
    ).insert_data(
        Row(id=-1, name='Unknown')
    ),

    Table('account').set_columns(
        Column('id', int, row_id=True),
        Column('name', str, not_null=True),
        Column('account_type_id', int, not_null=True, default=-1),
        Column('provider_id', int, not_null=True, default=-1),
        Column('holder_1_id', int, not_null=True, default=-1),
        Column('holder_2_id', int),
        Column('holder_3_id', int)
    ).set_constraint(
        ForeignKey(['account_type_id'], 'account_type', ['id'])
    ).set_constraint(
        ForeignKey(['provider_id'], 'provider', ['id'])
    ).set_constraint(
        ForeignKey(['holder_1_id'], 'holder', ['id'])
    ).set_constraint(
        ForeignKey(['holder_2_id'], 'holder', ['id'])
    ).set_constraint(
        ForeignKey(['holder_3_id'], 'holder', ['id'])
    ).set_constraint(
        Unique(['name'])
    ).insert_data(
        Row(id=-1, name='Unknown')
    ),

    Table('financial_product').set_columns(
        Column('id', int, row_id=True),
        Column('name', str, not_null=True),
        Column('financial_product_type_id', int, not_null=True, default=-1),
        Column('currency', str, not_null=True),
        Column('provider_id', int, not_null=True, default=-1),
        Column('holder_id', int, not_null=True, default=-1),
        Column('ticker', str),
        Column('isin', str)
    ).set_constraint(
        ForeignKey(['financial_product_type_id'], 'financial_product_type', ['id'])
    ).set_constraint(
        ForeignKey(['provider_id'], 'provider', ['id'])
    ).set_constraint(
        ForeignKey(['holder_id'], 'holder', ['id'])
    ).set_constraint(
        Unique(['name'])
    ).insert_data(
        Row(id=-1, name='Unknown', currency='')
    ),

    Table('account_balance').set_columns(
        Column('date', date, not_null=True),
        Column('account_id', int, not_null=True, default=-1),
        Column('balance', Decimal, not_null=True)
    ).set_constraint(
        PrimaryKey(['date', 'account_id'])
    ).set_constraint(
        ForeignKey(['account_id'], 'account', ['id'])
    ),

    Table('account_transaction').set_columns(
        Column('id', int, row_id=True),
        Column('date', date, not_null=True),
        Column('account_id', int, not_null=True, default=-1),
        Column('transaction_type_id', int, not_null=True, default=-1),
        Column('transaction_amount', Decimal, not_null=True),
        Column('description', str)
    ).set_constraint(
        ForeignKey(['account_id'], 'account', ['id'])
    ).set_constraint(
        ForeignKey(['transaction_type_id'], 'transaction_type', ['id'])
    ),

    Table('product_value').set_columns(
        Column('date', date, not_null=True),
        Column('financial_product_id', int, not_null=True, default=-1),
        Column('current_value', Decimal, not_null=True),
        Column('units', Decimal),
        Column('unit_value', Decimal)
    ).set_constraint(
        PrimaryKey(['date', 'financial_product_id'])
    ).set_constraint(
        ForeignKey(['financial_product_id'], 'financial_product', ['id'])
    ),

    Table('product_transaction').set_columns(
        Column('id', int, row_id=True),
        Column('date', date, not_null=True),
        Column('financial_product_id', int, not_null=True, default=-1),
        Column('transaction_type_id', int, not_null=True, default=-1),
        Column('transaction_amount', Decimal, not_null=True),
        Column('units', Decimal),
        Column('unit_value', Decimal)
    ).set_constraint(
        ForeignKey(['financial_product_id'], 'financial_product', ['id'])
    ).set_constraint(
        ForeignKey(['transaction_type_id'], 'transaction_type', ['id'])
    )
]
