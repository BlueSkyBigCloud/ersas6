from django.contrib import admin
from .models import Transaction, FinAccount

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_by_user', 'to_user', 'amount', 'currency', 'timestamp')
    list_filter = ('currency', 'timestamp')
    search_fields = ('id', 'description')

@admin.register(FinAccount)
class FinAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'total')
    list_filter = ('type',)
    search_fields = ('user__username',)