from cryptography.fernet import Fernet
from django.conf import settings
from cryptography.fernet import Fernet
import cryptography

def get_cipher():
    """Helper to get a Fernet cipher object with the encryption key."""
    encryption_key = settings.FERNET_KEY  # Retrieve the Fernet key from Django settings
    return Fernet(encryption_key)

def encrypt(data: str) -> str:
    """Encrypts a string using Fernet symmetric encryption."""
    cipher = get_cipher()  # Get the cipher from the key
    encrypted_data = cipher.encrypt(data.encode())  # Encrypt the data
    return encrypted_data.decode('utf-8')  # Convert bytes to string for storage

def decrypt(encrypted_data: str) -> str:
    """Decrypts a string using Fernet symmetric encryption."""
    try:
        cipher = get_cipher()  # Get the cipher from the key
        decrypted_data = cipher.decrypt(encrypted_data.encode())  # Decrypt the data
        return decrypted_data.decode('utf-8')  # Convert bytes to string
    except cryptography.fernet.InvalidToken:
        # Handle the InvalidToken exception gracefully
        return "Decryption failed - Invalid Token"
    except Exception as e:
        # Handle any other exceptions
        return f"Decryption failed - {str(e)}"