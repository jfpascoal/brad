"""
Entity management page for creating and managing accounts, products, providers, and holders.

This module provides a Streamlit page for creating new entities that are used
in balance and valuation entries. It includes forms for providers, holders,
accounts, and financial products.
"""

from datetime import date
from typing import List, Optional

import streamlit as st

from brad.sql import (
    DatabaseManager,
    list_providers,
    list_holders,
    list_accounts,
    list_financial_products,
    list_account_types,
    list_financial_product_types,
    insert_provider,
    insert_holder,
    insert_account,
    insert_financial_product,
)
from brad.frontend.utils import get_entity_names


def get_db() -> DatabaseManager:
    """
    Retrieves the DatabaseManager from session state.

    :return: DatabaseManager instance.
    """
    return st.session_state.db


# =============================================================================
# Provider Form
# =============================================================================

def render_provider_form() -> None:
    """
    Renders the form for creating a new provider.
    """
    st.subheader('Add New Provider')

    with st.form('provider_form', clear_on_submit=True):
        name = st.text_input(
            'Provider Name *',
            placeholder='e.g., Barclays, Vanguard',
            help='Name of the financial institution or provider.'
        )

        country = st.text_input(
            'Country Code *',
            placeholder='e.g., GB, PT, US',
            max_chars=2,
            help='ISO 3166-1 alpha-2 country code.'
        )

        submitted = st.form_submit_button('Create Provider', type='primary')

        if submitted:
            if not name or not country:
                st.error('Please fill in all required fields.')
            elif len(country) != 2:
                st.error('Country code must be exactly 2 characters.')
            else:
                try:
                    insert_provider(get_db(), name=name, country_iso_alpha2=country.upper())
                    st.success(f'Provider "{name}" created successfully.')
                except Exception as e:
                    st.error(f'Failed to create provider: {e}')


def render_providers_list() -> None:
    """
    Renders the list of existing providers.
    """
    providers = list_providers(get_db())

    if providers:
        st.caption(f'{len(providers)} provider(s)')
        for provider in providers:
            st.text(f"• {provider['name']} ({provider['country_iso_alpha2']})")
    else:
        st.caption('No providers found.')


# =============================================================================
# Holder Form
# =============================================================================

def render_holder_form() -> None:
    """
    Renders the form for creating a new holder.
    """
    st.subheader('Add New Holder')

    with st.form('holder_form', clear_on_submit=True):
        name = st.text_input(
            'Holder Name *',
            placeholder='e.g., John Doe',
            help='Name of the account or product holder.'
        )

        tax_bracket = st.text_input(
            'Tax Bracket',
            placeholder='e.g., Basic, Higher, Additional',
            help='Optional tax bracket classification.'
        )

        submitted = st.form_submit_button('Create Holder', type='primary')

        if submitted:
            if not name:
                st.error('Please enter a holder name.')
            else:
                try:
                    insert_holder(
                        get_db(),
                        name=name,
                        tax_bracket=tax_bracket if tax_bracket else None
                    )
                    st.success(f'Holder "{name}" created successfully.')
                except Exception as e:
                    st.error(f'Failed to create holder: {e}')


def render_holders_list() -> None:
    """
    Renders the list of existing holders.
    """
    holders = list_holders(get_db())

    if holders:
        st.caption(f'{len(holders)} holder(s)')
        for holder in holders:
            tax_info = f" - {holder['tax_bracket']}" if holder.get('tax_bracket') else ''
            st.text(f"• {holder['name']}{tax_info}")
    else:
        st.caption('No holders found.')


# =============================================================================
# Account Form
# =============================================================================

def render_account_form() -> None:
    """
    Renders the form for creating a new account.
    """
    st.subheader('Add New Account')

    # Fetch options for dropdowns
    providers = list_providers(get_db())
    holders = list_holders(get_db())
    account_types = list_account_types(get_db())

    if not providers:
        st.warning('Please create a provider first before adding an account.')
        return

    if not holders:
        st.warning('Please create a holder first before adding an account.')
        return

    provider_names = get_entity_names(providers)
    holder_names = get_entity_names(holders)
    type_names = [t['name'] for t in account_types if t['name'] != 'Unknown']

    with st.form('account_form', clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                'Account Name *',
                placeholder='e.g., Main Current Account',
                help='A unique name for this account.'
            )

            account_type = st.selectbox(
                'Account Type *',
                options=type_names,
                help='Type of account.'
            )

            currency = st.text_input(
                'Currency *',
                placeholder='e.g., GBP, EUR, USD',
                max_chars=3,
                help='Currency code for this account.'
            )

            provider = st.selectbox(
                'Provider *',
                options=provider_names,
                help='Financial institution for this account.'
            )

        with col2:
            holder_1 = st.selectbox(
                'Primary Holder *',
                options=holder_names,
                help='Primary account holder.'
            )

            holder_2 = st.selectbox(
                'Secondary Holder',
                options=[''] + holder_names,
                help='Optional secondary holder (for joint accounts).'
            )

            holder_3 = st.selectbox(
                'Tertiary Holder',
                options=[''] + holder_names,
                help='Optional third holder.'
            )

            is_active = st.checkbox('Active', value=True, help='Whether the account is currently active.')

        st.markdown('**Optional Details**')
        col3, col4 = st.columns(2)

        with col3:
            account_number = st.text_input('Account Number')
            sort_code = st.text_input('Sort Code')
            opening_date = st.date_input(
                'Opening Date',
                value=None,
                max_value=date.today()
            )

        with col4:
            iban = st.text_input('IBAN')
            swift_code = st.text_input('SWIFT/BIC Code')
            closing_date = st.date_input(
                'Closing Date',
                value=None,
                max_value=date.today()
            )

        submitted = st.form_submit_button('Create Account', type='primary')

        if submitted:
            if not name or not account_type or not currency or not provider or not holder_1:
                st.error('Please fill in all required fields.')
            elif len(currency) != 3:
                st.error('Currency code must be exactly 3 characters.')
            else:
                try:
                    insert_account(
                        get_db(),
                        name=name,
                        account_type=account_type,
                        currency=currency.upper(),
                        provider_name=provider,
                        holder_name_1=holder_1,
                        holder_name_2=holder_2 if holder_2 else None,
                        holder_name_3=holder_3 if holder_3 else None,
                        account_number=account_number if account_number else None,
                        sort_code=sort_code if sort_code else None,
                        iban=iban if iban else None,
                        swift_code=swift_code if swift_code else None,
                        opening_date=opening_date,
                        closing_date=closing_date,
                        is_active=is_active
                    )
                    st.success(f'Account "{name}" created successfully.')
                except Exception as e:
                    st.error(f'Failed to create account: {e}')


def render_accounts_list() -> None:
    """
    Renders the list of existing accounts.
    """
    accounts = list_accounts(get_db(), active_only=False)

    if accounts:
        st.caption(f'{len(accounts)} account(s)')
        for account in accounts:
            status = '✓' if account.get('is_active') else '✗'
            st.text(f"{status} {account['name']} ({account['account_type']}, {account['currency']})")
    else:
        st.caption('No accounts found.')


# =============================================================================
# Financial Product Form
# =============================================================================

def render_financial_product_form() -> None:
    """
    Renders the form for creating a new financial product.
    """
    st.subheader('Add New Financial Product')

    # Fetch options for dropdowns
    providers = list_providers(get_db())
    holders = list_holders(get_db())
    accounts = list_accounts(get_db())
    product_types = list_financial_product_types(get_db())

    if not providers:
        st.warning('Please create a provider first before adding a financial product.')
        return

    if not holders:
        st.warning('Please create a holder first before adding a financial product.')
        return

    provider_names = get_entity_names(providers)
    holder_names = get_entity_names(holders)
    account_names = [''] + get_entity_names(accounts)
    type_names = [t['name'] for t in product_types if t['name'] != 'Unknown']

    with st.form('product_form', clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                'Product Name *',
                placeholder='e.g., Vanguard FTSE All-World ETF',
                help='A unique name for this financial product.'
            )

            product_type = st.selectbox(
                'Product Type *',
                options=type_names,
                help='Type of financial product.'
            )

            currency = st.text_input(
                'Currency *',
                placeholder='e.g., GBP, EUR, USD',
                max_chars=3,
                help='Currency code for this product.'
            )

            provider = st.selectbox(
                'Provider *',
                options=provider_names,
                help='Provider or platform for this product.'
            )

        with col2:
            holder = st.selectbox(
                'Holder *',
                options=holder_names,
                help='Owner of this financial product.'
            )

            linked_account = st.selectbox(
                'Linked Account',
                options=account_names,
                help='Optional linked account (e.g., ISA wrapper account).'
            )

            ticker = st.text_input(
                'Ticker Symbol',
                placeholder='e.g., VWRL, AAPL',
                help='Stock ticker symbol if applicable.'
            )

            isin = st.text_input(
                'ISIN',
                placeholder='e.g., IE00B3RBWM25',
                help='International Securities Identification Number.'
            )

        is_active = st.checkbox('Active', value=True, help='Whether the product is currently held.')

        submitted = st.form_submit_button('Create Financial Product', type='primary')

        if submitted:
            if not name or not product_type or not currency or not provider or not holder:
                st.error('Please fill in all required fields.')
            elif len(currency) != 3:
                st.error('Currency code must be exactly 3 characters.')
            else:
                try:
                    insert_financial_product(
                        get_db(),
                        name=name,
                        financial_product_type=product_type,
                        currency=currency.upper(),
                        provider_name=provider,
                        holder_name=holder,
                        linked_account_name=linked_account if linked_account else None,
                        ticker=ticker if ticker else None,
                        isin=isin if isin else None,
                        is_active=is_active
                    )
                    st.success(f'Financial product "{name}" created successfully.')
                except Exception as e:
                    st.error(f'Failed to create financial product: {e}')


def render_financial_products_list() -> None:
    """
    Renders the list of existing financial products.
    """
    products = list_financial_products(get_db(), active_only=False)

    if products:
        st.caption(f'{len(products)} product(s)')
        for product in products:
            status = '✓' if product.get('is_active') else '✗'
            ticker_info = f" [{product['ticker']}]" if product.get('ticker') else ''
            st.text(f"{status} {product['name']}{ticker_info} ({product['financial_product_type']})")
    else:
        st.caption('No financial products found.')


# =============================================================================
# Main Page
# =============================================================================

def render_entity_management_page() -> None:
    """
    Renders the main entity management page with tabs for different entity types.

    This page allows users to create and view:
    - Providers (financial institutions)
    - Holders (account/product owners)
    - Accounts
    - Financial Products
    """
    st.title('Manage Entities')

    # Determine initial tab from session state (for shortcuts from other pages)
    default_tab = st.session_state.get('entity_tab', 'Providers')
    tab_options = ['Providers', 'Holders', 'Accounts', 'Financial Products']
    default_index = tab_options.index(default_tab) if default_tab in tab_options else 0

    tabs = st.tabs(tab_options)

    with tabs[0]:  # Providers
        col_form, col_list = st.columns([2, 1])
        with col_form:
            render_provider_form()
        with col_list:
            st.subheader('Existing Providers')
            render_providers_list()

    with tabs[1]:  # Holders
        col_form, col_list = st.columns([2, 1])
        with col_form:
            render_holder_form()
        with col_list:
            st.subheader('Existing Holders')
            render_holders_list()

    with tabs[2]:  # Accounts
        col_form, col_list = st.columns([2, 1])
        with col_form:
            render_account_form()
        with col_list:
            st.subheader('Existing Accounts')
            render_accounts_list()

    with tabs[3]:  # Financial Products
        col_form, col_list = st.columns([2, 1])
        with col_form:
            render_financial_product_form()
        with col_list:
            st.subheader('Existing Products')
            render_financial_products_list()

    # Clear the entity_tab from session state after rendering
    if 'entity_tab' in st.session_state:
        del st.session_state['entity_tab']
