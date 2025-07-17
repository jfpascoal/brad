import os

SECRETS_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    os.pardir,
    os.pardir,
    'docker',
    'secrets'
))
