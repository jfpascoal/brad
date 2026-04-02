from unittest.mock import patch, MagicMock

import pytest

from brad.services.backup import backup_database, restore_database


@patch("brad.services.backup.subprocess.run")
def test_backup_database_success(mock_run, tmp_path):
    """Test pg_dump is invoked correctly and PGPASSWORD is merged into env."""
    mock_run.return_value = MagicMock(returncode=0)

    output_file = tmp_path / "brad_backup.dump"
    output_file.touch()  # pg_dump would create this; we simulate it
    output_path = backup_database(output_path=output_file)

    mock_run.assert_called_once()
    _, kwargs = mock_run.call_args
    assert "PGPASSWORD" in kwargs["env"]
    # Verify env was merged (not replaced) — it should contain our mock env vars too
    assert "POSTGRES_DB" in kwargs["env"]
    assert output_path == output_file


@patch("brad.services.backup.subprocess.run")
def test_backup_database_failure(mock_run, tmp_path):
    """Ensure a non-zero exit raises RuntimeError."""
    mock_run.return_value = MagicMock(returncode=1, stderr="Connection refused")

    with pytest.raises(RuntimeError, match="pg_dump failed"):
        backup_database(output_path=tmp_path / "fail.dump")


@patch("brad.services.backup.subprocess.run")
def test_restore_database_success(mock_run, tmp_path):
    """Test pg_restore maps input arguments correctly."""
    mock_run.return_value = MagicMock(returncode=0)

    dummy_backup = tmp_path / "backup.dump"
    dummy_backup.touch()

    restore_database(dummy_backup)

    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    call_str = " ".join(args[0])
    assert "pg_restore" in call_str
    assert "--clean" in call_str
    assert "PGPASSWORD" in kwargs["env"]
