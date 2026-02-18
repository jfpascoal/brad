import os

import yaml

from brad import DATA_DIR, CONFIG_DIR

HISTORY_FILE = os.path.join(DATA_DIR, "excel", "historical.ods")

with open(os.path.join(CONFIG_DIR, "history.yaml"), 'rb') as f:
    config = yaml.load(f.read(), Loader=yaml.SafeLoader)
    TABS = config.get("tabs", {})
    FINANCIAL_PRODUCT_LABELS = config.get("financial_product_labels", {})
