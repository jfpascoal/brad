"""
Balance entry page for adding account balance records.

This module provides a Streamlit page for entering one or more balance
entries for existing accounts, with batch entry support, last entry
preview, and delta calculation.
"""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

import streamlit as st

import contextlib

from brad.core.models.operational import Account, AccountBalance
from brad.repositories.accounts import AccountRepository, AccountBalanceRepository
from brad.frontend.utils import (
    format_currency,
    format_delta,
    get_entity_names,
    calculate_delta,
)


@contextlib.contextmanager
def get_session():
    """Provides a transactional scope around a series of operations."""
    with st.session_state.session_factory() as session:
        yield session


def render_last_entry_preview(account: Account) -> Optional[AccountBalance]:
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
            f"{format_currency(latest.balance, account.currency)}"
        )
    else:
        st.info('No previous entries for this account.')

    return latest


def render_delta_indicator(
    new_balance: Optional[Decimal],
    previous_balance: Optional[Decimal],
    currency: str
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
    delta_str = format_delta(delta['absolute'], delta['percentage'])

    if delta['absolute'] is not None:
        if delta['absolute'] > 0:
            st.success(f'Change: {delta_str}')
        elif delta['absolute'] < 0:
            st.error(f'Change: {delta_str}')
        else:
            st.info(f'Change: {delta_str}')


def render_batch_table(account: Account, latest_balance: Optional[AccountBalance]) -> None:
    """
    Renders the batch entry table showing entries to be submitted.

    :param account: The selected Account model.
    :param latest_balance: The latest balance from the database.
    """
    batch = st.session_state.balance_batch

    if not batch:
        return

    st.subheader('Pending Entries')

    # Filter batch for current account
    account_batch = [e for e in batch if e['account_id'] == account.id]

    if not account_batch:
        st.caption('No pending entries for this account.')
        return

    # Display batch entries with deltas
    previous_value = latest_balance.balance if latest_balance else None

    for i, entry in enumerate(account_batch):
        col1, col2, col3, col4 = st.columns([2, 2, 3, 1])

        with col1:
            st.text(entry['date'].strftime('%d %b %Y'))

        with col2:
            st.text(format_currency(entry['balance'], account.currency))

        with col3:
            delta = calculate_delta(entry['balance'], previous_value)
            st.text(format_delta(delta['absolute'], delta['percentage']))

        with col4:
            if st.button('🗑️', key=f'remove_balance_{i}', help='Remove entry'):
                st.session_state.balance_batch = [
                    e for j, e in enumerate(batch)
                    if not (e['account_id'] == account.id and
                            batch.index(e) == batch.index(entry))
                ]
                st.rerun()

        previous_value = entry['balance']


def add_to_batch(account: Account, entry_date: date, balance: Decimal) -> None:
    """
    Adds a new entry to the balance batch.

    :param account: The Account model.
    :param entry_date: Date of the balance entry.
    :param balance: Balance amount.
    """
    st.session_state.balance_batch.append({
        'account_id': account.id,
        'date': entry_date,
        'balance': balance
    })


def clear_batch(account_id: Optional[int] = None) -> None:
    """
    Clears the balance batch, optionally for a specific account only.

    :param account_id: If provided, only clears entries for this account.
    """
    if account_id is not None:
        st.session_state.balance_batch = [
            e for e in st.session_state.balance_batch
            if e['account_id'] != account_id
        ]
    else:
        st.session_state.balance_batch = []


def submit_batch(account: Account) -> bool:
    """
    Submits the batch entries for a specific account to the database.

    :param account: The Account model to submit entries for.
    :return: True if submission was successful, False otherwise.
    """
    batch = [e for e in st.session_state.balance_batch if e['account_id'] == account.id]

    if not batch:
        return False

    try:
        with get_session() as session:
            repo = AccountBalanceRepository(session)
            balances = [
                AccountBalance(account_id=e['account_id'], date=e['date'], balance=e['balance'])
                for e in batch
            ]
            repo.create_many(balances)
            session.commit()
            
        clear_batch(account.id)
        st.success(f'Successfully added {len(batch)} balance entries.')
        return True
    except Exception as e:
        st.error(f'Failed to submit entries: {e}')
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
    st.title('Add Account Balance')

    # Fetch accounts for dropdown
    with get_session() as session:
        accounts = AccountRepository(session).get_active()

    if not accounts:
        st.warning('No accounts found. Please create an account first.')
        if st.button('Go to Entity Management'):
            st.session_state['nav_to'] = 'Manage Entities'
            st.rerun()
        return

    # Create account lookup
    account_map = {acc.name: acc for acc in accounts}
    account_names = get_entity_names(accounts)

    # Account selection
    selected_account_name = st.selectbox(
        'Select Account',
        options=account_names,
        help='Choose the account to add a balance entry for.'
    )

    if not selected_account_name:
        return

    account = account_map[selected_account_name]
    currency = account.currency or ''

    # Show shortcut to create new account
    with st.expander('Account not listed?'):
        st.markdown('You can create a new account in the **Manage Entities** section.')
        if st.button('Create New Account', key='create_account_shortcut'):
            st.session_state['entity_tab'] = 'Accounts'
            st.switch_page('pages/entity_management.py') if hasattr(st, 'switch_page') else None

    st.divider()

    # Last entry preview
    latest_balance = render_last_entry_preview(account)

    st.divider()

    # Entry form
    st.subheader('New Entry')

    col1, col2 = st.columns(2)

    with col1:
        entry_date = st.date_input(
            'Date',
            value=date.today(),
            max_value=date.today(),
            help='Date of the balance entry.'
        )

    with col2:
        balance_input = st.text_input(
            f'Balance ({currency})',
            placeholder='0.00',
            help='Current balance amount.'
        )

    # Parse and validate balance input
    balance_value: Optional[Decimal] = None
    if balance_input:
        try:
            balance_value = Decimal(balance_input.replace(',', ''))
        except InvalidOperation:
            st.error('Please enter a valid number.')

    # Show delta preview
    if balance_value is not None:
        # Determine previous value (from batch or database)
        account_batch = [e for e in st.session_state.balance_batch
                         if e['account_id'] == account.id]
        if account_batch:
            previous_value = account_batch[-1]['balance']
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
        if st.button('Add to Batch', disabled=add_disabled, use_container_width=True):
            add_to_batch(account, entry_date, balance_value)
            st.rerun()

    with col_submit:
        account_batch = [e for e in st.session_state.balance_batch
                         if e['account_id'] == account.id]
        submit_disabled = len(account_batch) == 0
        if st.button('Submit All', disabled=submit_disabled, type='primary', use_container_width=True):
            submit_batch(account)
            st.rerun()

    with col_clear:
        if st.button('Clear Batch', use_container_width=True):
            clear_batch(account.id)
            st.rerun()

    # Render batch table
    render_batch_table(account, latest_balance)
