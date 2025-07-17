from bread.sql.objects import Row, BigInt, Numeric, Date, Text, GeneratedIdentityOptions, \
    Column, PrimaryKey, FkActions, ForeignKey, Unique, Table

BIGINT = BigInt()
DATE = Date()
TEXT = Text()
NUMERIC_19_5 = Numeric(19, 5)

TABLES = [
    Table('exchange_rate').set_columns(
        Column('date', DATE, not_null=True),
        Column('base_currency', TEXT, not_null=True),
        Column('target_currency', TEXT, not_null=True),
        Column('exchange_rate', NUMERIC_19_5, not_null=True)
    ).set_constraint(
        PrimaryKey(['date', 'base_currency', 'target_currency'], "pk_exchange_rate")
    ),

    Table('account_type').set_columns(
        Column('id', BIGINT, generated_identity=GeneratedIdentityOptions.BY_DEFAULT),
        Column('name', TEXT, not_null=True),
        Column('name_pt', TEXT)
    ).set_constraint(
        PrimaryKey(['id'], "pk_account_type")
    ).set_constraint(
        Unique(['name'], "unq_account_type_name")
    ).insert_data(
        Row(id=-1, name='Unknown', name_pt='Desconhecido'),
        Row(id=1, name='Checking', name_pt='Conta corrente'),
        Row(id=2, name='Savings', name_pt='Conta poupança'),
        Row(id=3, name='Credit Card', name_pt='Cartão de crédito'),
        Row(id=4, name='Investment', name_pt='Investimento'),
        Row(id=5, name='Loan', name_pt='Empréstimo'),
        Row(id=6, name='Mortgage', name_pt='Hipoteca'),
        Row(id=7, name='Cash', name_pt='Dinheiro'),
        Row(id=8, name='Other', name_pt='Outros')
    ),

    Table('financial_product_type').set_columns(
        Column('id', BIGINT, generated_identity=GeneratedIdentityOptions.BY_DEFAULT),
        Column('name', TEXT, not_null=True),
        Column('name_pt', TEXT)
    ).set_constraint(
        PrimaryKey(['id'], "pk_financial_product_type")
    ).set_constraint(
        Unique(['name'], "unq_financial_product_type_name")
    ).insert_data(
        Row(id=-1, name='Unknown', name_pt='Desconhecido'),
        Row(id=1, name='Stock', name_pt='Acção'),
        Row(id=2, name='Bond', name_pt='Título'),
        Row(id=3, name='Investment Fund', name_pt='Fundo de investimento'),
        Row(id=4, name='Exchange-Traded Fund (ETF)', name_pt='Fundo de índice (ETF)'),
        Row(id=5, name='Real Estate Investment Trust (REIT)', name_pt='Fundo de investimento imobiliário'),
        Row(id=6, name='Cryptocurrency', name_pt='Criptomoeda')
    ),

    Table('transaction_type').set_columns(
        Column('id', BIGINT, generated_identity=GeneratedIdentityOptions.BY_DEFAULT),
        Column('name', TEXT, not_null=True),
        Column('name_pt', TEXT)
    ).set_constraint(
        PrimaryKey(['id'], "pk_transaction_type")
    ).set_constraint(
        Unique(['name'], "unq_transaction_type_name")
    ).insert_data(
        Row(id=-1, name='Unknown', name_pt='Desconhecido'),
        Row(id=1, name='Purchase', name_pt='Compra'),
        Row(id=2, name='Sale', name_pt='Venda'),
        Row(id=3, name='Dividend', name_pt='Dividendo'),
        Row(id=4, name='Interest', name_pt='Juro'),
        Row(id=5, name='Fee', name_pt='Taxa'),
        Row(id=6, name='Transfer', name_pt='Transferência')
    ),

    Table('holder').set_columns(
        Column('id', BIGINT, generated_identity=GeneratedIdentityOptions.BY_DEFAULT),
        Column('name', TEXT, not_null=True),
        Column('tax_bracket', TEXT)
    ).set_constraint(
        PrimaryKey(['id'], "pk_holder")
    ).set_constraint(
        Unique(['name'], "unq_holder_name")
    ).insert_data(
        Row(id=-1, name='Unknown')
    ),

    Table('provider').set_columns(
        Column('id', BIGINT, generated_identity=GeneratedIdentityOptions.BY_DEFAULT),
        Column('name', TEXT, not_null=True)
    ).set_constraint(
        PrimaryKey(['id'], "pk_provider")
    ).set_constraint(
        Unique(['name'], "unq_provider_name")
    ).insert_data(
        Row(id=-1, name='Unknown')
    ),

    Table('account').set_columns(
        Column('id', BIGINT, generated_identity=GeneratedIdentityOptions.BY_DEFAULT),
        Column('name', TEXT, not_null=True),
        Column('account_type_id', BIGINT, not_null=True, default=-1),
        Column('provider_id', BIGINT, not_null=True, default=-1),
        Column('holder_1_id', BIGINT, not_null=True, default=-1),
        Column('holder_2_id', BIGINT),
        Column('holder_3_id', BIGINT)
    ).set_constraint(
        PrimaryKey(['id'], "pk_account")
    ).set_constraint(
        Unique(['name'], "unq_account_name")
    ).set_constraint(
        ForeignKey(['account_type_id'], 'account_type', ['id'],
                   on_delete=FkActions.SET_DEFAULT, name="fk_account_account_type")
    ).set_constraint(
        ForeignKey(['provider_id'], 'provider', ['id'],
                   name="fk_account_provider")
    ).set_constraint(
        ForeignKey(['holder_1_id'], 'holder', ['id'],
                   name="fk_account_holder_1")
    ).set_constraint(
        ForeignKey(['holder_2_id'], 'holder', ['id'],
                   name="fk_account_holder_2")
    ).set_constraint(
        ForeignKey(['holder_3_id'], 'holder', ['id'],
                   name="fk_account_holder_3")
    ).insert_data(
        Row(id=-1, name='Unknown')
    ),

    Table('financial_product').set_columns(
        Column('id', BIGINT, generated_identity=GeneratedIdentityOptions.BY_DEFAULT),
        Column('name', TEXT, not_null=True),
        Column('financial_product_type_id', BIGINT, not_null=True, default=-1),
        Column('currency', TEXT, not_null=True),
        Column('provider_id', BIGINT, not_null=True, default=-1),
        Column('holder_id', BIGINT, not_null=True, default=-1),
        Column('ticker', TEXT),
        Column('isin', TEXT)
    ).set_constraint(
        PrimaryKey(['id'], "pk_financial_product")
    ).set_constraint(
        Unique(['name'], "unq_financial_product_name")
    ).set_constraint(
        ForeignKey(['financial_product_type_id'], 'financial_product_type',
                   ['id'], on_delete=FkActions.SET_DEFAULT,
                   name="fk_financial_product_financial_product_type")
    ).set_constraint(
        ForeignKey(['provider_id'], 'provider', ['id'],
                   name="fk_financial_product_provider")
    ).set_constraint(
        ForeignKey(['holder_id'], 'holder', ['id'],
                   name="fk_financial_product_holder")
    ).insert_data(
        Row(id=-1, name='Unknown', currency='')
    ),

    Table('account_balance').set_columns(
        Column('date', DATE, not_null=True),
        Column('account_id', BIGINT, not_null=True, default=-1),
        Column('balance', NUMERIC_19_5, not_null=True)
    ).set_constraint(
        PrimaryKey(['date', 'account_id'], "pk_account_balance")
    ).set_constraint(
        ForeignKey(['account_id'], 'account', ['id'],
                   on_delete=FkActions.CASCADE, name="fk_account_balance_account")
    ),

    Table('account_transaction').set_columns(
        Column('id', BIGINT, generated_identity=GeneratedIdentityOptions.ALWAYS),
        Column('date', DATE, not_null=True),
        Column('account_id', BIGINT, not_null=True, default=-1),
        Column('transaction_type_id', BIGINT, not_null=True, default=-1),
        Column('transaction_amount', NUMERIC_19_5, not_null=True),
        Column('description', TEXT)
    ).set_constraint(
        PrimaryKey(['id'], "pk_account_transaction")
    ).set_constraint(
        ForeignKey(['account_id'], 'account', ['id'],
                   on_delete=FkActions.CASCADE, name="fk_account_transaction_account_id")
    ).set_constraint(
        ForeignKey(['transaction_type_id'], 'transaction_type',
                   ['id'], on_delete=FkActions.SET_DEFAULT,
                   name="fk_account_transaction_transaction_type")
    ),

    Table('product_value').set_columns(
        Column('date', DATE, not_null=True),
        Column('financial_product_id', BIGINT, not_null=True, default=-1),
        Column('current_value', NUMERIC_19_5, not_null=True),
        Column('units', NUMERIC_19_5),
        Column('unit_value', NUMERIC_19_5)
    ).set_constraint(
        PrimaryKey(['date', 'financial_product_id'], "pk_product_value")
    ).set_constraint(
        ForeignKey(['financial_product_id'], 'financial_product',
                   ['id'], on_delete=FkActions.CASCADE,
                   name="fk_product_value_financial_product")
    ),

    Table('product_transaction').set_columns(
        Column('id', BIGINT, generated_identity=GeneratedIdentityOptions.ALWAYS),
        Column('date', DATE, not_null=True),
        Column('financial_product_id', BIGINT, not_null=True, default=-1),
        Column('transaction_type_id', BIGINT, not_null=True, default=-1),
        Column('transaction_amount', NUMERIC_19_5, not_null=True),
        Column('units', NUMERIC_19_5),
        Column('unit_value', NUMERIC_19_5)
    ).set_constraint(
        PrimaryKey(['id'], "pk_product_transaction")
    ).set_constraint(
        ForeignKey(['financial_product_id'], 'financial_product',
                   ['id'], on_delete=FkActions.CASCADE,
                   name="fk_product_transaction_financial_product")
    ).set_constraint(
        ForeignKey(['transaction_type_id'], 'transaction_type',
                   ['id'], on_delete=FkActions.SET_DEFAULT,
                   name="fk_product_transaction_transaction_type")
    )
]
