import json
import os

import yaml

from brad import DATA_DIR, BACKUP_DIR

HISTORY_FILE = os.path.join(DATA_DIR, "excel", "historical.ods")

with open(os.path.join(DATA_DIR, "excel", "tabs.yaml"), 'rb') as f:
    TABS = yaml.load(f.read(), Loader=yaml.Loader)

with open(os.path.join(BACKUP_DIR, "reference.json"), 'rb') as f:
    REFERENCE_DATA = json.load(f)
