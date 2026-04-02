from pathlib import Path
from unittest.mock import patch, mock_open

from brad.services.seeding import _load_yaml


def test_load_yaml_parses_content():
    """Ensure YAML content is correctly parsed."""
    mock_yaml = "- name: Test Currency\n  code: TST"

    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_yaml)):
            results = _load_yaml(Path("currencies.yaml"))
            assert len(results) == 1
            assert results[0]["code"] == "TST"


def test_load_yaml_empty_file():
    """Ensure empty YAML files return an empty list."""
    with patch("builtins.open", mock_open(read_data="")):
        results = _load_yaml(Path("empty.yaml"))
        assert results == []
