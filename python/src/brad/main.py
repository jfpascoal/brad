import argparse
import logging
import sys
from typing import List, Dict, Tuple, Any

from brad.sql.database import DatabaseManager
from brad.sql.schema import create_schema

logger = logging.getLogger(__name__)


class MethodOptions:
    """Represents command line options for a method."""

    def __init__(self, opts: Dict[str, Tuple[List[str], Any, str]]):
        """Initialize with option specifications: {attr: ([flags], type, desc)}."""
        self.opts = opts
        self.flag_map = {flag: key for key, (flags, _, _) in opts.items() for flag in flags}
        for attr, (_, typ, _) in opts.items():
            setattr(self, attr, typ())

    def flag_list(self) -> List[str]:
        """Return list of valid flags."""
        return list(self.flag_map.keys())

    def valid_opts(self) -> str:
        """Return string representation of valid options."""
        options = []
        for flags, _, desc in self.opts.values():
            option = ',\t'.join(flags)
            options.append(f"{option}: {desc}")
        return '\n'.join(options)

    def set(self, input_opts: List[str]):
        """
        Set options as attributes based on command line input.
        
        :param input_opts: List of command line option strings to process.
        """
        active_opt = None
        for opt in input_opts:
            # Check if the option is a valid flag or value
            if opt.startswith('-') and opt not in self.flag_list():
                logger.warning(f"Unknown option '{opt}'.")
            elif opt.startswith('-'):
                # If it's a flag, set the corresponding attribute to True
                if isinstance(getattr(self, self.flag_map[opt]), bool):
                    setattr(self, self.flag_map[opt], True)
                # If it's a value, set the last active option
                else:
                    active_opt = self.flag_map[opt]
            else:
                # If it's a value, set it to the last active option
                if active_opt is not None:
                    typ = self.opts[active_opt][1]
                    setattr(self, active_opt, typ(opt))
                    active_opt = None
                else:
                    logger.warning(f"Value '{opt}' without a preceding option.")


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments for the Brad application.
    
    :return: Parsed command line arguments as an argparse.Namespace object.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('method', choices=['db_init'], help="Method to run")
    parser.add_argument('options', nargs=argparse.REMAINDER, help="Additional options for the method")
    return parser.parse_args()


def initialize_db(options: List[str]) -> DatabaseManager:
    """
    Initializes the PostgreSQL database schema with optional seeding.
    
    :param options: Command line options for database initialization:
                   - '-f', '--force': Drop and recreate all tables
                   - '--no-seed': Skip seeding data (default is to seed data)
    :return: A configured DatabaseManager instance
    """
    valid_options = MethodOptions({
        'force': (['-f', '--force'], bool, "Drop and recreate all tables"),
        'no_seed': (['--no-seed'], bool, "Skip seeding data")
    })

    valid_options.set(options)
    db = DatabaseManager()
    create_schema(db, force=valid_options.force, seed=(not valid_options.no_seed))
    return db


if __name__ == "__main__":

    logging.basicConfig(filename="python/logs/brad.log", level=logging.INFO)
    logger.info("\n _                _ "
                "\n| |__ _ _ __ _ __| |"
                "\n| '_ \\ '_/ _` / _` |"
                "\n|_.__/_| \\__,_\\__,_|")

    args = parse_args()
    if args.method == 'db_init':
        logger.info("Initializing database...")
        initialize_db(args.options)
    else:
        logger.error(f"Unknown method: {args.method}")
        logging.shutdown()
        sys.exit(1)

    logger.info("All done.")
    logging.shutdown()
    sys.exit(0)
