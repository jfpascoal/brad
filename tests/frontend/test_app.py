"""
Headless integration tests for the main Streamlit application entry point.

Uses Streamlit's official AppTest framework to verify layout,
navigation radio selection, and page routing without launching a browser.
"""

import os
import unittest
from pathlib import Path

# Ensure HOME environment variable is set for Streamlit config loading on Windows
if "HOME" not in os.environ and "USERPROFILE" in os.environ:
    os.environ["HOME"] = os.environ["USERPROFILE"]

from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from streamlit.testing.v1 import AppTest

import brad.core.models.operational
import brad.core.models.reference  # noqa: F401
from brad.core.models.base import Base
from brad.frontend.constants import Pages, StateKeys


class TestStreamlitApp(unittest.TestCase):
    """Headless integration tests for brad.frontend.app."""

    def setUp(self):
        """Locate app.py and setup in-memory database engine mock."""
        self.app_path = str(
            Path(__file__).resolve().parents[2] / "src" / "brad" / "frontend" / "app.py"
        )
        self.test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.test_engine)
        self.engine_patcher = patch(
            "brad.core.db.get_engine", return_value=self.test_engine
        )
        self.engine_patcher.start()

    def tearDown(self):
        """Stop engine mock after test."""
        self.engine_patcher.stop()

    def test_app_initialization_and_default_page(self):
        """Test launching app.py headlessly and verifying default state."""
        at = AppTest.from_file(self.app_path).run()
        self.assertFalse(
            at.exception, f"App threw unexpected exception: {at.exception}"
        )

        # Verify sidebar title and navigation radio
        self.assertTrue(len(at.sidebar.radio) > 0)
        nav_radio = at.sidebar.radio[0]
        self.assertEqual(Pages.ADD_BALANCE, nav_radio.value)

    def test_navigation_between_pages(self):
        """Test switching navigation options headlessly."""
        at = AppTest.from_file(self.app_path).run()
        self.assertFalse(at.exception)

        # Switch to 'Manage Entities'
        at.sidebar.radio[0].set_value(Pages.MANAGE_ENTITIES).run()
        self.assertFalse(at.exception)
        self.assertEqual(
            Pages.MANAGE_ENTITIES, at.session_state[StateKeys.NAVIGATION_PAGE]
        )

        # Switch to 'Add Valuation'
        at.sidebar.radio[0].set_value(Pages.ADD_VALUATION).run()
        self.assertFalse(at.exception)
        self.assertEqual(
            Pages.ADD_VALUATION, at.session_state[StateKeys.NAVIGATION_PAGE]
        )


if __name__ == "__main__":
    unittest.main()
