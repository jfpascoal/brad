"""
Entity management page for creating and managing accounts, products, providers, and holders.

This module provides a Streamlit page for creating new entities that are used
in balance and valuation entries. It includes forms for providers, holders,
accounts, and financial products.
"""

from datetime import date

import streamlit as st

from brad.core.models.operational import Account, FinancialProduct, Holder, Provider
from brad.core.models.reference import AccountType, ProductType
from brad.frontend.constants import EntityTabs, StateKeys
from brad.frontend.utils import get_entity_names, get_session
from brad.repositories.accounts import AccountRepository
from brad.repositories.base import BaseRepository
from brad.repositories.products import ProductRepository

# =============================================================================
# Provider Form
# =============================================================================


def render_provider_form() -> None:
    """
    Renders the form for creating a new provider.
    """
    st.subheader("Add New Provider")

    with st.form("provider_form", clear_on_submit=True):
        name = st.text_input(
            "Provider Name *",
            placeholder="e.g., Barclays, Vanguard",
            help="Name of the financial institution or provider.",
        )

        country = st.text_input(
            "Country Code *",
            placeholder="e.g., GB, PT, US",
            max_chars=2,
            help="ISO 3166-1 alpha-2 country code.",
        )

        submitted = st.form_submit_button("Create Provider", type="primary")

        if submitted:
            if not name or not country:
                st.error("Please fill in all required fields.")
            elif len(country) != 2:
                st.error("Country code must be exactly 2 characters.")
            else:
                try:
                    with get_session() as session:
                        repo = BaseRepository(session, Provider)
                        repo.create(Provider(name=name, country=country.upper()))
                        session.commit()
                    st.success(f'Provider "{name}" created successfully.')
                except Exception as e:  # noqa: BLE001
                    st.error(f"Failed to create provider: {e}")


def render_providers_list() -> None:
    """
    Renders the list of existing providers.
    """
    with get_session() as session:
        providers = BaseRepository(session, Provider).list_all()

    if providers:
        st.caption(f"{len(providers)} provider(s)")
        for provider in providers:
            st.text(f"• {provider.name} ({provider.country})")
    else:
        st.caption("No providers found.")


# =============================================================================
# Holder Form
# =============================================================================


def render_holder_form() -> None:
    """
    Renders the form for creating a new holder.
    """
    st.subheader("Add New Holder")

    with st.form("holder_form", clear_on_submit=True):
        name = st.text_input(
            "Holder Name *",
            placeholder="e.g., John Doe",
            help="Name of the account or product holder.",
        )

        tax_bracket = st.text_input(
            "Tax Bracket",
            placeholder="e.g., Basic, Higher, Additional",
            help="Optional tax bracket classification.",
        )

        submitted = st.form_submit_button("Create Holder", type="primary")

        if submitted:
            if not name:
                st.error("Please enter a holder name.")
            else:
                try:
                    with get_session() as session:
                        repo = BaseRepository(session, Holder)
                        repo.create(
                            Holder(
                                name=name,
                                tax_bracket=tax_bracket if tax_bracket else None,
                            )
                        )
                        session.commit()
                    st.success(f'Holder "{name}" created successfully.')
                except Exception as e:  # noqa: BLE001
                    st.error(f"Failed to create holder: {e}")


def render_holders_list() -> None:
    """
    Renders the list of existing holders.
    """
    with get_session() as session:
        holders = BaseRepository(session, Holder).list_all()

    if holders:
        st.caption(f"{len(holders)} holder(s)")
        for holder in holders:
            tax_info = f" - {holder.tax_bracket}" if holder.tax_bracket else ""
            st.text(f"• {holder.name}{tax_info}")
    else:
        st.caption("No holders found.")


# =============================================================================
# Account Form
# =============================================================================


def render_account_form() -> None:
    """
    Renders the form for creating a new account.
    """
    st.subheader("Add New Account")

    with get_session() as session:
        providers = BaseRepository(session, Provider).list_all()
        holders = BaseRepository(session, Holder).list_all()
        account_types = BaseRepository(session, AccountType).list_all()

    if not providers:
        st.warning("Please create a provider first before adding an account.")
        return

    if not holders:
        st.warning("Please create a holder first before adding an account.")
        return

    provider_names = get_entity_names(providers)
    holder_names = get_entity_names(holders)
    type_names = [t.name for t in account_types if t.name != "Unknown"]

    with st.form("account_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Account Name *",
                placeholder="e.g., Main Current Account",
                help="A unique name for this account.",
            )

            account_type = st.selectbox(
                "Account Type *", options=type_names, help="Type of account."
            )

            currency = st.text_input(
                "Currency *",
                placeholder="e.g., GBP, EUR, USD",
                max_chars=3,
                help="Currency code for this account.",
            )

            provider = st.selectbox(
                "Provider *",
                options=provider_names,
                help="Financial institution for this account.",
            )

        with col2:
            holder_1 = st.selectbox(
                "Primary Holder *", options=holder_names, help="Primary account holder."
            )

            holder_2 = st.selectbox(
                "Secondary Holder",
                options=[""] + holder_names,
                help="Optional secondary holder (for joint accounts).",
            )

            holder_3 = st.selectbox(
                "Tertiary Holder",
                options=[""] + holder_names,
                help="Optional third holder.",
            )

            is_active = st.checkbox(
                "Active", value=True, help="Whether the account is currently active."
            )

        st.markdown("**Optional Details**")
        col3, col4 = st.columns(2)

        with col3:
            account_number = st.text_input("Account Number")
            sort_code = st.text_input("Sort Code")
            opening_date = st.date_input(
                "Opening Date",
                value=None,
                max_value=date.today(),  # noqa: DTZ011
            )

        with col4:
            iban = st.text_input("IBAN")
            swift_code = st.text_input("SWIFT/BIC Code")
            closing_date = st.date_input(
                "Closing Date",
                value=None,
                max_value=date.today(),  # noqa: DTZ011
            )

        submitted = st.form_submit_button("Create Account", type="primary")

        if submitted:
            if (
                not name
                or not account_type
                or not currency
                or not provider
                or not holder_1
            ):
                st.error("Please fill in all required fields.")
            elif len(currency) != 3:
                st.error("Currency code must be exactly 3 characters.")
            else:
                try:
                    with get_session() as session:
                        # Convert selected names back to IDs
                        provider_rc = BaseRepository(session, Provider).get_by_name(
                            provider
                        )
                        type_rc = BaseRepository(session, AccountType).get_by_name(
                            account_type
                        )

                        holder_res = BaseRepository(session, Holder)
                        h_ids = []
                        for h_name in [holder_1, holder_2, holder_3]:
                            if h_name:
                                h_ids.append(holder_res.get_by_name(h_name).id)

                        if len(h_ids) != len(set(h_ids)):
                            st.error(
                                "Please select distinct holders for primary, secondary, and tertiary fields."
                            )
                        else:
                            acc = Account(
                                name=name,
                                account_type_id=type_rc.id,
                                currency_code=currency.upper(),
                                provider_id=provider_rc.id,
                                account_number=account_number
                                if account_number
                                else None,
                                sort_code=sort_code if sort_code else None,
                                iban=iban if iban else None,
                                swift_code=swift_code if swift_code else None,
                                opening_date=opening_date,
                                closing_date=closing_date,
                                is_active=is_active,
                            )

                            repo = AccountRepository(session)
                            repo.create(acc)
                            session.flush()  # ensure ID is generated

                            repo.set_holders(acc, h_ids)
                            session.commit()
                            st.success(f'Account "{name}" created successfully.')
                except Exception as e:  # noqa: BLE001
                    st.error(f"Failed to create account: {e}")


def render_accounts_list() -> None:
    """
    Renders the list of existing accounts.
    """
    with get_session() as session:
        accounts = AccountRepository(session).list_all_with_types()

    if accounts:
        st.caption(f"{len(accounts)} account(s)")
        for account in accounts:
            status = "✓" if account.is_active else "✗"
            type_name = account.type_link.name if account.type_link else "Unknown"
            st.text(f"{status} {account.name} ({type_name}, {account.currency_code})")
    else:
        st.caption("No accounts found.")


# =============================================================================
# Financial Product Form
# =============================================================================


def render_financial_product_form() -> None:
    """
    Renders the form for creating a new financial product.
    """
    st.subheader("Add New Financial Product")

    with get_session() as session:
        providers = BaseRepository(session, Provider).list_all()
        holders = BaseRepository(session, Holder).list_all()
        accounts = BaseRepository(session, Account).list_all()
        product_types = BaseRepository(session, ProductType).list_all()

    if not providers:
        st.warning("Please create a provider first before adding a financial product.")
        return

    if not holders:
        st.warning("Please create a holder first before adding a financial product.")
        return

    provider_names = get_entity_names(providers)
    holder_names = get_entity_names(holders)
    account_names = [""] + get_entity_names(accounts)
    type_names = [t.name for t in product_types if t.name != "Unknown"]

    with st.form("product_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "Product Name *",
                placeholder="e.g., Vanguard FTSE All-World ETF",
                help="A unique name for this financial product.",
            )

            product_type = st.selectbox(
                "Product Type *", options=type_names, help="Type of financial product."
            )

            currency = st.text_input(
                "Currency *",
                placeholder="e.g., GBP, EUR, USD",
                max_chars=3,
                help="Currency code for this product.",
            )

            provider = st.selectbox(
                "Provider *",
                options=provider_names,
                help="Provider or platform for this product.",
            )

        with col2:
            holder = st.selectbox(
                "Holder *",
                options=holder_names,
                help="Owner of this financial product.",
            )

            linked_account = st.selectbox(
                "Linked Account",
                options=account_names,
                help="Optional linked account (e.g., ISA wrapper account).",
            )

            ticker = st.text_input(
                "Ticker Symbol",
                placeholder="e.g., VWRL, AAPL",
                help="Stock ticker symbol if applicable.",
            )

            isin = st.text_input(
                "ISIN",
                placeholder="e.g., IE00B3RBWM25",
                help="International Securities Identification Number.",
            )

        is_active = st.checkbox(
            "Active", value=True, help="Whether the product is currently held."
        )

        submitted = st.form_submit_button("Create Financial Product", type="primary")

        if submitted:
            if (
                not name
                or not product_type
                or not currency
                or not provider
                or not holder
            ):
                st.error("Please fill in all required fields.")
            elif len(currency) != 3:
                st.error("Currency code must be exactly 3 characters.")
            else:
                try:
                    with get_session() as session:
                        provider_rc = BaseRepository(session, Provider).get_by_name(
                            provider
                        )
                        type_rc = BaseRepository(session, ProductType).get_by_name(
                            product_type
                        )
                        holder_rc = BaseRepository(session, Holder).get_by_name(holder)

                        account_id = None
                        if linked_account:
                            account_rc = BaseRepository(session, Account).get_by_name(
                                linked_account
                            )
                            if account_rc:
                                account_id = account_rc.id

                        prod = FinancialProduct(
                            name=name,
                            product_type_id=type_rc.id,
                            currency_code=currency.upper(),
                            provider_id=provider_rc.id,
                            linked_account_id=account_id,
                            ticker=ticker if ticker else None,
                            isin=isin if isin else None,
                            is_active=is_active,
                        )

                        repo = ProductRepository(session)
                        repo.create(prod)
                        session.flush()

                        repo.set_holders(prod, [holder_rc.id])
                        session.commit()

                    st.success(f'Financial product "{name}" created successfully.')
                except Exception as e:  # noqa: BLE001
                    st.error(f"Failed to create financial product: {e}")


def render_financial_products_list() -> None:
    """
    Renders the list of existing financial products.
    """
    with get_session() as session:
        products = ProductRepository(session).list_all_with_types()

    if products:
        st.caption(f"{len(products)} product(s)")
        for product in products:
            status = "✓" if product.is_active else "✗"
            ticker_info = f" [{product.ticker}]" if product.ticker else ""
            type_name = product.type_link.name if product.type_link else "Unknown"
            st.text(f"{status} {product.name}{ticker_info} ({type_name})")
    else:
        st.caption("No financial products found.")


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
    st.title("Manage Entities")

    tab_options = EntityTabs.list_all()

    tabs = st.tabs(tab_options)

    with tabs[0]:  # Providers
        col_form, col_list = st.columns([2, 1])
        with col_form:
            render_provider_form()
        with col_list:
            st.subheader("Existing Providers")
            render_providers_list()

    with tabs[1]:  # Holders
        col_form, col_list = st.columns([2, 1])
        with col_form:
            render_holder_form()
        with col_list:
            st.subheader("Existing Holders")
            render_holders_list()

    with tabs[2]:  # Accounts
        col_form, col_list = st.columns([2, 1])
        with col_form:
            render_account_form()
        with col_list:
            st.subheader("Existing Accounts")
            render_accounts_list()

    with tabs[3]:  # Financial Products
        col_form, col_list = st.columns([2, 1])
        with col_form:
            render_financial_product_form()
        with col_list:
            st.subheader("Existing Products")
            render_financial_products_list()

    # Clear the entity_tab from session state after rendering
    if StateKeys.ENTITY_TAB in st.session_state:
        del st.session_state[StateKeys.ENTITY_TAB]
