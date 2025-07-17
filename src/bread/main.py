import argparse
import sys
from typing import List

from bread.sql.database import DatabaseManager


def parse_args() -> argparse.Namespace:
    """
    Parses command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('method', choices=['initialize_db'], help="Method to run")
    parser.add_argument('options', nargs=argparse.REMAINDER, help="Additional options for the method")
    return parser.parse_args()


def initialize_db(options: List[str]):
    """
    Initialize the PostgreSQL database schema and seed data.
    """
    db = DatabaseManager()
    db.initialize_schema(force=('-f' in options or '--force' in options))


if __name__ == "__main__":
    args = parse_args()
    if args.method == 'initialize_db':
        initialize_db(args.options)
    else:
        print(f"Unknown method: {args.method}")
    sys.exit(0)
