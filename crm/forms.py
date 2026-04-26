from django import forms
from .models import Opportunity
from users.models import *

class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = ['stage', 'converted_to_customer', 'value', 'assigned_to']

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)  # Get current_user from kwargs
        super().__init__(*args, **kwargs)

        if current_user:
            # Filter the assigned_to field to only include users from the same company as the logged-in user
            self.fields['assigned_to'].queryset = CustomUser.objects.filter(company=current_user.company)