from cryptography.fernet import Fernet
from django.conf import settings
import base64



def get_cipher():
    """Helper to get a Fernet cipher object with the encryption key."""
    encryption_key = settings.ENCRYPTION_KEY  # Retrieve the key from Django settings
    return Fernet(encryption_key)

def encrypt(data: str) -> str:
    """Encrypts a string using Fernet symmetric encryption."""
    cipher = get_cipher()
    encrypted_data = cipher.encrypt(data.encode())
    return encrypted_data.decode('utf-8')  # Convert bytes to string for storage

def decrypt(data: str) -> str:
    """Decrypts a string using Fernet symmetric encryption."""
    cipher = get_cipher()
    try:
        decrypted_data = cipher.decrypt(data.encode())
        return decrypted_data.decode('utf-8')  # Convert bytes back to string
    except Exception as e:
        # Handle decryption error (e.g., log the error, raise an exception, etc.)
        return None