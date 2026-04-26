from django.db import models
from django.http import HttpResponse

# Create your models here.

class APKFile(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='apks/')  # The directory for storing files
    uploaded_at = models.DateTimeField(auto_now_add=True)
