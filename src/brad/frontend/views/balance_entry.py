"""
Balance entry page for adding account balance records.

This module provides a Streamlit page for entering one or more balance
entries for existing accounts, with batch entry support, last entry
preview, and delta calculation.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy.exc import IntegrityError
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


def render_batch_table() -> None:
    """
    Renders the batch entry table showing entries across all accounts to be submitted.
    Calculates deltas in chronological order per account.
    """
    batch = st.session_state.get(StateKeys.BALANCE_BATCH, [])

    if not batch:
        return

    st.subheader("Pending Entries")

    # Group batch entries by account_id and sort chronologically by date
    grouped_entries: dict[int, list[dict]] = {}
    for entry in batch:
        acc_id = entry["account_id"]
        grouped_entries.setdefault(acc_id, []).append(entry)

    # Calculate chronological deltas per account
    deltas_map: dict[id, dict] = {}
    with get_session() as session:
        repo = AccountBalanceRepository(session)
        for acc_id, entries in grouped_entries.items():
            # Sort entries by date ascending for delta calculation
            sorted_entries = sorted(entries, key=lambda x: x["date"])
            for i, entry in enumerate(sorted_entries):
                if i == 0:
                    latest_db = repo.get_latest_before(acc_id, entry["date"])
                    prev_val = latest_db.balance if latest_db else None
                else:
                    prev_val = sorted_entries[i - 1]["balance"]

                deltas_map[id(entry)] = calculate_delta(entry["balance"], prev_val)

    # Display batch entries in table
    for i, entry in enumerate(batch):
        col_acc, col_date, col_val, col_delta, col_del = st.columns([3, 2, 2, 3, 1])

        with col_acc:
            st.text(entry["account_name"])

        with col_date:
            st.text(entry["date"].strftime("%d %b %Y"))

        with col_val:
            st.text(format_currency(entry["balance"], entry["currency_code"]))

        with col_delta:
            delta = deltas_map.get(id(entry), {"absolute": None, "percentage": None})
            st.text(format_delta(delta["absolute"], delta["percentage"]))

        with col_del:
            if st.button("🗑️", key=f"remove_balance_{i}", help="Remove entry"):
                target_entry = entry
                st.session_state[StateKeys.BALANCE_BATCH] = [
                    e for e in batch if e is not target_entry
                ]
                st.rerun()


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
                f"An entry for account '{account.name}' on {entry_date.strftime('%d %b %Y')} already exists in the batch."
            )
            return False

    if StateKeys.BALANCE_BATCH not in st.session_state:
        st.session_state[StateKeys.BALANCE_BATCH] = []

    st.session_state[StateKeys.BALANCE_BATCH].append(
        {
            "account_id": account.id,
            "account_name": account.name,
            "currency_code": account.currency_code or "",
            "date": entry_date,
            "balance": balance,
        }
    )
    return True


def clear_batch() -> None:
    """Clears all pending entries in the balance batch."""
    st.session_state[StateKeys.BALANCE_BATCH] = []


def submit_batch() -> bool:
    """
    Submits all pending balance batch entries across accounts to the database.

    :return: True if submission was successful, False otherwise.
    """
    batch = st.session_state.get(StateKeys.BALANCE_BATCH, [])

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

        clear_batch()
        st.success(
            f"Successfully added {len(batch)} balance record(s) across accounts."
        )
        return True
    except IntegrityError:
        st.error(
            "Failed to submit entries: A balance record with the same account and date already exists in the database."
        )
        return False
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
    render_last_entry_preview(account)

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

    # Show delta preview for current entry date against DB/batch
    if balance_value is not None:
        # Determine preceding value for entry_date
        with get_session() as session:
            repo = AccountBalanceRepository(session)
            latest_before = repo.get_latest_before(account.id, entry_date)

        batch = st.session_state.get(StateKeys.BALANCE_BATCH, [])
        account_batch_before = [
            e for e in batch if e["account_id"] == account.id and e["date"] < entry_date
        ]

        if account_batch_before:
            account_batch_before.sort(key=lambda x: x["date"])
            previous_value = account_batch_before[-1]["balance"]
        elif latest_before:
            previous_value = latest_before.balance
        else:
            previous_value = None

        render_delta_indicator(balance_value, previous_value, currency)

    st.divider()

    # Action buttons
    col_add, col_submit, col_clear = st.columns([1, 1, 1])

    with col_add:
        add_disabled = balance_value is None
        if st.button(
            "Add to Batch", disabled=add_disabled, use_container_width=True
        ) and add_to_batch(account, entry_date, balance_value):
            st.rerun()

    batch_count = len(st.session_state.get(StateKeys.BALANCE_BATCH, []))

    with col_submit:
        submit_disabled = batch_count == 0
        btn_label = f"Submit All ({batch_count})" if batch_count > 0 else "Submit All"
        if (
            st.button(
                btn_label,
                disabled=submit_disabled,
                type="primary",
                use_container_width=True,
            )
            and submit_batch()
        ):
            st.rerun()

    with col_clear:
        if st.button("Clear Batch", use_container_width=True):
            clear_batch()
            st.rerun()

    # Render batch table across all accounts
    render_batch_table()
