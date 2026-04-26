from django.contrib import admin
from .models import *

# Register your models here.
# Admin configuration for ServiceType
@admin.register(UploadedFile)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('file',)  # Display the name in the admin list view
    search_fields = ('file',)  # Allow searching by name
    list_filter = ('file',)  # Filter by name in the sidebar
    readonly_fields = ['user', 'file', 'format_type']

@admin.register(UploadedFileAnalysis)
class UploadedFileAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id',)  # Display the name in the admin list view
    search_fields = ('id',)  # Allow searching by name
    list_filter = ('id',)  # Filter by name in the sidebar
    readonly_fields = ['uploaded_file', 'id', 'file_type', 'num_columns', 'num_rows', 'column_headers']