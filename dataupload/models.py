from django.db import models
from django.contrib.auth.models import User
import os
from users.models import *
import uuid

class UploadedFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
    format_type = models.CharField(max_length=50, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)  # Track if the file has been processed

    def save(self, *args, **kwargs):
        if not self.format_type:
             self.format_type = os.path.splitext(self.file.name)[1].lower()
        super().save(*args, **kwargs)
        

class UploadedFileAnalysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uploaded_file = models.OneToOneField(UploadedFile, on_delete=models.CASCADE, related_name="analysis")
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=50, help_text="MIME type or extension")
    num_columns = models.PositiveIntegerField(help_text="Number of columns in the file")
    num_rows = models.PositiveIntegerField(help_text="Number of rows in the file")
    column_headers = models.JSONField(help_text="List of column names", default=list)

    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.uploaded_file.file.name}"