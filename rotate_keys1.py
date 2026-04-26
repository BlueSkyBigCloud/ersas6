import os
import django
from django.conf import settings
from django.db import connections


# Set up the Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ersas5.settings.base")
django.setup()

from cryptography.fernet import Fernet
from app.models import (

    Directmessage, 

)  # Replace with your actual model import names


# Load old and new keys from environment variables or hardcode them
OLD_KEY = "qaB2f73Uv_RGZSuC-U1WLJNtYdf30c-gQyuWijW7Mzs="
NEW_KEY = "JCQn4Ut5KZ-B2mPZWKr7yv2YFoKxLhhd_FRlTw9eUjw="

old_cipher = Fernet(OLD_KEY.encode())
new_cipher = Fernet(NEW_KEY.encode())

def rotate_model_keys(model, fields):
    """Generic function to rotate encryption keys for a given model and its encrypted fields."""
    modified_objs = []
    
    for obj in model.objects.all():
        try:
            updated = False  # Flag to track if any field is updated
            for field in fields:
                # Get the field value dynamically
                value = getattr(obj, field)
                
                if value:  # If the field has a value
                    decrypted_value = old_cipher.decrypt(value.encode()).decode()
                    encrypted_value = new_cipher.encrypt(decrypted_value.encode()).decode()
                    
                    if getattr(obj, field) != encrypted_value:  # Check if value is different
                        setattr(obj, field, encrypted_value)
                        updated = True  # Mark as updated
            
            # Only add to modified objects if something was updated
            if updated:
                modified_objs.append(obj)
        
        except Exception as e:
            print(f"Error processing {model.__name__} (ID: {obj.id}): {e}")
    
    # Perform bulk update for modified objects
    if modified_objs:
        model.objects.bulk_update(modified_objs, fields)

# Define fields that need to be processed for each model
model_field_map = {
    Directmessage: ['body'],
}

# Process each model
for model, fields in model_field_map.items():
    rotate_model_keys(model, fields)

print("Encryption keys rotated successfully across all models.")