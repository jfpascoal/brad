"""Shared utility helpers used across services."""

from pathlib import Path

import yaml


def load_yaml(path: Path) -> list[dict]:
    """Load a YAML file and return its contents as a list.

    Returns an empty list if the file does not exist or is empty.
    """
    if not path.exists():
        return []
    with open(path) as f:
        data = yaml.safe_load(f)
    return data if data else []
