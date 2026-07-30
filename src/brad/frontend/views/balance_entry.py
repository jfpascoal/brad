"""
Balance entry page for adding account balance records.

This module provides a Streamlit page for entering one or more balance
entries for existing accounts, with batch entry support, last entry
preview, and delta calculation.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

import streamlit as st

from brad.core.models.operational import Account, AccountBalance
from brad.frontend.constants import EntityTabs, Pages, StateKeys
from brad.frontend.utils import (
    calculate_delta,
    format_currency,
    format_delta,
    get_entity_names,
    get_session,
)
from brad.repositories.accounts import AccountBalanceRepository, AccountRepository


def render_last_entry_preview(account: Account) -> AccountBalance | None:
    """
    Renders the preview of the most recent balance entry for an account.

    :param account: The selected Account model.
    :return: The latest AccountBalance model, or None if no entries exist.
    """
    with get_session() as session:
        repo = AccountBalanceRepository(session)
        latest = repo.get_latest(account.id)

    if latest:
        st.info(
            f"**Last entry:** {latest.date.strftime('%d %b %Y')} — "
            f"{format_currency(latest.balance, account.currency_code)}"
        )
    else:
        st.info("No previous entries for this account.")

    return latest


def render_delta_indicator(
    new_balance: Decimal | None, previous_balance: Decimal | None, currency: str
) -> None:
    """
    Renders the delta indicator showing change from previous balance.

    :param new_balance: The new balance value entered by the user.
    :param previous_balance: The previous balance value (from DB or batch).
    :param currency: Currency code for display.
    """
    if new_balance is None or previous_balance is None:
        return

    delta = calculate_delta(new_balance, previous_balance)
    delta_str = format_delta(delta["absolute"], delta["percentage"])

    if delta["absolute"] is not None:
        if delta["absolute"] > 0:
            st.success(f"Change: {delta_str}")
        elif delta["absolute"] < 0:
            st.error(f"Change: {delta_str}")
        else:
            st.info(f"Change: {delta_str}")


def render_batch_table(account: Account, latest_balance: AccountBalance | None) -> None:
    """
    Renders the batch entry table showing entries to be submitted.

    :param account: The selected Account model.
    :param latest_balance: The latest balance from the database.
    """
    batch = st.session_state.get(StateKeys.BALANCE_BATCH, [])

    if not batch:
        return

    st.subheader("Pending Entries")

    # Filter batch for current account
    account_batch = [e for e in batch if e["account_id"] == account.id]

    if not account_batch:
        st.caption("No pending entries for this account.")
        return

    # Display batch entries with deltas
    previous_value = latest_balance.balance if latest_balance else None

    for i, entry in enumerate(account_batch):
        col1, col2, col3, col4 = st.columns([2, 2, 3, 1])

        with col1:
            st.text(entry["date"].strftime("%d %b %Y"))

        with col2:
            st.text(format_currency(entry["balance"], account.currency_code))

        with col3:
            delta = calculate_delta(entry["balance"], previous_value)
            st.text(format_delta(delta["absolute"], delta["percentage"]))

        with col4:
            if st.button(
                "🗑️", key=f"remove_balance_{account.id}_{i}", help="Remove entry"
            ):
                target_entry = entry
                st.session_state[StateKeys.BALANCE_BATCH] = [
                    e for e in batch if e is not target_entry
                ]
                st.rerun()

        previous_value = entry["balance"]


def add_to_batch(account: Account, entry_date: date, balance: Decimal) -> bool:
    """
    Adds a new entry to the balance batch.

    :param account: The Account model.
    :param entry_date: Date of the balance entry.
    :param balance: Balance amount.
    :return: True if added successfully, False if duplicate date.
    """
    batch = st.session_state.get(StateKeys.BALANCE_BATCH, [])
    for entry in batch:
        if entry["account_id"] == account.id and entry["date"] == entry_date:
            st.error(
                f"An entry for {entry_date.strftime('%d %b %Y')} already exists in the batch."
            )
            return False

    if StateKeys.BALANCE_BATCH not in st.session_state:
        st.session_state[StateKeys.BALANCE_BATCH] = []

    st.session_state[StateKeys.BALANCE_BATCH].append(
        {"account_id": account.id, "date": entry_date, "balance": balance}
    )
    return True


def clear_batch(account_id: int | None = None) -> None:
    """
    Clears the balance batch, optionally for a specific account only.

    :param account_id: If provided, only clears entries for this account.
    """
    if account_id is not None:
        st.session_state[StateKeys.BALANCE_BATCH] = [
            e
            for e in st.session_state.get(StateKeys.BALANCE_BATCH, [])
            if e["account_id"] != account_id
        ]
    else:
        st.session_state[StateKeys.BALANCE_BATCH] = []


def submit_batch(account: Account) -> bool:
    """
    Submits the batch entries for a specific account to the database.

    :param account: The Account model to submit entries for.
    :return: True if submission was successful, False otherwise.
    """
    batch = [
        e
        for e in st.session_state.get(StateKeys.BALANCE_BATCH, [])
        if e["account_id"] == account.id
    ]

    if not batch:
        return False

    try:
        with get_session() as session:
            repo = AccountBalanceRepository(session)
            balances = [
                AccountBalance(
                    account_id=e["account_id"], date=e["date"], balance=e["balance"]
                )
                for e in batch
            ]
            repo.create_many(balances)
            session.commit()

        clear_batch(account.id)
        st.success(f"Successfully added {len(batch)} balance entries.")
        return True
    except Exception as e:  # noqa: BLE001
        st.error(f"Failed to submit entries: {e}")
        return False


def render_balance_entry_page() -> None:
    """
    Renders the main balance entry page.

    This page allows users to:
    - Select an account from a dropdown
    - View the most recent balance entry
    - Add one or more balance entries (batch mode)
    - See delta calculations for each entry
    - Submit all entries at once
    """
    st.title("Add Account Balance")

    # Fetch accounts for dropdown
    with get_session() as session:
        accounts = AccountRepository(session).get_active()

    if not accounts:
        st.warning("No accounts found. Please create an account first.")
        if st.button("Go to Entity Management"):
            st.session_state[StateKeys.NAV_TO] = Pages.MANAGE_ENTITIES
            st.rerun()
        return

    # Create account lookup
    account_map = {acc.name: acc for acc in accounts}
    account_names = get_entity_names(accounts)

    # Account selection
    selected_account_name = st.selectbox(
        "Select Account",
        options=account_names,
        help="Choose the account to add a balance entry for.",
    )

    if not selected_account_name:
        return

    account = account_map[selected_account_name]
    currency = account.currency_code or ""

    # Show shortcut to create new account
    with st.expander("Account not listed?"):
        st.markdown("You can create a new account in the **Manage Entities** section.")
        if st.button("Create New Account", key="create_account_shortcut"):
            st.session_state[StateKeys.ENTITY_TAB] = EntityTabs.ACCOUNTS
            st.session_state[StateKeys.NAV_TO] = Pages.MANAGE_ENTITIES
            st.rerun()

    st.divider()

    # Last entry preview
    latest_balance = render_last_entry_preview(account)

    st.divider()

    # Entry form
    st.subheader("New Entry")

    col1, col2 = st.columns(2)

    with col1:
        entry_date = st.date_input(
            "Date",
            value=date.today(),  # noqa: DTZ011
            max_value=date.today(),  # noqa: DTZ011
            help="Date of the balance entry.",
        )

    with col2:
        balance_input = st.text_input(
            f"Balance ({currency})", placeholder="0.00", help="Current balance amount."
        )

    # Parse and validate balance input
    balance_value: Decimal | None = None
    if balance_input:
        try:
            balance_value = Decimal(balance_input.replace(",", ""))
        except InvalidOperation:
            st.error("Please enter a valid number.")

    # Show delta preview
    if balance_value is not None:
        # Determine previous value (from batch or database)
        account_batch = [
            e
            for e in st.session_state.get(StateKeys.BALANCE_BATCH, [])
            if e["account_id"] == account.id
        ]
        if account_batch:
            previous_value = account_batch[-1]["balance"]
        elif latest_balance:
            previous_value = latest_balance.balance
        else:
            previous_value = None

        render_delta_indicator(balance_value, previous_value, currency)

    st.divider()

    # Action buttons
    col_add, col_submit, col_clear = st.columns([1, 1, 1])

    with col_add:
        add_disabled = balance_value is None
        if st.button("Add to Batch", disabled=add_disabled, use_container_width=True):
            add_to_batch(account, entry_date, balance_value)
            st.rerun()

    with col_submit:
        account_batch = [
            e
            for e in st.session_state.get(StateKeys.BALANCE_BATCH, [])
            if e["account_id"] == account.id
        ]
        submit_disabled = len(account_batch) == 0
        if st.button(
            "Submit All",
            disabled=submit_disabled,
            type="primary",
            use_container_width=True,
        ):
            submit_batch(account)
            st.rerun()

    with col_clear:
        if st.button("Clear Batch", use_container_width=True):
            clear_batch(account.id)
            st.rerun()

    # Render batch table
    render_batch_table(account, latest_balance)
