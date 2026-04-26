from django import forms
from .models import Prospect, Action
from business.models import Customer

class ProspectForm(forms.ModelForm):
    class Meta:
        model = Prospect
        fields = [
            "name",
            "business_type",
            "contact",
            "email",
            "phone_number",
            "website",
            "products",
            "company_size",
            "account_rep",
            "status",
            "address",
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
            'products': forms.Textarea(attrs={'rows': 2}),
        }

        
class ActionForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ["action_type", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class ConvertToCustomerForm(forms.Form):
    payment_terms = forms.ChoiceField(choices=Customer.PAYMENT_TERMS)
    payment_method = forms.ChoiceField(choices=Customer.PAYMENT_METHOD_CHOICES)