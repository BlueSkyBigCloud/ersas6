from django.db import models
from django.utils.timezone import now, timedelta
from django.conf import settings
import os
import uuid
from django.db import models
from users.models import CustomUser

class FileTransfer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to="uploads/")
    from_user = models.ForeignKey(CustomUser, related_name="files_sent", on_delete=models.CASCADE)
    to_user = models.ForeignKey(CustomUser, related_name="files_received", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    opened = models.BooleanField(default=False)  # Track if the file is opened
    opened_timestamp = models.DateTimeField(null=True, blank=True)  # Track when it was opened
    
    def is_expired(self):
        # Check if the file has been opened and the expiration time has passed (15 minutes after opened)
        if self.opened and self.opened_timestamp:
            expiration_time = self.opened_timestamp + timedelta(minutes=15)
            if now() > expiration_time:
                return True  # The file is expired if 15 minutes have passed after it was opened
        return False
    
    def mark_as_opened(self):
        # Mark the file as opened and store the opened timestamp
        self.opened = True
        self.opened_timestamp = now()
        self.save()
    
    def delete_file(self):
        # Optionally delete the file from the file system and remove the record from the database
        file_path = os.path.join(settings.MEDIA_ROOT, self.file.name)
        if os.path.exists(file_path):
            os.remove(file_path)
        self.delete()

