from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import *

admin.site.site_header = _("TRADE-SEC ADMIN")  # Title on the top-left of the admin
admin.site.site_title = _("TRADESEC 1.0 PROTOTYPE ALPHA PLATFORM ADMIN Portal")   # Title on the browser tab
admin.site.index_title = _("Welcome to TRADESEC ADMIN")  #

# Admin configuration for ServiceType
@admin.register(FileTransfer)
class FileTransferAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'timestamp')  # Display the name in the admin list view
    search_fields = ('from_user', 'to_user')  # Allow searching by name
    list_filter = ('timestamp',)  # Filter by name in the sidebar
    readonly_fields = ['file', 'from_user', 'to_user', 'timestamp', 'opened', 'opened_timestamp']
