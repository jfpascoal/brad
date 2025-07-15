import sys
from bread.sql.database import DatabaseManager


def run():
    db = DatabaseManager()
    db.initialize_schema(force=True)

if __name__ == "__main__":
    run()
    sys.exit(0)
