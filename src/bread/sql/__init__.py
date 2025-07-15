import os

DB_PATH =  os.path.abspath(os.path.join(
    os.path.dirname(__file__), # bread/src/bread/sql
    os.pardir, # bread/src/bread
    os.pardir, # bread/src
    os.pardir, # bread
    os.path.join("data", "bread.db")
))
