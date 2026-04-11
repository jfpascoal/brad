import logging
from pathlib import Path

import click

from brad.core.config import get_settings

logger = logging.getLogger(__name__)


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
def cli(verbose: bool) -> None:
    """brad — personal finance data management."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )


@cli.group()
def db() -> None:
    """Database management commands."""
    pass


@db.command()
def init() -> None:
    """Create all database tables."""
    import brad.core.models.operational  # noqa: F401
    import brad.core.models.reference  # noqa: F401
    from brad.core.db import get_engine
    from brad.core.models.base import Base

    click.echo("Creating tables...")
    Base.metadata.create_all(get_engine())
    click.echo("[OK] All tables created.")


@db.command()
@click.option(
    "--seed-dir",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to seed data directory (default: data/seed)",
)
def seed(seed_dir: Path | None) -> None:
    """Populate the database with initial historical data."""
    from brad.core.db import get_session_factory
    from brad.services.seeding import seed_all

    settings = get_settings()
    if seed_dir is None:
        seed_dir = settings.seed_dir

    SessionLocal = get_session_factory()
    click.echo(f"Seeding initial data from {seed_dir}...")
    with SessionLocal() as session:
        try:
            results = seed_all(session, seed_dir)
            session.commit()
            for name, count in results.items():
                click.echo(f"  {name}: {count} records")
            click.echo("[OK] Initial data population complete.")
        except Exception as e:
            session.rollback()
            click.echo(f"[ERROR] Seeding failed: {e}", err=True)
            raise click.Abort()


@db.command()
@click.option(
    "--history-file",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to Excel history file (default: data/excel/historical.ods)",
)
def ingest(history_file: Path | None) -> None:
    """Ingest historical account and product data from Excel."""
    from brad.core.db import get_session_factory
    from brad.services.ingestion import ingest_from_excel

    settings = get_settings()
    if history_file is None:
        history_file = settings.data_dir / "excel" / "historical.ods"

    SessionLocal = get_session_factory()
    click.echo(f"Ingesting data from {history_file}...")
    with SessionLocal() as session:
        try:
            results = ingest_from_excel(session, history_file)
            session.commit()
            for name, count in results.items():
                click.echo(f"  {name}: {count} records inserted/updated")
            click.echo("[OK] Ingestion complete.")
        except Exception as e:
            session.rollback()
            click.echo(f"[ERROR] Ingestion failed: {e}", err=True)
            raise click.Abort()


@db.command()
@click.confirmation_option(prompt="This will drop and recreate all tables. Continue?")
def reset() -> None:
    """Drop all tables, recreate, and re-seed initial data."""
    import brad.core.models.operational  # noqa: F401
    import brad.core.models.reference  # noqa: F401
    from brad.core.db import get_engine, get_session_factory
    from brad.core.models.base import Base
    from brad.services.seeding import seed_all

    settings = get_settings()
    engine = get_engine()

    click.echo("Dropping all tables...")
    Base.metadata.drop_all(engine)

    click.echo("Creating tables...")
    Base.metadata.create_all(engine)

    SessionLocal = get_session_factory()
    click.echo(f"Seeding initial data from {settings.seed_dir}...")
    with SessionLocal() as session:
        try:
            results = seed_all(session, settings.seed_dir)
            session.commit()
            for name, count in results.items():
                click.echo(f"  {name}: {count} records")
            click.echo("[OK] Reset and population complete.")
        except Exception as e:
            session.rollback()
            click.echo(f"[ERROR] Reset failed: {e}", err=True)
            raise click.Abort()


@cli.command()
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file path",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["custom", "plain"]),
    default="custom",
    help="pg_dump format",
)
def backup(output: Path | None, fmt: str) -> None:
    """Create a database backup using pg_dump."""
    from brad.services.backup import backup_database

    path = backup_database(output_path=output, fmt=fmt)
    click.echo(f"[OK] Backup created: {path}")


@cli.command()
@click.argument("backup_path", type=click.Path(exists=True, path_type=Path))
def restore(backup_path: Path) -> None:
    """Restore database from a backup file."""
    from brad.services.backup import restore_database

    restore_database(backup_path)
    click.echo("[OK] Database restored.")


@cli.command()
@click.option(
    "--port",
    type=int,
    default=8501,
    help="Port to run the Streamlit server on",
)
def frontend(port: int) -> None:
    """Launch the Streamlit frontend application."""
    import subprocess
    import sys

    frontend_app_path = Path(__file__).parent / "frontend" / "app.py"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(frontend_app_path),
        "--server.port",
        str(port),
    ]

    click.echo(f"Launching frontend on port {port}...")
    try:
        # We merge env variables to keep PATH intact as per AGENTS.md Gotchas!
        import os
        env = {**os.environ}
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        click.echo("\n✓ Frontend stopped.")


if __name__ == "__main__":
    cli()
