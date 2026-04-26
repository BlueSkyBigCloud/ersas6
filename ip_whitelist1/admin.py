from django.contrib import admin
from .models import *

class IPWhitelistAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'created_at')
    search_fields = ('user__username', 'ip_address')


admin.site.register(IPWhiteList, IPWhitelistAdmin)

class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'accessed_at')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ['user', 'ip_address']

admin.site.register(AccessLog, AccessLogAdmin)

from .models import Blocked_IPAddress

admin.site.register(Blocked_IPAddress)