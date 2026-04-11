"""
Main Streamlit application for Brad frontend.

This module serves as the entry point for the Streamlit application,
providing navigation and routing to different pages for data entry
and entity management.
"""

import os

import streamlit as st

from brad.core.db import get_session_factory


@st.dialog('Confirm Exit')
def confirm_exit_dialog() -> None:
    """
    Displays a confirmation dialog for exiting the application.

    When confirmed, terminates the Streamlit server process.
    """
    st.write('Are you sure you want to stop the application?')
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Yes, stop', type='primary', use_container_width=True):
            os._exit(0)
    with col2:
        if st.button('Cancel', use_container_width=True):
            st.rerun()


def init_session_state() -> None:
    """
    Initialises Streamlit session state variables.

    Sets up the session factory and any other persistent state needed
    across page navigations and reruns.
    """
    if 'session_factory' not in st.session_state:
        st.session_state.session_factory = get_session_factory()

    # Batch entry state for balances
    if 'balance_batch' not in st.session_state:
        st.session_state.balance_batch = []

    # Batch entry state for valuations
    if 'valuation_batch' not in st.session_state:
        st.session_state.valuation_batch = []


def main() -> None:
    """
    Main application entry point.

    Configures the Streamlit page and renders the navigation sidebar
    with links to different sections of the application.
    """
    st.set_page_config(
        page_title='Brad - Financial Manager',
        page_icon='💰',
        layout='wide',
        initial_sidebar_state='expanded'
    )

    init_session_state()

    st.sidebar.title('Brad')
    st.sidebar.markdown('Financial Management')
    st.sidebar.divider()

    # Navigation
    page = st.sidebar.radio(
        'Navigation',
        options=[
            'Add Balance',
            'Add Valuation',
            'Manage Entities'
        ],
        label_visibility='collapsed'
    )

    # Exit button
    st.sidebar.divider()
    if st.sidebar.button(
        '🛑 Stop Application',
        type='secondary',
        use_container_width=True
    ):
        confirm_exit_dialog()

    # Route to appropriate page
    if page == 'Add Balance':
        from brad.frontend.pages.balance_entry import render_balance_entry_page
        render_balance_entry_page()
    elif page == 'Add Valuation':
        from brad.frontend.pages.valuation_entry import render_valuation_entry_page
        render_valuation_entry_page()
    elif page == 'Manage Entities':
        from brad.frontend.pages.entity_management import render_entity_management_page
        render_entity_management_page()


def run_app() -> None:
    """
    Entry point for running the Streamlit application.

    This function is called from the main.py CLI to launch the frontend.
    """
    main()


if __name__ == '__main__':
    main()
