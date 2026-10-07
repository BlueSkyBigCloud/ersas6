from django.db import models

# Create your models here.
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import os
import base64

class AESCipher:
    def __init__(self, password, data=None):
        """
        Initialize the AESCipher class with a password and optional data.
        :param password: The password used for key derivation (should be at least 8 characters long).
        :param data: Data to be encrypted (optional, only for encryption)
        """
        self.password = password
        self.data = data
        self.block_size = 16  # AES block size is 16 bytes
        self.key = None
        self.salt = None
        self.iv = None
        self.encrypted_data = None

    def _derive_key(self):
        """
        Derive a 256-bit AES key using PBKDF2 from the password.
        """
        # Generate a random 16-byte salt (this should be stored alongside encrypted data)
        self.salt = os.urandom(16)
        
        # PBKDF2-HMAC with SHA-256, 100,000 iterations
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits for AES-256
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )
        self.key = kdf.derive(self.password.encode())  # Derive the key from the password
        return self.key

    def encrypt(self):
        """
        Encrypt the data using AES-256 in CBC mode.
        :return: Encrypted data (base64 encoded), IV (base64 encoded), and Salt (base64 encoded)
        """
        if self.data is None:
            raise ValueError("No data provided to encrypt.")
        
        # Ensure data is in bytes
        if isinstance(self.data, str):
            self.data = self.data.encode()

        # Derive the key
        self._derive_key()

        # Generate a random IV (Initialization Vector)
        self.iv = os.urandom(self.block_size)

        # Pad the data to make its length a multiple of the block size
        padder = padding.PKCS7(128).padder()  # AES block size is 128 bits (16 bytes)
        padded_data = padder.update(self.data) + padder.finalize()

        # Create the cipher using AES-256 CBC mode
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Encrypt the data
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

        # Base64 encode the encrypted data, IV, and Salt for storage/transmission
        encrypted_data_b64 = base64.b64encode(encrypted_data).decode()
        iv_b64 = base64.b64encode(self.iv).decode()
        salt_b64 = base64.b64encode(self.salt).decode()

        return encrypted_data_b64, iv_b64, salt_b64

    def decrypt(self, encrypted_data_b64, iv_b64, salt_b64):
        """
        Decrypt the provided data using AES-256 in CBC mode.
        :param encrypted_data_b64: Base64 encoded encrypted data.
        :param iv_b64: Base64 encoded IV.
        :param salt_b64: Base64 encoded salt used for key derivation.
        :return: Decrypted data (original string)
        """
        # Decode the base64 encoded data
        encrypted_data = base64.b64decode(encrypted_data_b64)
        iv = base64.b64decode(iv_b64)
        salt = base64.b64decode(salt_b64)

        # Derive the key using the provided salt
        self.salt = salt
        self._derive_key()

        # Create the cipher using AES-256 CBC mode with the IV
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        # Decrypt the data
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

        # Unpad the decrypted data
        unpadder = padding.PKCS7(128).unpadder()
        original_data = unpadder.update(decrypted_data) + unpadder.finalize()

        return original_data.decode()  # Assuming the original data was a string

# Example Usage:

# Encryption Example
cipher = AESCipher(password="securepassword", data="Sensitive Data to Encrypt")
encrypted_data_b64, iv_b64, salt_b64 = cipher.encrypt()
print(f"Encrypted Data: {encrypted_data_b64}")
print(f"IV: {iv_b64}")
print(f"Salt: {salt_b64}")

# Decryption Example
cipher = AESCipher(password="securepassword")
decrypted_data = cipher.decrypt(encrypted_data_b64, iv_b64, salt_b64)
print(f"Decrypted Data: {decrypted_data}")