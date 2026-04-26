from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import *

@admin.register(Video)
class Video(admin.ModelAdmin):
    list_display = ('name',) 
    search_fields = ('name',)
    list_filter = ('name',)
    readonly_fields = []
