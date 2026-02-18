import json
import os
import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from random import randbytes
from unittest.mock import patch, mock_open, call, MagicMock

from brad.data.backup import (
    _create_type_map,
    _serialize_to_json,
    _restore_types,
    backup_data,
    load_backup_file,
    restore_backup,
    get_reference_data
)
from brad.sql.schema import ACCOUNT_BALANCES, PRODUCT_VALUES, ACCOUNTS, FINANCIAL_PRODUCTS


class TestBackupHelperMethods(unittest.TestCase):
    """Test cases for the backup module with metadata preservation."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_data = {
            ACCOUNT_BALANCES: [
                {"account_name": "foobar", "date": datetime(2023, 1, 1), "amount": Decimal("1000.50")},
                {"account_name": "foobar", "date": datetime(2023, 1, 2), "amount": Decimal("2500.75")}
            ],
            PRODUCT_VALUES: [
                {"product_name": "baz", "date": datetime(2023, 1, 1), "units": Decimal("10.0"),
                 "investment": Decimal("1000.00"), "value": Decimal("1200.00")}
            ]
        }
        self.simple_data = {"string": "hello", "number": 42, "decimal": Decimal("10.5")}

    def test_create_type_map_simple(self):
        """Test type map creation for simple data structures."""
        data = self.simple_data
        type_map = _create_type_map(data)

        expected = {
            "decimal": "Decimal"
        }
        self.assertEqual(expected, type_map)

    def test_create_type_map_list(self):
        """Test type map creation for lists with non-JSON-serializable types."""
        test_data = {"dates": [datetime(2023, 1, 1), datetime(2023, 1, 2)]}
        type_map = _create_type_map(test_data)
        expected = {"dates[]": "datetime"}
        self.assertEqual(expected, type_map)

    def test_create_type_map_nested(self):
        """Test type map creation for nested data structures."""
        type_map = _create_type_map(self.test_data)
        expected = {
            f'{ACCOUNT_BALANCES}[].date': 'datetime',
            f'{ACCOUNT_BALANCES}[].amount': 'Decimal',
            f'{PRODUCT_VALUES}[].date': 'datetime',
            f'{PRODUCT_VALUES}[].units': 'Decimal',
            f'{PRODUCT_VALUES}[].investment': 'Decimal',
            f'{PRODUCT_VALUES}[].value': 'Decimal'
        }
        self.assertEqual(expected, type_map)

    def test_create_type_map_empty(self):
        """Test type map creation for data structures without non-JSON-serializable types."""
        data = {"balances": [{"account_name": "foobar", "date": 20250131, "amount": 1000.50}]}
        type_map = _create_type_map(data)
        expected = {}
        self.assertEqual(expected, type_map)

    def test_serialize_to_json_no_metadata(self):
        """Test serialization with empty metadata."""
        result = _serialize_to_json(self.simple_data, metadata={})
        self.assertIsInstance(result, str)

        deserialized_result = json.loads(result)

        self.assertEqual({"data", "_metadata"}, set(deserialized_result.keys()))

        expected_data = self.simple_data.copy()
        expected_data["decimal"] = str(expected_data["decimal"])
        self.assertEqual(expected_data, deserialized_result["data"])

        self.assertEqual({"version", "timestamp", "source", "file_name", "type_map"},
                         set(deserialized_result["_metadata"].keys()))
        self.assertIsNone(deserialized_result["_metadata"]['source'])
        self.assertIsNone(deserialized_result["_metadata"]['file_name'])
        self.assertEqual({"decimal": "Decimal"}, deserialized_result["_metadata"]['type_map'])

    def test_serialize_to_json_with_metadata(self):
        """Test serialization with metadata."""
        timestamp = datetime.now().isoformat()
        metadata = {
            "source": "tests",
            "file_name": "test_file.json",
            "timestamp": timestamp
        }
        result = _serialize_to_json(self.simple_data, metadata)
        self.assertIsInstance(result, str)

        deserialized_result = json.loads(result)
        expected_metadata = {
            "version": "0.1",
            "timestamp": timestamp,
            "source": "tests",
            "file_name": "test_file.json",
            "type_map": {"decimal": "Decimal"}
        }
        self.assertEqual(expected_metadata, deserialized_result["_metadata"])

    def test_restore_types_decimal(self):
        """Test restoration of Decimal types."""
        type_map = {"value": "Decimal"}
        result = _restore_types("100.50", type_map, "value")

        self.assertIsInstance(result, Decimal)
        self.assertEqual(result, Decimal("100.50"))

    def test_restore_types_datetime(self):
        """Test restoration of datetime types."""
        dt_str = "2023-01-01T12:00:00"
        type_map = {"date": "datetime"}
        result = _restore_types(dt_str, type_map, "date")

        self.assertIsInstance(result, datetime)
        self.assertEqual(result, datetime.fromisoformat(dt_str))


@patch('builtins.open', new_callable=mock_open)
@patch('os.path.exists')
@patch('os.makedirs')
@patch('brad.data.backup._serialize_to_json')
class TestBackupData(unittest.TestCase):
    """Test cases for the backup_data function."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_data = {"data": {"key": "value"}, "_metadata": {"key": "value"}}
        self.serialized_data = json.dumps(self.test_data)
        self.file_name = "test_backup"
        self.metadata = {"source": None, "file_name": self.file_name}

    def test_backup_data_json(self, mock_serialize, mock_makedirs, mock_path_exists, mock_open_file):
        """Test the backup_data function with 'json' format."""
        mock_serialize.return_value = self.serialized_data

        backup_data(self.file_name, self.test_data, fmt="json")

        mock_serialize.assert_called_once_with(self.test_data, metadata=self.metadata)

        # Assert that the directory was created if it didn't exist, and that file path was checked
        # with the correct file name and extension.
        mock_makedirs.assert_called_once()
        mock_path_exists.assert_called_once()
        file_path = mock_path_exists.call_args.args[0]
        self.assertTrue(file_path.endswith(self.file_name + ".json"))

        # Assert that the file was opened in write mode, data was written, and file was closed in the end
        mock_open_file.assert_called_once_with(file_path, 'w')
        self.assertIn(call().write(self.serialized_data), mock_open_file.mock_calls)
        self.assertEqual(call().close(), mock_open_file.mock_calls[-1])

    @patch('brad.data.backup.encrypt_string')
    def test_backup_data_binary(self, mock_encrypt, mock_serialize, mock_makedirs, mock_path_exists, mock_open_file):
        """Test the backup_data function with 'binary' format, without encryption."""

        mock_serialize.return_value = self.serialized_data

        backup_data(self.file_name, self.test_data, fmt="binary", encrypt=False)
        mock_serialize.assert_called_once_with(self.test_data, metadata=self.metadata)

        # Assert that the directory was created if it didn't exist, and that file path was checked
        # with the correct file name and extension.
        mock_makedirs.assert_called_once()
        mock_path_exists.assert_called_once()
        file_path = mock_path_exists.call_args.args[0]
        self.assertTrue(file_path.endswith(self.file_name + ".b"))

        # Assert that data encryption was not called
        mock_encrypt.assert_not_called()

        # Assert that the file was opened in write mode, data was written, and file was closed in the end
        mock_open_file.assert_called_once_with(file_path, 'wb')
        self.assertIn(call().write(self.serialized_data.encode('utf-8')), mock_open_file.mock_calls)
        self.assertEqual(call().close(), mock_open_file.mock_calls[-1])

    @patch('brad.data.backup.encrypt_string')
    def test_back_up_data_encrypted(self, mock_encrypt, mock_serialize, mock_makedirs, mock_path_exists,
                                    mock_open_file):
        """Test the backup_data function with 'binary' format and encryption."""

        mock_serialize.return_value = self.serialized_data
        mock_encrypt.return_value = randbytes(16)  # Simulate encrypted data

        backup_data(self.file_name, self.test_data, fmt="binary", encrypt=True)
        mock_serialize.assert_called_once_with(self.test_data, metadata=self.metadata)

        # Assert that the directory was created if it didn't exist, and that file path was checked
        # with the correct file name and extension.
        mock_makedirs.assert_called_once()
        mock_path_exists.assert_called_once()
        file_path = mock_path_exists.call_args.args[0]
        self.assertTrue(file_path.endswith(self.file_name + ".b"))

        # Assert that data encryption was called
        mock_encrypt.assert_called_once_with(self.serialized_data)

        # Assert that the file was opened in write mode, data was written, and file was closed in the end
        mock_open_file.assert_called_once_with(file_path, 'wb')
        self.assertIn(call().write(mock_encrypt.return_value), mock_open_file.mock_calls)
        self.assertEqual(call().close(), mock_open_file.mock_calls[-1])

    def test_invalid_format(self, mock_serialize, mock_makedirs, mock_path_exists, mock_open_file):
        """Test that ValueError is raised for unsupported formats."""
        with self.assertRaises(ValueError):
            backup_data(self.file_name, self.test_data, fmt="unsupported_format")

        # Ensure no file operations were attempted
        mock_serialize.assert_not_called()
        mock_makedirs.assert_not_called()
        mock_path_exists.assert_not_called()
        mock_open_file.assert_not_called()


class TestRestoreBackup(unittest.TestCase):
    """Test cases for backup restoration."""

    def setUp(self):
        self.test_data = {
            "balances": [
                {"account_name": "foobar", "date": datetime(2023, 1, 1), "amount": Decimal("1000.50")},
                {"account_name": "foobar", "date": datetime(2023, 1, 2), "amount": Decimal("2500.75")}
            ]
        }
        self.metadata = {
            "version": "0.1",
            "timestamp": "2023-01-01T12:00:00",
            "source": "tests",
            "file_name": "test_backup",
            "type_map": {
                "balances[].date": "datetime",
                "balances[].amount": "Decimal"
            }
        }
        self.json_data = json.dumps({
            "_metadata": self.metadata,
            "data": self.test_data
        }, ensure_ascii=False, default=str)
        self.binary_data = self.json_data.encode('utf-8')

    def test_load_backup_file_json(self):
        """Test loading a JSON backup file."""
        file_name = "test_backup.json"

        with patch('builtins.open', mock_open(read_data=self.json_data)) as mock_open_file:
            loaded_data = load_backup_file(file_name)
            mock_open_file.assert_called_once_with(file_name, 'r')
            self.assertEqual(call().close(), mock_open_file.mock_calls[-1])

        self.assertEqual(json.loads(self.json_data), loaded_data)

    @patch('brad.data.backup.decrypt_string')
    def test_load_backup_file_binary(self, mock_decrypt):
        """Test loading a binary backup file with no encryption."""
        file_name = "test_backup.b"
        mock_decrypt.side_effect = Exception()

        with patch('builtins.open', mock_open(read_data=self.binary_data)) as mock_open_file:
            loaded_data = load_backup_file(file_name)
            mock_open_file.assert_called_once_with(file_name, 'rb')
            self.assertEqual(call().close(), mock_open_file.mock_calls[-1])

        mock_decrypt.assert_called_once_with(self.binary_data)
        self.assertEqual(json.loads(self.json_data), loaded_data)

    @patch('brad.data.backup.decrypt_string')
    def test_load_backup_file_binary_encrypted(self, mock_decrypt):
        """Test loading a binary backup file with encryption."""
        file_name = "test_backup.b"
        mock_decrypt.return_value = self.binary_data

        with patch('builtins.open', mock_open(read_data=self.binary_data)) as mock_open_file:
            loaded_data = load_backup_file(file_name)
            mock_open_file.assert_called_once_with(file_name, 'rb')
            self.assertEqual(call().close(), mock_open_file.mock_calls[-1])

        mock_decrypt.assert_called_once_with(self.binary_data)
        self.assertEqual(json.loads(self.json_data), loaded_data)

    def test_load_backup_file_invalid_format(self):
        """Test loading a backup file with unsupported format."""
        file_name = "test_backup.txt"
        with self.assertRaises(ValueError):
            load_backup_file(file_name)

    @patch('builtins.open', side_effect=FileNotFoundError("File not found"))
    def test_load_backup_file_not_found(self, mock_open_file):
        """Test loading a backup file that does not exist."""
        file_name = "non_existent_file.json"
        with self.assertRaises(FileNotFoundError):
            load_backup_file(file_name)

    @patch('builtins.open', new_callable=mock_open, read_data=b'\x80\x81\x82')
    @patch('brad.data.backup.decrypt_string', side_effect=Exception())
    def test_load_backup_file_binary_decode_error(self, mock_open_file, mock_decrypt):
        """Test loading a binary backup file that cannot be decoded."""
        file_name = "test_backup.b"
        with self.assertRaises(ValueError):
            load_backup_file(file_name)

    @patch('brad.data.backup._restore_types')
    @patch('brad.data.backup.load_backup_file')
    def test_restore_backup(self, mock_load, mock_restore):
        """Test restoring a backup file."""

        file_name = "test_backup.json"
        mock_db = MagicMock()
        mock_load.return_value = json.loads(self.json_data)
        mock_restore.return_value = self.test_data

        restored_data = restore_backup(file_name, mock_db)

        mock_load.assert_called_once_with(file_name)
        mock_restore.assert_called_once_with(mock_load.return_value["data"],
                                             mock_load.return_value["_metadata"]["type_map"])
        self.assertEqual(self.test_data, restored_data)


class TestBackupRoundTrip(unittest.TestCase):
    """Test cases for complete backup and restore roundtrip."""

    def setUp(self):
        self.test_data = {
            ACCOUNT_BALANCES: [
                {"account_name": "foobar", "date": datetime(2023, 1, 1), "amount": Decimal("1000.50")},
                {"account_name": "foobar", "date": datetime(2023, 1, 2), "amount": Decimal("2500.75")}
            ],
            PRODUCT_VALUES: [
                {"product_name": "baz", "date": datetime(2023, 1, 1), "units": Decimal("10.0"),
                 "investment": Decimal("1000.00"), "value": Decimal("1200.00")}
            ]
        }
        self.test_file_name = "test_roundtrip"

    def test_roundtrip_json_backup_restore(self):
        """Test complete roundtrip: backup to JSON then restore."""
        # Create temporary directory for test
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_path = os.path.join(temp_dir, "balances")

            with patch('brad.data.backup.BACKUP_DIR', backup_path):
                # Backup data
                backup_data(self.test_file_name, self.test_data, fmt="json")

                # Restore data
                backup_file_path = os.path.join(backup_path, self.test_file_name + ".json")
                mock_db = MagicMock()
                restored_data = restore_backup(backup_file_path, mock_db)

                # Verify data integrity
                self.assertEqual(self.test_data, restored_data)

    @patch('brad.data.backup.decrypt_string')
    @patch('brad.data.backup.encrypt_string')
    def test_roundtrip_binary_backup_restore(self, mock_encrypt, mock_decrypt):
        """Test complete roundtrip: backup to binary without encryption and then restore."""
        mock_decrypt.side_effect = Exception()

        with tempfile.TemporaryDirectory() as temp_dir:
            backup_path = os.path.join(temp_dir, "balances")

            with patch('brad.data.backup.BACKUP_DIR', backup_path):
                backup_data(self.test_file_name, self.test_data, fmt="binary", encrypt=False)

                backup_file_path = os.path.join(backup_path, self.test_file_name + ".b")
                mock_db = MagicMock()
                restored_data = restore_backup(backup_file_path, mock_db)

        mock_encrypt.assert_not_called()
        self.assertEqual(self.test_data, restored_data)

    @patch('brad.data.backup.decrypt_string')
    @patch('brad.data.backup.encrypt_string')
    def test_roundtrip_binary_backup_restore_encrypted(self, mock_encrypt, mock_decrypt):
        """Test complete roundtrip: backup to binary with encryption and then restore."""

        source = "tests"

        json_with_metadata = json.dumps({
            "data": self.test_data,
            "_metadata": {
                "version": "0.1",
                "timestamp": datetime.now().isoformat(),
                "source": source,
                "file_name": self.test_file_name,
                "type_map": {
                    f"{ACCOUNT_BALANCES}[].date": "datetime",
                    f"{ACCOUNT_BALANCES}[].amount": "Decimal",
                    f"{PRODUCT_VALUES}[].date": "datetime",
                    f"{PRODUCT_VALUES}[].units": "Decimal",
                    f"{PRODUCT_VALUES}[].investment": "Decimal",
                    f"{PRODUCT_VALUES}[].value": "Decimal"
                }
            }
        }, ensure_ascii=False, default=str)

        mock_encrypt.return_value = mock_decrypt.return_value = json_with_metadata.encode('utf-8')

        with tempfile.TemporaryDirectory() as temp_dir:
            backup_path = os.path.join(temp_dir, "balances")

            with patch('brad.data.backup.BACKUP_DIR', backup_path):
                backup_data(self.test_file_name, self.test_data, source=source, fmt="binary", encrypt=True)
                backup_file_path = os.path.join(backup_path, self.test_file_name + ".b")

                self.assertTrue(os.path.exists(backup_file_path))
                with open(backup_file_path, 'rb') as f:
                    self.assertEqual(mock_encrypt.return_value, f.read())

                mock_db = MagicMock()
                restored_data = restore_backup(backup_file_path, mock_db)

        mock_encrypt.assert_called_once()
        mock_decrypt.assert_called_once_with(mock_encrypt.return_value)
        self.assertEqual(self.test_data, restored_data)


class TestGetReferenceData(unittest.TestCase):
    """Test cases for get_reference_data function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_reference_data = {
            "data": {
                ACCOUNTS: [
                    {"id": 1, "name": "Test Account", "account_type": "checking"}
                ],
                FINANCIAL_PRODUCTS: [
                    {"id": 1, "name": "Test Product", "product_type": "investment"}
                ]
            },
            "_metadata": {
                "type_map": {},
                "created_at": "2023-01-01T00:00:00"
            }
        }

    @patch('brad.data.backup.load_backup_file')
    @patch('brad.data.backup.get_history_transactions')
    @patch('brad.data.backup.remove_historical_attributes')
    @patch('brad.data.backup.write_to_db')
    @patch('brad.data.backup._restore_types')
    def test_get_reference_data_without_history(self, mock_restore_types, mock_write_to_db,
                                                mock_remove_hist, mock_get_hist, mock_load_backup):
        """Test getting reference data without history transactions."""
        mock_load_backup.return_value = self.test_reference_data
        mock_restore_types.return_value = self.test_reference_data["data"]
        mock_remove_hist.return_value = self.test_reference_data["data"]
        mock_db = MagicMock()

        result = get_reference_data(with_history_transactions=False)

        mock_load_backup.assert_called_once()
        mock_restore_types.assert_called_once_with(
            self.test_reference_data["data"],
            self.test_reference_data["_metadata"]["type_map"]
        )
        mock_get_hist.assert_not_called()
        mock_remove_hist.assert_called_once_with(self.test_reference_data["data"])
        self.assertEqual(result, self.test_reference_data["data"])

    @patch('brad.data.backup.load_backup_file')
    @patch('brad.data.backup.get_history_transactions')
    @patch('brad.data.backup.remove_historical_attributes')
    @patch('brad.data.backup.write_to_db')
    @patch('brad.data.backup._restore_types')
    def test_get_reference_data_with_history(self, mock_restore_types, mock_write_to_db,
                                             mock_remove_hist, mock_get_hist, mock_load_backup):
        """Test getting reference data with history transactions."""
        mock_load_backup.return_value = self.test_reference_data.copy()

        # _restore_types returns the original data (no changes in this test)
        restored_data = self.test_reference_data["data"].copy()
        mock_restore_types.return_value = restored_data

        # get_history_transactions returns some history data
        mock_get_hist.return_value = {"history_transactions": [{"id": 1, "amount": 100}]}

        # remove_historical_attributes returns some cleaned data
        final_data = {"cleaned": "data"}
        mock_remove_hist.return_value = final_data

        mock_db = MagicMock()

        result = get_reference_data(with_history_transactions=True)

        # Verify the mocks were called
        mock_load_backup.assert_called_once()
        mock_restore_types.assert_called_once_with(
            self.test_reference_data["data"],
            self.test_reference_data["_metadata"]["type_map"]
        )
        mock_get_hist.assert_called_once()  # Called with some version of reference_data
        mock_remove_hist.assert_called_once()  # Called with some version of reference_data
        self.assertEqual(result, final_data)


class TestBackupErrorHandling(unittest.TestCase):
    """Test error handling in backup operations."""

    @patch('brad.data.backup.open', side_effect=PermissionError("Access denied"))
    @patch('brad.data.backup.logger')
    def test_backup_data_json_permission_error(self, mock_logger, mock_open):
        """Test JSON backup handles permission errors."""
        with self.assertRaises(PermissionError):
            backup_data("test", {"data": "test"}, source="test", fmt="json")

        mock_logger.error.assert_called()

    @patch('brad.data.backup.open', side_effect=OSError("Disk full"))
    @patch('brad.data.backup.logger')
    def test_backup_data_binary_os_error(self, mock_logger, mock_open):
        """Test binary backup handles OS errors."""
        with self.assertRaises(OSError):
            backup_data("test", {"data": "test"}, source="test", fmt="binary")

        mock_logger.error.assert_called()


if __name__ == '__main__':
    unittest.main()
