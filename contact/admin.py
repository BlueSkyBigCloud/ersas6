from django.contrib import admin

from .models import ContactUsRequest

@admin.register(ContactUsRequest)
class ContactUsRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone_number", "created_at")
    search_fields = ("name", "email", "phone_number", "address")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    readonly_fields = ("uuid", "created_at")