from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from brad.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_help_without_db_config(runner):
    """Verify `brad --help` works without any database configuration."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "personal finance data management" in result.output


def test_cli_db_group_help(runner):
    """Verify `brad db --help` lists subcommands."""
    result = runner.invoke(cli, ["db", "--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "seed" in result.output


@patch("brad.core.db.get_engine")
@patch("brad.core.models.base.Base.metadata")
def test_cli_db_init(mock_meta, mock_get_engine, runner):
    """Test db init creates tables via the engine."""
    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine

    result = runner.invoke(cli, ["db", "init"])

    assert result.exit_code == 0
    assert "tables created" in result.output


@patch("brad.services.backup.backup_database")
def test_cli_backup(mock_backup, runner):
    """Verify backup command delegates to the service."""
    mock_backup.return_value = "fake/path/backup.dump"
    result = runner.invoke(cli, ["backup"])

    assert result.exit_code == 0
    assert "Backup created" in result.output
    mock_backup.assert_called_once()
