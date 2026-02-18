import logging
from typing import List

from brad.sql.database import DatabaseManager
from brad.sql.objects import Row, GeneratedIdOptions, Column, PrimaryKey, Unique, Schema, Table
from brad.sql.types import BigInt, Numeric, Boolean, Date, Text

logger = logging.getLogger(__name__)

# Table names
ACCOUNT_TYPES = "account_types"
FINANCIAL_PRODUCT_TYPES = "financial_product_types"
TRANSACTION_TYPES = "transaction_types"
EXCHANGE_RATES = "exchange_rates"
PROVIDERS = "providers"
HOLDERS = "holders"
ACCOUNTS = "accounts"
ACCOUNT_BALANCES = "account_balances"
ACCOUNT_TRANSACTIONS = "account_transactions"
FINANCIAL_PRODUCTS = "financial_products"
PRODUCT_VALUES = "product_values"
PRODUCT_TRANSACTIONS = "product_transactions"

# Type constants for reusability
BIGINT = BigInt()
DATE = Date()
TEXT = Text()
NUMERIC_19_5 = Numeric(19, 5)
BOOLEAN = Boolean()

# Raw schema
REF = Schema('ref')
STG = Schema('stg')

# ============================================================================
# Table definitions
# ============================================================================

account_type_tbl = Table(ACCOUNT_TYPES, db_schema=REF).set_columns(
    Column('id', BIGINT, generated_identity=GeneratedIdOptions.BY_DEFAULT),
    Column('name', TEXT, not_null=True),
    Column('name_pt', TEXT)
).set_constraint(
    PrimaryKey(['id'], "pk_account_type")
).set_constraint(
    Unique(['name'], "unq_account_type_name")
).set_seed(
    Row(id=-1, name='Unknown', name_pt='Desconhecido'),
    Row(id=1, name='Checking', name_pt='Conta corrente'),
    Row(id=2, name='Savings', name_pt='Conta poupança'),
    Row(id=3, name='Credit Card', name_pt='Cartão de crédito'),
    Row(id=4, name='Loan', name_pt='Empréstimo'),
    Row(id=5, name='Mortgage', name_pt='Hipoteca'),
    Row(id=6, name='Cash', name_pt='Dinheiro'),
    Row(id=7, name='Other', name_pt='Outros')
)

financial_product_type_tbl = Table(FINANCIAL_PRODUCT_TYPES, db_schema=REF).set_columns(
    Column('id', BIGINT, generated_identity=GeneratedIdOptions.BY_DEFAULT),
    Column('name', TEXT, not_null=True),
    Column('name_pt', TEXT)
).set_constraint(
    PrimaryKey(['id'], "pk_financial_product_type")
).set_constraint(
    Unique(['name'], "unq_financial_product_type_name")
).set_seed(
    Row(id=-1, name='Unknown', name_pt='Desconhecido'),
    Row(id=1, name='Stock', name_pt='Acção'),
    Row(id=2, name='Bond', name_pt='Título'),
    Row(id=3, name='Investment Fund', name_pt='Fundo de investimento'),
    Row(id=4, name='Pension Investment Fund', name_pt='Fundo de investimento / PPR'),
    Row(id=5, name='Cash ISA', name_pt='ISA dinheiro'),
    Row(id=6, name='Stocks and Shares ISA', name_pt='ISA acções e títulos'),
    Row(id=7, name='Peer-to-Peer Lending', name_pt='Empréstimo P2P'),
    Row(id=8, name='Fractional Shares', name_pt='Acções fraccionadas'),
    Row(id=9, name='Exchange-Traded Fund (ETF)', name_pt='Fundo de índice (ETF)'),
    Row(id=10, name='Real Estate Investment Trust (REIT)', name_pt='Fundo de investimento imobiliário'),
    Row(id=11, name='Cryptocurrency', name_pt='Criptomoeda')
)

transaction_type_tbl = Table(TRANSACTION_TYPES, db_schema=REF).set_columns(
    Column('id', BIGINT, generated_identity=GeneratedIdOptions.BY_DEFAULT),
    Column('name', TEXT, not_null=True),
    Column('name_pt', TEXT)
).set_constraint(
    PrimaryKey(['id'], "pk_transaction_type")
).set_constraint(
    Unique(['name'], "unq_transaction_type_name")
).set_seed(
    Row(id=-1, name='Unknown', name_pt='Desconhecido'),
    Row(id=1, name='Purchase', name_pt='Compra'),
    Row(id=2, name='Sale', name_pt='Venda'),
    Row(id=3, name='Dividend', name_pt='Dividendo'),
    Row(id=4, name='Interest', name_pt='Juro'),
    Row(id=5, name='Fee', name_pt='Taxa'),
    Row(id=6, name='Transfer', name_pt='Transferência'),
    Row(id=7, name='Bonus', name_pt='Bónus'),
)

exchange_rate_tbl = Table(EXCHANGE_RATES, db_schema=REF).set_columns(
    Column('date', DATE, not_null=True),
    Column('base_currency', TEXT, not_null=True),
    Column('target_currency', TEXT, not_null=True),
    Column('exchange_rate', NUMERIC_19_5, not_null=True)
).set_constraint(
    PrimaryKey(['date', 'base_currency', 'target_currency'], "pk_exchange_rate")
)

provider_tbl = Table(PROVIDERS, db_schema=STG).set_columns(
    Column('id', BIGINT, generated_identity=GeneratedIdOptions.BY_DEFAULT),
    Column('name', TEXT, not_null=True),
    Column('country_iso_alpha2', TEXT, not_null=True)
).set_constraint(
    PrimaryKey(['id'], "pk_provider")
).set_constraint(
    Unique(['name'], "unq_provider_name")
)

holder_tbl = Table(HOLDERS, db_schema=STG).set_columns(
    Column('id', BIGINT, generated_identity=GeneratedIdOptions.BY_DEFAULT),
    Column('name', TEXT, not_null=True),
    Column('tax_bracket', TEXT)
).set_constraint(
    PrimaryKey(['id'], "pk_holder")
).set_constraint(
    Unique(['name'], "unq_holder_name")
)

account_tbl = Table(ACCOUNTS, db_schema=STG).set_columns(
    Column('id', BIGINT, generated_identity=GeneratedIdOptions.ALWAYS),
    Column('name', TEXT, not_null=True),
    Column('account_type', TEXT, not_null=True),
    Column('currency', TEXT, not_null=True),
    Column('provider_name', TEXT, not_null=True),
    Column('holder_name_1', TEXT, not_null=True),
    Column('holder_name_2', TEXT),
    Column('holder_name_3', TEXT),
    Column('account_number', TEXT),
    Column('sort_code', TEXT),
    Column('iban', TEXT),
    Column('swift_code', TEXT),
    Column('opening_date', DATE),
    Column('closing_date', DATE),
    Column('is_active', BOOLEAN, not_null=True, default=True)
).set_constraint(
    PrimaryKey(['id'], "pk_account")
).set_constraint(
    Unique(['name'], "unq_account_name")
)

account_balance_tbl = Table(ACCOUNT_BALANCES, db_schema=STG).set_columns(
    Column('date', DATE, not_null=True),
    Column('account_name', TEXT, not_null=True),
    Column('balance', NUMERIC_19_5, not_null=True)
).set_constraint(
    PrimaryKey(['date', 'account_name'], "pk_account_balance")
)

account_transaction_tbl = Table(ACCOUNT_TRANSACTIONS, db_schema=STG).set_columns(
    Column('id', BIGINT, generated_identity=GeneratedIdOptions.ALWAYS),
    Column('date', DATE, not_null=True),
    Column('account_name', TEXT, not_null=True),
    Column('transaction_type', TEXT, not_null=True),
    Column('transaction_amount', NUMERIC_19_5, not_null=True),
    Column('description', TEXT)
).set_constraint(
    PrimaryKey(['id'], "pk_account_transaction")
)

financial_product_tbl = Table(FINANCIAL_PRODUCTS, db_schema=STG).set_columns(
    Column('id', BIGINT, generated_identity=GeneratedIdOptions.ALWAYS),
    Column('name', TEXT, not_null=True),
    Column('financial_product_type', TEXT, not_null=True),
    Column('currency', TEXT, not_null=True),
    Column('linked_account_name', TEXT),
    Column('provider_name', TEXT, not_null=True),
    Column('holder_name', TEXT, not_null=True),
    Column('ticker', TEXT),
    Column('isin', TEXT),
    Column('is_active', BOOLEAN, not_null=True, default=True)
).set_constraint(
    PrimaryKey(['id'], "pk_financial_product")
).set_constraint(
    Unique(['name'], "unq_financial_product_name")
)

product_value_tbl = Table(PRODUCT_VALUES, db_schema=STG).set_columns(
    Column('date', DATE, not_null=True),
    Column('financial_product_name', TEXT, not_null=True),
    Column('current_value', NUMERIC_19_5, not_null=True),
    Column('units', NUMERIC_19_5),
    Column('unit_value', NUMERIC_19_5)
).set_constraint(
    PrimaryKey(['date', 'financial_product_name'], "pk_product_value")
)

product_transaction_tbl = Table(PRODUCT_TRANSACTIONS, db_schema=STG).set_columns(
    Column('id', BIGINT, generated_identity=GeneratedIdOptions.ALWAYS),
    Column('date', DATE, not_null=True),
    Column('financial_product_name', TEXT, not_null=True),
    Column('transaction_type', TEXT, not_null=True),
    Column('transaction_amount', NUMERIC_19_5, not_null=True),
    Column('transaction_amount_eur', NUMERIC_19_5),
    Column('units', NUMERIC_19_5),
    Column('unit_value', NUMERIC_19_5)
).set_constraint(
    PrimaryKey(['id'], "pk_product_transaction")
)


# ============================================================================

def get_all_tables() -> List[Table]:
    """
    Returns all table definitions in dependency order.
    
    Tables are ordered to respect foreign key dependencies - referenced
    tables appear before tables that reference them.
    
    :return: List of all Table instances in creation order.
    """
    return [
        # Dimension tables with no dependencies
        account_type_tbl,
        financial_product_type_tbl,
        transaction_type_tbl,
        provider_tbl,
        holder_tbl,

        # Dimension tables with dependencies
        account_tbl,
        financial_product_tbl,

        # Fact tables
        exchange_rate_tbl,
        account_balance_tbl,
        account_transaction_tbl,
        product_value_tbl,
        product_transaction_tbl
    ]


def create_schema(db_manager: DatabaseManager, force: bool = False, seed: bool = True) -> None:
    """
    Creates the complete database schema with optional seeding.
    
    :param db_manager: DatabaseManager instance for database operations.
    :param force: If True, drops existing tables before creating new ones.
    :param seed: If True, inserts seed data after table creation.
    :raises Exception: If any database operation fails, triggers rollback.
    """

    schemas = [STG, REF]
    tables = get_all_tables()
    with db_manager.get_connection() as conn:
        try:
            if force:
                # Drop tables in reverse order to respect foreign key dependencies
                for table in reversed(tables):
                    table.drop(conn)

                # Drop schemas
                for schema in schemas:
                    schema.drop(conn)

            # Create schemas:
            for schema in schemas:
                schema.create(conn)

            # Create tables in dependency order
            for table in tables:
                table.create(conn)

            # Insert seed data if requested
            if seed:
                for table in tables:
                    if table.seed:  # Only seed tables that have seed data
                        table.insert(conn, table.seed)

        except Exception as e:
            logger.error(f"Error while creating schema: {e}")
            conn.rollback()
            raise
        else:
            conn.commit()
            logger.info("Database schema created successfully.")


TABLES = {tbl.name: tbl for tbl in get_all_tables()}
