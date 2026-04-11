"""
Valuation entry page for adding financial product valuation records.

This module provides a Streamlit page for entering one or more valuation
entries for existing financial products, with batch entry support, last entry
preview, and delta calculation.
"""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

import streamlit as st

from brad.sql import (
    DatabaseManager,
    list_financial_products,
    get_latest_valuation,
    insert_valuations,
)
from brad.frontend.utils import (
    format_currency,
    format_delta,
    get_entity_names,
    calculate_delta,
)


def get_db() -> DatabaseManager:
    """
    Retrieves the DatabaseManager from session state.

    :return: DatabaseManager instance.
    """
    return st.session_state.db


def render_last_entry_preview(product_name: str, currency: str) -> Optional[dict]:
    """
    Renders the preview of the most recent valuation entry for a product.

    :param product_name: Name of the selected financial product.
    :param currency: Currency code of the product.
    :return: The latest valuation entry dict, or None if no entries exist.
    """
    latest = get_latest_valuation(get_db(), product_name)

    if latest:
        details = [f"**Last entry:** {latest['date'].strftime('%d %b %Y')}"]
        details.append(f"Value: {format_currency(latest['current_value'], currency)}")

        if latest.get('units'):
            details.append(f"Units: {latest['units']:,.4f}")
        if latest.get('unit_value'):
            details.append(f"Unit value: {format_currency(latest['unit_value'], currency)}")

        st.info(' — '.join(details))
    else:
        st.info('No previous entries for this product.')

    return latest


def render_delta_indicator(
    new_value: Optional[Decimal],
    previous_value: Optional[Decimal],
    currency: str
) -> None:
    """
    Renders the delta indicator showing change from previous valuation.

    :param new_value: The new valuation value entered by the user.
    :param previous_value: The previous valuation value (from DB or batch).
    :param currency: Currency code for display.
    """
    if new_value is None or previous_value is None:
        return

    delta = calculate_delta(new_value, previous_value)
    delta_str = format_delta(delta['absolute'], delta['percentage'])

    if delta['absolute'] is not None:
        if delta['absolute'] > 0:
            st.success(f'Change: {delta_str}')
        elif delta['absolute'] < 0:
            st.error(f'Change: {delta_str}')
        else:
            st.info(f'Change: {delta_str}')


def render_batch_table(product_name: str, currency: str, latest_valuation: Optional[dict]) -> None:
    """
    Renders the batch entry table showing entries to be submitted.

    :param product_name: Name of the selected financial product.
    :param currency: Currency code of the product.
    :param latest_valuation: The latest valuation from the database.
    """
    batch = st.session_state.valuation_batch

    if not batch:
        return

    st.subheader('Pending Entries')

    # Filter batch for current product
    product_batch = [e for e in batch if e['financial_product_name'] == product_name]

    if not product_batch:
        st.caption('No pending entries for this product.')
        return

    # Display batch entries with deltas
    previous_value = latest_valuation['current_value'] if latest_valuation else None

    for i, entry in enumerate(product_batch):
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])

        with col1:
            st.text(entry['date'].strftime('%d %b %Y'))

        with col2:
            st.text(format_currency(entry['current_value'], currency))

        with col3:
            units_str = f"{entry['units']:,.4f}" if entry.get('units') else '-'
            st.text(units_str)

        with col4:
            delta = calculate_delta(entry['current_value'], previous_value)
            st.text(format_delta(delta['absolute'], delta['percentage']))

        with col5:
            if st.button('🗑️', key=f'remove_valuation_{i}', help='Remove entry'):
                st.session_state.valuation_batch = [
                    e for e in batch
                    if not (e['financial_product_name'] == product_name and
                            e['date'] == entry['date'] and
                            e['current_value'] == entry['current_value'])
                ]
                st.rerun()

        previous_value = entry['current_value']


def add_to_batch(
    product_name: str,
    entry_date: date,
    current_value: Decimal,
    units: Optional[Decimal],
    unit_value: Optional[Decimal]
) -> None:
    """
    Adds a new entry to the valuation batch.

    :param product_name: Name of the financial product.
    :param entry_date: Date of the valuation entry.
    :param current_value: Total current value of the holding.
    :param units: Optional number of units held.
    :param unit_value: Optional value per unit.
    """
    st.session_state.valuation_batch.append({
        'financial_product_name': product_name,
        'date': entry_date,
        'current_value': current_value,
        'units': units,
        'unit_value': unit_value
    })


def clear_batch(product_name: Optional[str] = None) -> None:
    """
    Clears the valuation batch, optionally for a specific product only.

    :param product_name: If provided, only clears entries for this product.
    """
    if product_name:
        st.session_state.valuation_batch = [
            e for e in st.session_state.valuation_batch
            if e['financial_product_name'] != product_name
        ]
    else:
        st.session_state.valuation_batch = []


def submit_batch(product_name: str) -> bool:
    """
    Submits the batch entries for a specific product to the database.

    :param product_name: Name of the product to submit entries for.
    :return: True if submission was successful, False otherwise.
    """
    batch = [e for e in st.session_state.valuation_batch
             if e['financial_product_name'] == product_name]

    if not batch:
        return False

    try:
        count = insert_valuations(get_db(), batch)
        clear_batch(product_name)
        st.success(f'Successfully added {count} valuation entries.')
        return True
    except Exception as e:
        st.error(f'Failed to submit entries: {e}')
        return False


def render_valuation_entry_page() -> None:
    """
    Renders the main valuation entry page.

    This page allows users to:
    - Select a financial product from a dropdown
    - View the most recent valuation entry
    - Add one or more valuation entries (batch mode)
    - See delta calculations for each entry
    - Submit all entries at once
    """
    st.title('Add Product Valuation')

    # Fetch financial products for dropdown
    products = list_financial_products(get_db())

    if not products:
        st.warning('No financial products found. Please create a product first.')
        if st.button('Go to Entity Management'):
            st.session_state['nav_to'] = 'Manage Entities'
            st.rerun()
        return

    # Create product lookup
    product_map = {prod['name']: prod for prod in products}
    product_names = get_entity_names(products)

    # Product selection
    selected_product = st.selectbox(
        'Select Financial Product',
        options=product_names,
        help='Choose the financial product to add a valuation entry for.'
    )

    if not selected_product:
        return

    product = product_map[selected_product]
    currency = product.get('currency', '')

    # Show shortcut to create new product
    with st.expander('Product not listed?'):
        st.markdown('You can create a new financial product in the **Manage Entities** section.')
        if st.button('Create New Product', key='create_product_shortcut'):
            st.session_state['entity_tab'] = 'Financial Products'

    st.divider()

    # Last entry preview
    latest_valuation = render_last_entry_preview(selected_product, currency)

    st.divider()

    # Entry form
    st.subheader('New Entry')

    col1, col2 = st.columns(2)

    with col1:
        entry_date = st.date_input(
            'Date',
            value=date.today(),
            max_value=date.today(),
            help='Date of the valuation entry.'
        )

    with col2:
        value_input = st.text_input(
            f'Current Value ({currency})',
            placeholder='0.00',
            help='Total current value of your holding.'
        )

    # Optional fields for units and unit value
    col3, col4 = st.columns(2)

    with col3:
        units_input = st.text_input(
            'Units (optional)',
            placeholder='0.0000',
            help='Number of units/shares held.'
        )

    with col4:
        unit_value_input = st.text_input(
            f'Unit Value ({currency}, optional)',
            placeholder='0.00',
            help='Value per unit/share.'
        )

    # Parse and validate inputs
    current_value: Optional[Decimal] = None
    units_value: Optional[Decimal] = None
    unit_value: Optional[Decimal] = None

    if value_input:
        try:
            current_value = Decimal(value_input.replace(',', ''))
        except InvalidOperation:
            st.error('Please enter a valid number for current value.')

    if units_input:
        try:
            units_value = Decimal(units_input.replace(',', ''))
        except InvalidOperation:
            st.error('Please enter a valid number for units.')

    if unit_value_input:
        try:
            unit_value = Decimal(unit_value_input.replace(',', ''))
        except InvalidOperation:
            st.error('Please enter a valid number for unit value.')

    # Show delta preview
    if current_value is not None:
        # Determine previous value (from batch or database)
        product_batch = [e for e in st.session_state.valuation_batch
                         if e['financial_product_name'] == selected_product]
        if product_batch:
            previous_value = product_batch[-1]['current_value']
        elif latest_valuation:
            previous_value = latest_valuation['current_value']
        else:
            previous_value = None

        render_delta_indicator(current_value, previous_value, currency)

    st.divider()

    # Action buttons
    col_add, col_submit, col_clear = st.columns([1, 1, 1])

    with col_add:
        add_disabled = current_value is None
        if st.button('Add to Batch', disabled=add_disabled, use_container_width=True):
            add_to_batch(selected_product, entry_date, current_value, units_value, unit_value)
            st.rerun()

    with col_submit:
        product_batch = [e for e in st.session_state.valuation_batch
                         if e['financial_product_name'] == selected_product]
        submit_disabled = len(product_batch) == 0
        if st.button('Submit All', disabled=submit_disabled, type='primary', use_container_width=True):
            submit_batch(selected_product)
            st.rerun()

    with col_clear:
        if st.button('Clear Batch', use_container_width=True):
            clear_batch(selected_product)
            st.rerun()

    # Render batch table
    render_batch_table(selected_product, currency, latest_valuation)
