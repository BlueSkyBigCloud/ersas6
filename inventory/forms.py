from django import forms
from .models import Transaction, Item


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'sku', 'category', 'description', 'quantity', 'cost_price', 'selling_price', 'reorder_level']


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["item", "transaction_type", "quantity", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }