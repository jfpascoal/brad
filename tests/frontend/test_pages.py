"""
Headless component integration tests for frontend page modules.

Tests balance entry, valuation entry, and entity management components
using Streamlit's official AppTest framework and test database sessions.
"""

import os
import unittest
from pathlib import Path

# Ensure HOME environment variable is set for Streamlit config loading on Windows
if "HOME" not in os.environ and "USERPROFILE" in os.environ:
    os.environ["HOME"] = os.environ["USERPROFILE"]

from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool
from streamlit.testing.v1 import AppTest

import brad.core.models.operational
import brad.core.models.reference  # noqa: F401
from brad.core.models.base import Base
from brad.core.models.operational import Holder, Provider
from brad.core.models.reference import AccountType, ProductType
from brad.frontend.constants import Pages, StateKeys
from brad.repositories.base import BaseRepository


class TestStreamlitPages(unittest.TestCase):
    """Headless component tests for frontend pages."""

    def setUp(self):
        """Setup in-memory database engine and session factory fixture."""
        self.app_path = str(
            Path(__file__).resolve().parents[2] / "src" / "brad" / "frontend" / "app.py"
        )
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.engine_patcher = patch("brad.core.db.get_engine", return_value=self.engine)
        self.engine_patcher.start()

        self.session_factory = scoped_session(
            sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        )

        # Populate reference data needed by entity forms
        with self.session_factory() as session:
            BaseRepository(session, AccountType).create(
                AccountType(id=1, name="Current Account")
            )
            BaseRepository(session, ProductType).create(
                ProductType(id=1, name="Equity ETF")
            )
            BaseRepository(session, Provider).create(
                Provider(id=1, name="Vanguard", country="GB")
            )
            BaseRepository(session, Holder).create(
                Holder(id=1, name="Jane Doe", tax_bracket="Basic")
            )
            session.commit()

    def tearDown(self):
        """Stop engine mock after test."""
        self.engine_patcher.stop()

    def test_entity_management_page_render(self):
        """Test rendering Manage Entities page and tab navigation."""
        at = AppTest.from_file(self.app_path).run()
        self.assertFalse(at.exception)

        # Select Manage Entities page
        at.sidebar.radio[0].set_value(Pages.MANAGE_ENTITIES).run()
        self.assertFalse(at.exception)

    def test_balance_entry_warning_when_no_accounts(self):
        """Test that Add Balance page displays warning when no active accounts exist."""
        at = AppTest.from_file(self.app_path).run()
        self.assertFalse(at.exception)

        # Balance page default view without accounts shows warning
        self.assertTrue(len(at.warning) > 0)
        self.assertIn("No accounts found", at.warning[0].value)

        # Clicking 'Go to Entity Management' updates state to 'Manage Entities'
        at.button[0].click().run()
        self.assertFalse(at.exception)
        self.assertEqual(
            Pages.MANAGE_ENTITIES, at.session_state[StateKeys.NAVIGATION_PAGE]
        )


if __name__ == "__main__":
    unittest.main()
