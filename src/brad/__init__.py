import os

ROOT_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    os.path.pardir,
    os.path.pardir
))

DATA_DIR = os.path.join(ROOT_DIR, 'data')
BACKUP_DIR = os.path.join(DATA_DIR, 'backup')
CONFIG_DIR = os.path.join(ROOT_DIR, 'config')

SECRETS_DIR = os.path.abspath(os.path.join(
    ROOT_DIR,
    'docker',
    'secrets'
))
