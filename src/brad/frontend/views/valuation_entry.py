"""
Valuation entry page for adding financial product valuation records.

This module provides a Streamlit page for entering one or more valuation
entries for existing financial products, with batch entry support, last entry
preview, and delta calculation.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy.exc import IntegrityError
import streamlit as st

from brad.core.models.operational import FinancialProduct, ProductValue
from brad.frontend.constants import EntityTabs, Pages, StateKeys
from brad.frontend.utils import (
    calculate_delta,
    format_currency,
    format_delta,
    get_entity_names,
    get_session,
)
from brad.repositories.products import ProductRepository, ProductValueRepository


def render_last_entry_preview(product: FinancialProduct) -> ProductValue | None:
    """
    Renders the preview of the most recent valuation entry for a product.

    :param product: The selected FinancialProduct model.
    :return: The latest ProductValue model, or None if no entries exist.
    """
    with get_session() as session:
        latest = ProductValueRepository(session).get_latest(product.id)

    if latest:
        details = [f"**Last entry:** {latest.date.strftime('%d %b %Y')}"]
        details.append(
            f"Value: {format_currency(latest.current_value, product.currency_code)}"
        )

        if latest.units is not None:
            details.append(f"Units: {latest.units:,.4f}")
        if latest.unit_value is not None:
            details.append(
                f"Unit value: {format_currency(latest.unit_value, product.currency_code)}"
            )

        st.info(" — ".join(details))
    else:
        st.info("No previous entries for this product.")

    return latest


def render_delta_indicator(
    new_value: Decimal | None, previous_value: Decimal | None, currency: str
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
    Renders the batch entry table showing entries across all products to be submitted.
    Calculates deltas in chronological order per product.
    """
    batch = st.session_state.get(StateKeys.VALUATION_BATCH, [])

    if not batch:
        return

    st.subheader("Pending Entries")

    # Group batch entries by product_id and sort chronologically by date
    grouped_entries: dict[int, list[dict]] = {}
    for entry in batch:
        prod_id = entry["product_id"]
        grouped_entries.setdefault(prod_id, []).append(entry)

    # Calculate chronological deltas per product
    deltas_map: dict[id, dict] = {}
    with get_session() as session:
        repo = ProductValueRepository(session)
        for prod_id, entries in grouped_entries.items():
            sorted_entries = sorted(entries, key=lambda x: x["date"])
            for i, entry in enumerate(sorted_entries):
                if i == 0:
                    latest_db = repo.get_latest_before(prod_id, entry["date"])
                    prev_val = latest_db.current_value if latest_db else None
                else:
                    prev_val = sorted_entries[i - 1]["current_value"]

                deltas_map[id(entry)] = calculate_delta(
                    entry["current_value"], prev_val
                )

    # Display batch entries in table
    for i, entry in enumerate(batch):
        col_prod, col_date, col_val, col_units, col_delta, col_del = st.columns(
            [3, 2, 2, 2, 3, 1]
        )

        with col_prod:
            st.text(entry["product_name"])

        with col_date:
            st.text(entry["date"].strftime("%d %b %Y"))

        with col_val:
            st.text(format_currency(entry["current_value"], entry["currency_code"]))

        with col_units:
            units_str = f"{entry['units']:,.4f}" if entry.get("units") else "-"
            st.text(units_str)

        with col_delta:
            delta = deltas_map.get(id(entry), {"absolute": None, "percentage": None})
            st.text(format_delta(delta["absolute"], delta["percentage"]))

        with col_del:
            if st.button("🗑️", key=f"remove_valuation_{i}", help="Remove entry"):
                target_entry = entry
                st.session_state[StateKeys.VALUATION_BATCH] = [
                    e for e in batch if e is not target_entry
                ]
                st.rerun()


def add_to_batch(
    product: FinancialProduct,
    entry_date: date,
    current_value: Decimal,
    units: Decimal | None,
    unit_value: Decimal | None,
) -> bool:
    """
    Adds a new entry to the valuation batch.

    :param product: The FinancialProduct model.
    :param entry_date: Date of the valuation entry.
    :param current_value: Total current value of the holding.
    :param units: Optional number of units held.
    :param unit_value: Optional value per unit.
    :return: True if added successfully, False if duplicate date.
    """
    batch = st.session_state.get(StateKeys.VALUATION_BATCH, [])
    for entry in batch:
        if entry["product_id"] == product.id and entry["date"] == entry_date:
            st.error(
                f"An entry for product '{product.name}' on {entry_date.strftime('%d %b %Y')} already exists in the batch."
            )
            return False

    if StateKeys.VALUATION_BATCH not in st.session_state:
        st.session_state[StateKeys.VALUATION_BATCH] = []

    st.session_state[StateKeys.VALUATION_BATCH].append(
        {
            "product_id": product.id,
            "product_name": product.name,
            "currency_code": product.currency_code or "",
            "date": entry_date,
            "current_value": current_value,
            "units": units,
            "unit_value": unit_value,
        }
    )
    return True


def clear_batch() -> None:
    """Clears all pending entries in the valuation batch."""
    st.session_state[StateKeys.VALUATION_BATCH] = []


def submit_batch() -> bool:
    """
    Submits all pending valuation batch entries across products to the database.

    :return: True if submission was successful, False otherwise.
    """
    batch = st.session_state.get(StateKeys.VALUATION_BATCH, [])

    if not batch:
        return False

    try:
        with get_session() as session:
            repo = ProductValueRepository(session)
            valuations = [
                ProductValue(
                    product_id=e["product_id"],
                    date=e["date"],
                    current_value=e["current_value"],
                    units=e["units"],
                    unit_value=e["unit_value"],
                )
                for e in batch
            ]
            repo.create_many(valuations)
            session.commit()

        clear_batch()
        st.success(
            f"Successfully added {len(batch)} valuation record(s) across products."
        )
        return True
    except IntegrityError:
        st.error(
            "Failed to submit entries: A valuation record with the same product and date already exists in the database."
        )
        return False
    except Exception as e:  # noqa: BLE001
        st.error(f"Failed to submit entries: {e}")
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
    st.title("Add Product Valuation")

    # Fetch financial products for dropdown
    with get_session() as session:
        products = ProductRepository(session).get_active()

    if not products:
        st.warning("No financial products found. Please create a product first.")
        if st.button("Go to Entity Management"):
            st.session_state[StateKeys.NAV_TO] = Pages.MANAGE_ENTITIES
            st.rerun()
        return

    # Create product lookup
    product_map = {prod.name: prod for prod in products}
    product_names = get_entity_names(products)

    # Product selection
    selected_product_name = st.selectbox(
        "Select Financial Product",
        options=product_names,
        help="Choose the financial product to add a valuation entry for.",
    )

    if not selected_product_name:
        return

    product = product_map[selected_product_name]
    currency = product.currency_code or ""

    # Show shortcut to create new product
    with st.expander("Product not listed?"):
        st.markdown(
            "You can create a new financial product in the **Manage Entities** section."
        )
        if st.button("Create New Product", key="create_product_shortcut"):
            st.session_state[StateKeys.ENTITY_TAB] = EntityTabs.FINANCIAL_PRODUCTS
            st.session_state[StateKeys.NAV_TO] = Pages.MANAGE_ENTITIES
            st.rerun()

    st.divider()

    # Last entry preview
    render_last_entry_preview(product)

    st.divider()

    # Entry form
    st.subheader("New Entry")

    col1, col2 = st.columns(2)

    with col1:
        entry_date = st.date_input(
            "Date",
            value=date.today(),  # noqa: DTZ011
            max_value=date.today(),  # noqa: DTZ011
            help="Date of the valuation entry.",
        )

    with col2:
        value_input = st.text_input(
            f"Current Value ({currency})",
            placeholder="0.00",
            help="Total current value of your holding.",
        )

    # Optional fields for units and unit value
    col3, col4 = st.columns(2)

    with col3:
        units_input = st.text_input(
            "Units (optional)",
            placeholder="0.0000",
            help="Number of units/shares held.",
        )

    with col4:
        unit_value_input = st.text_input(
            f"Unit Value ({currency}, optional)",
            placeholder="0.00",
            help="Value per unit/share.",
        )

    # Parse and validate inputs
    current_value: Decimal | None = None
    units_value: Decimal | None = None
    unit_value: Decimal | None = None

    if value_input:
        try:
            current_value = Decimal(value_input.replace(",", ""))
        except InvalidOperation:
            st.error("Please enter a valid number for current value.")

    if units_input:
        try:
            units_value = Decimal(units_input.replace(",", ""))
        except InvalidOperation:
            st.error("Please enter a valid number for units.")

    if unit_value_input:
        try:
            unit_value = Decimal(unit_value_input.replace(",", ""))
        except InvalidOperation:
            st.error("Please enter a valid number for unit value.")

    # Show delta preview for current entry date against DB/batch
    if current_value is not None:
        # Determine preceding value for entry_date
        with get_session() as session:
            repo = ProductValueRepository(session)
            latest_before = repo.get_latest_before(product.id, entry_date)

        batch = st.session_state.get(StateKeys.VALUATION_BATCH, [])
        product_batch_before = [
            e for e in batch if e["product_id"] == product.id and e["date"] < entry_date
        ]

        if product_batch_before:
            product_batch_before.sort(key=lambda x: x["date"])
            previous_value = product_batch_before[-1]["current_value"]
        elif latest_before:
            previous_value = latest_before.current_value
        else:
            previous_value = None

        render_delta_indicator(current_value, previous_value, currency)

    st.divider()

    # Action buttons
    col_add, col_submit, col_clear = st.columns([1, 1, 1])

    with col_add:
        add_disabled = current_value is None
        if st.button(
            "Add to Batch", disabled=add_disabled, use_container_width=True
        ) and add_to_batch(product, entry_date, current_value, units_value, unit_value):
            st.rerun()

    batch_count = len(st.session_state.get(StateKeys.VALUATION_BATCH, []))

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

    # Render batch table across all products
    render_batch_table()
