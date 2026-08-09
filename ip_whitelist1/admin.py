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

@admin.register(Blocked_IPAddress)
class Blocked_IPAddress(admin.ModelAdmin):
    list_display = ('ip_address', 'created_at', 'reason')
    search_fields = ('ip_address', 'created_at', 'reason')
    readonly_fields = ['ip_address', 'created_at']