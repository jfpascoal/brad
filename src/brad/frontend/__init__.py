"""
Brad Frontend Module - Streamlit-based user interface for financial data entry.

This module provides a web-based interface for entering account balances,
financial product valuations, and managing entities (accounts, products,
providers, holders).

The frontend is designed to integrate with the brad.sql data services layer,
abstracting database operations from the UI components.
"""

from brad.frontend.app import run_app

__all__ = ['run_app']
