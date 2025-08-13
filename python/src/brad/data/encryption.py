import os
import logging
from cryptography.fernet import Fernet

from brad import SECRETS_DIR


logger = logging.getLogger(__name__)

# Environment variable name for the encryption key
ENCRYPTION_KEY_ENV_VAR = "BRAD_DATA_KEY"


def _get_encryption_key() -> bytes:
    """
    Read the encryption key from environment variable or secrets directory.
    First checks for environment variable, then falls back to reading from secrets file.
    
    :return: Encryption key as bytes
    :raises FileNotFoundError: If the encryption key file is not found and env var is not set
    :raises ValueError: If the encryption key is invalid
    """
    # First, try to get the key from environment variable
    env_key = os.getenv(ENCRYPTION_KEY_ENV_VAR)
    if env_key:
        logger.debug(f"Using encryption key from environment variable: {ENCRYPTION_KEY_ENV_VAR}")
        return env_key.encode()
    
    # Fall back to reading from file
    key_file_path = os.path.join(SECRETS_DIR, "encryption_key.txt")
    
    try:
        with open(key_file_path, "r") as f:
            key_str = f.read().strip()
        logger.debug(f"Using encryption key from file: {key_file_path}")
        return key_str.encode()
    except FileNotFoundError:
        logger.error(f"Encryption key not found in environment variable '{ENCRYPTION_KEY_ENV_VAR}' or file '{key_file_path}'")
        raise
    except Exception as e:
        msg = f"Failed to read encryption key from file '{key_file_path}': {e}"
        logger.error(msg)
        raise ValueError(msg)


def encrypt_string(data: str) -> bytes:
    """
    Encrypt a string and return the encrypted data as bytes.
    
    :param data: String to encrypt
    :return: Encrypted data as bytes
    :raises ValueError: If encryption fails
    """
    try:
        # Get the encryption key
        key = _get_encryption_key()
        fernet = Fernet(key)
        
        # Convert string to bytes and encrypt
        data_bytes = data.encode('utf-8')
        encrypted_data = fernet.encrypt(data_bytes)
        
        logger.info("String encrypted successfully")
        return encrypted_data
        
    except Exception as e:
        msg = f"Failed to encrypt string: {e}"
        logger.error(msg)
        raise ValueError(msg)


def decrypt_string(encrypted_data: bytes) -> str:
    """
    Decrypt encrypted bytes and return the original string.
    
    :param encrypted_data: Encrypted data as bytes
    :return: Decrypted string in its original format
    :raises ValueError: If decryption fails
    """
    try:
        # Get the encryption key
        key = _get_encryption_key()
        fernet = Fernet(key)
        
        # Decrypt the data and convert back to string
        decrypted_bytes = fernet.decrypt(encrypted_data)
        data = decrypted_bytes.decode('utf-8')
        
        logger.info("String decrypted successfully")
        return data
        
    except Exception as e:
        msg = f"Failed to decrypt string: {e}"
        logger.error(msg)
        raise ValueError(msg)
