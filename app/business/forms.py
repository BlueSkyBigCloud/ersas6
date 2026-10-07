from django import forms
from .models import *

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'address', 'payment_terms', 'payment_method', 'phone_number', 'account_rep']
        exclude = ['created_by_user', 'created_at']

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        exclude = ['service_request', 'created_by_user']
        fields = ['issue_date', 'due_date', 'payment_status', 'notes']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }


from decimal import Decimal, InvalidOperation

class LineItemForm(forms.ModelForm):
    DELETE = forms.BooleanField(required=False)  # Allows removal of items
    total_price = forms.DecimalField(
        max_digits=10, decimal_places=2, required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )
    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        try:
            return int(quantity)  # Ensure quantity is an integer
        except ValueError:
            raise forms.ValidationError("Invalid quantity. Must be a number.")

    def clean_unit_price(self):
        unit_price = self.cleaned_data['unit_price']
        try:
            return Decimal(unit_price)  # Ensure unit_price is a decimal
        except InvalidOperation:
            raise forms.ValidationError("Invalid price. Must be a decimal number.")

    class Meta:
        model = LineItem
        fields = ['description', 'quantity', 'unit_price', 'total_price']

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.total_price = instance.quantity * instance.unit_price
        if commit:
            instance.save()
        return instance
    
class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ["status"]  # customer & servicerequest are auto-filled