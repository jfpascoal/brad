import logging
import subprocess
from pathlib import Path

from brad.core.config import get_settings

logger = logging.getLogger(__name__)


def backup_database(output_path: Path | None = None, fmt: str = "custom") -> Path:
    """Create a database backup using pg_dump.

    Args:
        output_path: Where to write the backup file. Defaults to
            ``<backup_dir>/brad_backup.dump``.
        fmt: pg_dump format — ``custom`` (default, compressed) or ``plain`` (SQL text).

    Returns:
        Path to the created backup file.
    """
    settings = get_settings()

    if output_path is None:
        ext = ".sql" if fmt == "plain" else ".dump"
        output_path = settings.backup_dir / f"brad_backup{ext}"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "pg_dump",
        f"--host={settings.postgres_host}",
        f"--port={settings.postgres_port}",
        f"--username={settings.postgres_user}",
        f"--dbname={settings.postgres_db}",
        f"--format={fmt[0]}",  # 'c' for custom, 'p' for plain
        f"--file={output_path}",
    ]

    env = {"PGPASSWORD": settings.postgres_password}

    logger.info(f"Running pg_dump → {output_path}")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"pg_dump failed: {result.stderr}")
        raise RuntimeError(f"pg_dump failed: {result.stderr}")

    logger.info(f"Backup created: {output_path} ({output_path.stat().st_size} bytes)")
    return output_path


def restore_database(backup_path: Path) -> None:
    """Restore a database from a pg_dump backup.

    Args:
        backup_path: Path to the ``.dump`` (custom format) or ``.sql`` (plain) file.
    """
    settings = get_settings()

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    if backup_path.suffix == ".sql":
        cmd = [
            "psql",
            f"--host={settings.postgres_host}",
            f"--port={settings.postgres_port}",
            f"--username={settings.postgres_user}",
            f"--dbname={settings.postgres_db}",
            f"--file={backup_path}",
        ]
    else:
        cmd = [
            "pg_restore",
            f"--host={settings.postgres_host}",
            f"--port={settings.postgres_port}",
            f"--username={settings.postgres_user}",
            f"--dbname={settings.postgres_db}",
            "--clean",
            "--if-exists",
            str(backup_path),
        ]

    env = {"PGPASSWORD": settings.postgres_password}

    logger.info(f"Restoring from {backup_path}")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"Restore failed: {result.stderr}")
        raise RuntimeError(f"Restore failed: {result.stderr}")

    logger.info("Database restored successfully")
