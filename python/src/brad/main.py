import argparse
import logging
import sys
from typing import List, Dict, Tuple, Any
from datetime import datetime

from brad.data.history import ingest_from_excel
from brad.data.backup import backup_data, write_to_db, restore_reference_data
from brad.sql.database import DatabaseManager
from brad.sql.schema import create_schema

logger = logging.getLogger(__name__)


class MethodOptions:
    """Represents command line options for a method."""

    def __init__(self, opts: Dict[str, Tuple[List[str], Any, str]]):
        """
        Initialize with option specifications.
        
        :param opts: Dictionary mapping attribute names to tuples of (flags, type, description)
        """
        self._opts = opts
        self._flag_map = {flag: key for key, (flags, _, _) in opts.items() for flag in flags}
        for attr, (_, typ, _) in opts.items():
            setattr(self, attr, typ())

    def flag_list(self) -> List[str]:
        """Return list of valid flags."""
        return list(self._flag_map.keys())

    def valid_opts(self) -> str:
        """Return string representation of valid options."""
        options = []
        for flags, _, desc in self._opts.values():
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
                if isinstance(getattr(self, self._flag_map[opt]), bool):
                    setattr(self, self._flag_map[opt], True)
                # If it's a value-expecting flag, store it for the next value
                else:
                    active_opt = self._flag_map[opt]
            else:
                # If it's a value, set it to the last active option
                if active_opt is not None:
                    typ = self._opts[active_opt][1]
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
    parser.add_argument('method', choices=['db_init', 'load_history'], help="Method to run")
    parser.add_argument('options', nargs=argparse.REMAINDER, help="Additional options for the method")
    return parser.parse_args()


def initialize_db(args: List[str]) -> DatabaseManager:
    """
    Initializes the PostgreSQL database schema with optional seeding.
    
    :param args: Command line options for database initialization:
                   - '-f', '--force': Drop and recreate all tables
                   - '--no-seed': Skip seeding data (default is to seed data)
    :return: A configured DatabaseManager instance
    """
    options = MethodOptions({
        'force': (['-f', '--force'], bool, "Drop and recreate all tables"),
        'no_seed': (['--no-seed'], bool, "Skip seeding data")
    })

    options.set(args)
    db = DatabaseManager()
    create_schema(db, force=options.force, seed=(not options.no_seed))
    return db


def load_history(args: List[str]) -> None:
    """
    Load historical data from an Excel file into the database.
    
    :param args: Command line options for loading history:
                   - '--file': Path to the history Excel file
                   - '--load-reference': Load reference data along with historical data
    """
    options = MethodOptions({
        'history_file': (['--file'], str, "Path to the history Excel file"),
        'load_reference': (['--load-reference'], bool, "Load reference data")
    })

    options.set(args)
    
    db = DatabaseManager()
    if options.load_reference:
        restore_reference_data(db)
    data = ingest_from_excel(history_file=options.history_file)
    write_to_db(db=db, data=data)
    backup_data(backup_file_name='history', data=data, source='excel', fmt='json')


if __name__ == "__main__":

    logging.basicConfig(filename=f"python/logs/brad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                        level=logging.DEBUG)
    logger.info("\n _                _ "
                "\n| |__ _ _ __ _ __| |"
                "\n| '_ \\ '_/ _` / _` |"
                "\n|_.__/_| \\__,_\\__,_|")

    args = parse_args()
    match args.method:
        case 'db_init':
            logger.info("Initializing database...")
            initialize_db(args.options)
        case 'load_history':
            logger.info("Loading historical data into DB...")
            load_history(args.options)
        case _:
            logger.error(f"Unknown method: {args.method}")
            logging.shutdown()
            sys.exit(1)

    logger.info("All done.")
    logging.shutdown()
    sys.exit(0)
