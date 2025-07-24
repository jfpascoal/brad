import os

SECRETS_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__),  # brad/python/src/brad/sql
    os.pardir,  # brad/python/src/brad
    os.pardir,  # brad/python/src
    os.pardir,  # brad/python
    os.pardir,  # brad
    'docker',
    'secrets'
))
