from django.db import models
from django.conf import settings
from embed_video.fields import EmbedVideoField
from app.models import Company

class Video(models.Model):
    name = models.CharField(max_length=100, unique=True)
    video = EmbedVideoField()
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='videos')
    def __str__(self):
        return self.name
    
