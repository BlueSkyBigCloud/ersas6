from django.db import models
from django.conf import settings
from embed_video.fields import EmbedVideoField

class Video(models.Model):
    name = models.CharField(max_length=100, unique=True)
    video = EmbedVideoField()
    def __str__(self):
        return self.name
    
