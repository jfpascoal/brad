import os
import unittest
from unittest.mock import patch, mock_open

from cryptography.fernet import Fernet

from brad.data.encryption import (
    _get_encryption_key,
    encrypt_string,
    decrypt_string,
    ENCRYPTION_KEY_ENV_VAR
)


class TestEncryption(unittest.TestCase):
    """Test cases for the encryption module."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_string = "Hello, World! This is a test string with special chars: àáâãäå"
        self.test_json = '{"key": "value", "number": 42, "nested": {"array": [1, 2, 3]}}'
        self.valid_key = Fernet.generate_key()

    def tearDown(self):
        """Clean up after each test."""
        # Ensure environment variable is cleaned up
        if ENCRYPTION_KEY_ENV_VAR in os.environ:
            del os.environ[ENCRYPTION_KEY_ENV_VAR]

    @patch.dict(os.environ, {}, clear=True)
    @patch('brad.data.encryption.SECRETS_DIR', '/tmp/test_secrets')
    def test_get_encryption_key_from_file(self):
        """Test reading encryption key from file when env var is not set."""
        mock_key = self.valid_key.decode()

        with patch('builtins.open', mock_open(read_data=mock_key)) as mock_file:
            key = _get_encryption_key()

            # Check that file was opened (path separators may vary by OS)
            mock_file.assert_called_once()
            call_args = mock_file.call_args[0]
            self.assertTrue(call_args[0].endswith('encryption_key.txt'))
            self.assertEqual('r', call_args[1])
            self.assertEqual(self.valid_key, key)

    @patch.dict(os.environ, {ENCRYPTION_KEY_ENV_VAR: ""}, clear=True)
    def test_get_encryption_key_from_env_var(self):
        """Test reading encryption key from environment variable."""
        mock_key = self.valid_key.decode()
        os.environ[ENCRYPTION_KEY_ENV_VAR] = mock_key

        key = _get_encryption_key()
        self.assertEqual(self.valid_key, key)

    @patch.dict(os.environ, {}, clear=True)
    @patch('brad.data.encryption.SECRETS_DIR', '/tmp/test_secrets')
    @patch('builtins.open', side_effect=FileNotFoundError("File not found"))
    def test_get_encryption_key_file_not_found(self, mock_open_func):
        """Test FileNotFoundError when encryption key file doesn't exist and no env var."""
        with self.assertRaises(FileNotFoundError):
            _get_encryption_key()

    @patch.dict(os.environ, {}, clear=True)
    @patch('brad.data.encryption.SECRETS_DIR', '/tmp/test_secrets')
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_get_encryption_key_file_permission_error(self, mock_open_func):
        """Test ValueError when unable to read encryption key file."""
        with self.assertRaises(ValueError) as context:
            _get_encryption_key()

        self.assertIn("Failed to read encryption key from file", str(context.exception))

    @patch('brad.data.encryption._get_encryption_key')
    def test_encrypt_string_success(self, mock_get_key):
        """Test successful string encryption."""
        mock_get_key.return_value = self.valid_key

        encrypted_data = encrypt_string(self.test_string)

        # Verify it returns bytes
        self.assertIsInstance(encrypted_data, bytes)

        # Verify it's actually encrypted (different from original)
        self.assertNotEqual(encrypted_data, self.test_string.encode())

        # Verify it can be decrypted back to original
        fernet = Fernet(self.valid_key)
        decrypted = fernet.decrypt(encrypted_data).decode('utf-8')
        self.assertEqual(self.test_string, decrypted)

    @patch('brad.data.encryption._get_encryption_key')
    def test_encrypt_string_json_data(self, mock_get_key):
        """Test encryption of JSON string data."""
        mock_get_key.return_value = self.valid_key

        encrypted_data = encrypt_string(self.test_json)

        # Verify it returns bytes
        self.assertIsInstance(encrypted_data, bytes)

        # Verify it can be decrypted back to original JSON
        fernet = Fernet(self.valid_key)
        decrypted = fernet.decrypt(encrypted_data).decode('utf-8')
        self.assertEqual(self.test_json, decrypted)

    @patch('brad.data.encryption._get_encryption_key')
    def test_encrypt_string_empty_string(self, mock_get_key):
        """Test encryption of empty string."""
        mock_get_key.return_value = self.valid_key

        encrypted_data = encrypt_string("")

        # Verify it returns bytes
        self.assertIsInstance(encrypted_data, bytes)

        # Verify it can be decrypted back to empty string
        fernet = Fernet(self.valid_key)
        decrypted = fernet.decrypt(encrypted_data).decode('utf-8')
        self.assertEqual("", decrypted)

    @patch('brad.data.encryption._get_encryption_key')
    def test_encrypt_string_unicode(self, mock_get_key):
        """Test encryption of unicode characters."""
        mock_get_key.return_value = self.valid_key
        unicode_string = "Test with émojis: 🎉🔒🛡️ and símböls: àáâãäå"

        encrypted_data = encrypt_string(unicode_string)

        # Verify it can be decrypted back to original
        fernet = Fernet(self.valid_key)
        decrypted = fernet.decrypt(encrypted_data).decode('utf-8')
        self.assertEqual(unicode_string, decrypted)

    @patch('brad.data.encryption._get_encryption_key')
    def test_encrypt_string_key_error(self, mock_get_key):
        """Test ValueError when encryption key retrieval fails."""
        mock_get_key.side_effect = FileNotFoundError("Key not found")

        with self.assertRaises(ValueError) as context:
            encrypt_string(self.test_string)

        self.assertIn("Failed to encrypt string", str(context.exception))

    @patch('brad.data.encryption._get_encryption_key')
    def test_encrypt_string_invalid_key(self, mock_get_key):
        """Test ValueError when encryption key is invalid."""
        mock_get_key.return_value = b"invalid_key"

        with self.assertRaises(ValueError) as context:
            encrypt_string(self.test_string)

        self.assertIn("Failed to encrypt string", str(context.exception))

    @patch('brad.data.encryption._get_encryption_key')
    def test_decrypt_string_success(self, mock_get_key):
        """Test successful string decryption."""
        mock_get_key.return_value = self.valid_key

        # First encrypt the test string
        fernet = Fernet(self.valid_key)
        encrypted_data = fernet.encrypt(self.test_string.encode('utf-8'))

        # Then decrypt it
        decrypted_string = decrypt_string(encrypted_data)

        self.assertEqual(self.test_string, decrypted_string)

    @patch('brad.data.encryption._get_encryption_key')
    def test_decrypt_string_json_data(self, mock_get_key):
        """Test decryption of JSON string data."""
        mock_get_key.return_value = self.valid_key

        # First encrypt the test JSON
        fernet = Fernet(self.valid_key)
        encrypted_data = fernet.encrypt(self.test_json.encode('utf-8'))

        # Then decrypt it
        decrypted_string = decrypt_string(encrypted_data)

        self.assertEqual(self.test_json, decrypted_string)

    @patch('brad.data.encryption._get_encryption_key')
    def test_decrypt_string_empty_data(self, mock_get_key):
        """Test decryption of empty string."""
        mock_get_key.return_value = self.valid_key

        # First encrypt empty string
        fernet = Fernet(self.valid_key)
        encrypted_data = fernet.encrypt("".encode('utf-8'))

        # Then decrypt it
        decrypted_string = decrypt_string(encrypted_data)

        self.assertEqual("", decrypted_string)

    @patch('brad.data.encryption._get_encryption_key')
    def test_decrypt_string_unicode(self, mock_get_key):
        """Test decryption of unicode characters."""
        mock_get_key.return_value = self.valid_key
        unicode_string = "Test with émojis: 🎉🔒🛡️ and símböls: àáâãäå"

        # First encrypt the unicode string
        fernet = Fernet(self.valid_key)
        encrypted_data = fernet.encrypt(unicode_string.encode('utf-8'))

        # Then decrypt it
        decrypted_string = decrypt_string(encrypted_data)

        self.assertEqual(unicode_string, decrypted_string)

    @patch('brad.data.encryption._get_encryption_key')
    def test_decrypt_string_invalid_data(self, mock_get_key):
        """Test ValueError when encrypted data is invalid."""
        mock_get_key.return_value = self.valid_key

        with self.assertRaises(ValueError) as context:
            decrypt_string(b"invalid_encrypted_data")

        self.assertIn("Failed to decrypt string", str(context.exception))

    @patch('brad.data.encryption._get_encryption_key')
    def test_decrypt_string_wrong_key(self, mock_get_key):
        """Test ValueError when using wrong key for decryption."""
        # Encrypt with one key
        fernet1 = Fernet(self.valid_key)
        encrypted_data = fernet1.encrypt(self.test_string.encode('utf-8'))

        # Try to decrypt with different key
        wrong_key = Fernet.generate_key()
        mock_get_key.return_value = wrong_key

        with self.assertRaises(ValueError) as context:
            decrypt_string(encrypted_data)

        self.assertIn("Failed to decrypt string", str(context.exception))

    @patch('brad.data.encryption._get_encryption_key')
    def test_decrypt_string_key_error(self, mock_get_key):
        """Test ValueError when decryption key retrieval fails."""
        mock_get_key.side_effect = FileNotFoundError("Key not found")

        with self.assertRaises(ValueError) as context:
            decrypt_string(b"some_encrypted_data")

        self.assertIn("Failed to decrypt string", str(context.exception))

    def test_roundtrip_encryption_decryption(self):
        """Test complete roundtrip: encrypt then decrypt."""
        with patch.dict(os.environ, {ENCRYPTION_KEY_ENV_VAR: self.valid_key.decode()}):
            # Encrypt
            encrypted_data = encrypt_string(self.test_string)

            # Decrypt
            decrypted_string = decrypt_string(encrypted_data)

            # Verify roundtrip success
            self.assertEqual(self.test_string, decrypted_string)

    def test_roundtrip_encryption_decryption_large_data(self):
        """Test roundtrip with large data."""
        large_string = "A" * 10000  # 10KB of data

        with patch.dict(os.environ, {ENCRYPTION_KEY_ENV_VAR: self.valid_key.decode()}):
            # Encrypt
            encrypted_data = encrypt_string(large_string)

            # Decrypt
            decrypted_string = decrypt_string(encrypted_data)

            # Verify roundtrip success
            self.assertEqual(large_string, decrypted_string)

    def test_encrypted_data_is_different_each_time(self):
        """Test that encrypting the same string produces different ciphertext each time."""
        with patch.dict(os.environ, {ENCRYPTION_KEY_ENV_VAR: self.valid_key.decode()}):
            encrypted1 = encrypt_string(self.test_string)
            encrypted2 = encrypt_string(self.test_string)

            # Should be different due to random IV
            self.assertNotEqual(encrypted1, encrypted2)

            # But both should decrypt to the same value
            decrypted1 = decrypt_string(encrypted1)
            decrypted2 = decrypt_string(encrypted2)
            self.assertEqual(self.test_string, decrypted1)
            self.assertEqual(self.test_string, decrypted2)


if __name__ == '__main__':
    unittest.main()
