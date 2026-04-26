from django.contrib import admin

from django.contrib import admin
from .models import Category, Item, Transaction

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "quantity", "in_stock")
    search_fields = ("name", "sku")
    list_filter = ("category",)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("item", "transaction_type", "quantity", "date")
    list_filter = ("transaction_type", "date")
    search_fields = ("item__name",)