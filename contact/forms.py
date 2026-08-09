from django import forms
from .models import ContactUsRequest

class ContactUsRequestForm(forms.ModelForm):
    class Meta:
        model = ContactUsRequest
        fields = ['name', 'last_name', 'company_name', 'phone_number', 'email', 'address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mark required fields
        self.fields['name'].required = True
        self.fields['last_name'].required = True
        self.fields['company_name'].required = True
        self.fields['phone_number'].required = True
        self.fields['email'].required = True
        self.fields['address'].required = True