import json
import logging
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any

from brad import BACKUP_DIR
from brad.data.encryption import encrypt_string, decrypt_string
from brad.data.reference import REFERENCE_PATH, get_history_transactions, remove_historical_attributes
from brad.sql.objects import Row
from brad.sql.schema import TABLES
from brad.sql.database import DatabaseManager

logger = logging.getLogger(__name__)


def _create_type_map(value: Any, path: str = "") -> Dict[str, str]:
    """
    Recursively analyze a nested data structure and create a map of paths to type names.
    Only tracks types that JSON cannot natively serialize, i.e., datetime and Decimal.
    
    For example, a structure like:
    {'accounts': [{'date': datetime(2024,1,1), 'amount': Decimal('100.50'), 'name': 'Account1'}]}
    
    Would produce a type map like:
    {
        'accounts[].date': 'datetime',
        'accounts[].amount': 'Decimal'
        # 'name' is omitted as str is JSON-native
    }
    
    :param value: The data structure to analyze (can be dict, list, or primitive)
    :param path: The current path in the structure (used for recursion, starts empty)
    :return: Dictionary mapping dotted/bracketed paths to non-JSON-serializable type names
    """
    # Types that JSON cannot natively serialize
    NON_JSON_TYPES = {datetime, Decimal}
    type_map = {}

    if isinstance(value, dict):
        for key, val in value.items():
            current_path = f"{path}.{key}" if path else key
            type_map.update(_create_type_map(val, current_path))
    elif isinstance(value, list):
        if value:  # If not empty, analyze first element only
            element_path = f"{path}[]"
            # Only record element type if it's non-JSON-serializable
            if type(value[0]) in NON_JSON_TYPES:
                type_map[element_path] = type(value[0]).__name__
            # Recursively analyze first element for nested structures
            type_map.update(_create_type_map(value[0], element_path))
    else:
        # Leaf value - only record if it's a non-JSON-serializable type
        if type(value) in NON_JSON_TYPES:
            type_map[path] = type(value).__name__

    return type_map


def _serialize_to_json(data: Dict[str, Any], metadata: Dict[str, str]) -> str:
    """
    Add metadata to data structure and serialize it to JSON. Metadata includes typemap
    to enable restoration of non-JSON-serializable types.
    
    :param data: Dictionary with data to be serialized.
    :param metadata: Dictionary with metadata to include in the JSON
    :return: JSON string with metadata included.
    """

    type_map = _create_type_map(data)
    backup_metadata = {
        "version": "0.1",
        "timestamp": metadata.get('timestamp') or datetime.now().isoformat(),
        "source": metadata.get('source'),
        "file_name": metadata.get('file_name'),
        "type_map": type_map
    }

    return json.dumps(
        {
            "data": data,
            "_metadata": backup_metadata
        },
        ensure_ascii=False,
        default=str
    )


def _restore_types(data: Any, type_map: Dict[str, str], path: str = "") -> Any:
    """
    Restore original types of non-JSON-serializable types based on the type map.
    Supports Decimal and datetime.
    
    :param data: The data to restore
    :param type_map: Map of paths to non-JSON-serializable type names
    :param path: Current path in the data structure
    :return: Data with restored types
    """
    # Check if path needs type conversion
    if path in type_map:
        target_type = type_map[path]
        if target_type == "Decimal":
            return Decimal(str(data)) if data is not None else None
        elif target_type == "datetime":
            return datetime.fromisoformat(data) if data else None

    # Recursively process dictionaries and lists
    if isinstance(data, dict):
        return {key: _restore_types(value, type_map, f"{path}.{key}" if path else key)
                for key, value in data.items()}
    elif isinstance(data, list):
        element_path = f"{path}[]"
        return [_restore_types(item, type_map, element_path) for item in data]

    return data


def backup_data(backup_file_name: str, data: dict, source: str = None, fmt: str = "json", encrypt: bool = False) \
        -> None:
    """
    Create a backup of the provided data in the specified format.
    
    :param backup_file_name: Name of the backup file to create (without extension)
    :param data: Dictionary with data to be backed up.
    :param source: Source of the data. Defaults to None.
    :param fmt: "json" or "binary" - determines file format
    :param encrypt: Whether to encrypt (only applicable for binary format). Defaults to False.
    :raises ValueError: If format specified is unsupported.
    """
    if fmt not in {"json", "binary"}:
        raise ValueError(f"Unsupported format: '{fmt}'. Supported formats are 'json' and 'binary'.")

    json_data = _serialize_to_json(data, metadata={"source": source, "file_name": backup_file_name})

    extension = ".json" if fmt == "json" else ".b" if fmt == "binary" else ""
    file_path = os.path.join(BACKUP_DIR, backup_file_name) + extension
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if os.path.exists(file_path):
        logger.warning(f"Backup file '{file_path}' already exists and will be overwritten.")

    match fmt:
        case "json":
            try:
                with open(file_path, "w") as f:
                    f.write(json_data)
                logger.info(f"JSON backup created successfully at '{file_path}'.")

            except Exception as e:
                logger.error(f"Failed to create JSON backup: {e}")
                raise

        case "binary":
            try:
                if encrypt:
                    # Encrypt the JSON string
                    binary_data = encrypt_string(json_data)
                else:
                    # Store as plain text bytes
                    binary_data = json_data.encode('utf-8')

                with open(file_path, "wb") as f:
                    f.write(binary_data)

                logger.info(f"{'Encrypted' if encrypt else 'Binary'} backup created successfully at '{file_path}'.")

            except Exception as e:
                logger.error(f"Failed to create binary backup: {e}")
                raise


def load_backup_file(file_path: str) -> Dict[str, Any]:
    """
    Load backup data from a file, automatically detecting format based on extension.
    
    :param file_path: Path to back up file (.json or .b)
    :return: Raw backup data (with metadata structure)
    :raises ValueError: If file format is unsupported or decryption fails
    :raises FileNotFoundError: If the backup file is not found
    """
    try:
        if file_path.endswith('.json'):
            with open(file_path, "r") as f:
                return json.load(f)

        elif file_path.endswith('.b'):
            with open(file_path, "rb") as f:
                raw_data = f.read()

            # Try to decrypt first, fall back to plain text if decryption fails
            try:
                json_string = decrypt_string(raw_data)
            except Exception:
                # If decryption fails, try as plain text
                try:
                    json_string = raw_data.decode('utf-8')
                except UnicodeDecodeError:
                    raise ValueError("Binary file is neither encrypted nor valid UTF-8 text")

            return json.loads(json_string)

        else:
            raise ValueError(f"Unsupported file format: {file_path}.")

    except FileNotFoundError:
        logger.error(f"Backup file not found at: {file_path}")
        raise
    except Exception as e:
        msg = f"Failed to load backup file '{file_path}': {e}"
        logger.error(msg)
        raise ValueError(msg)


def restore_backup(file_path: str, db: DatabaseManager) -> Dict[str, Any]:
    """
    Restore data from backup file.
    
    :param file_path: Path to back up file (.json or .b)
    :param db: An instance of DatabaseManager to write restored data to the database.
    :return: Restored data with original types
    :raises ValueError: If file format is unsupported or restoration fails
    :raises FileNotFoundError: If the backup file is not found
    """
    try:
        # Load raw backup data
        backup_data = load_backup_file(file_path)

        # Restore types using metadata
        data = backup_data.get("data", {})
        type_map = backup_data.get("_metadata", {}).get("type_map", {})

        restored_data = _restore_types(data, type_map)
        write_to_db(db=db, data=restored_data)
        logger.info(f"Data restored successfully from '{file_path}'.")
        return restored_data

    except Exception as e:
        logger.error(f"Error restoring from backup file: {e}")
        raise


def get_reference_data(with_history_transactions: bool) -> Dict[str, Dict[str, Any]]:
    """
    Retrieve reference data from backup file. Returns data as dictionary
    
    :param with_history_transactions: Whether to include historical transactions in the restored data.
    :return: Reference data with original types.
    """
    logger.info(f"Loading reference data from file '{REFERENCE_PATH}'")
    reference = load_backup_file(REFERENCE_PATH)
    data = reference.get("data", {})
    type_map = reference.get("_metadata", {}).get("type_map", {})
    
    reference_data = _restore_types(data, type_map)
    if with_history_transactions:
        logger.info("Getting historical transactions from reference data.")
        history_transactions = get_history_transactions(reference_data)
        reference_data.update(history_transactions)

    reference_data = remove_historical_attributes(reference_data)
    return reference_data


def write_to_db(db: DatabaseManager, data: List[Dict[str, Any]]) -> None:
    """
    Write processed data to the database.

    :param db: An instance of DatabaseManager to interact with the database.
    :param data: List of dictionaries containing data to insert.
    """
    with db.get_connection() as conn:
        for table_name, tbl in TABLES.items():
            tbl_data = data.get(table_name, [])
            if not tbl_data:
                logger.debug(f"No data to insert in table '{table_name}'.")
                continue
            logger.info(f"Inserting {len(tbl_data)} records into table '{table_name}'.")
            tbl.insert(conn, [Row(row) for row in tbl_data])
