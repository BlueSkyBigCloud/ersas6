from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import *

admin.site.site_header = _("TRADE-SEC ADMIN") 

from .models import *
@admin.register(APKFile)
class ServiceTypeAdmin(admin.ModelAdmin):
    search_fields = ('name', 'id')
    list_filter = ('name', 'id') 
    readonly_fields = ['name', 'id']