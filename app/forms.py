from django import forms
from users.models import CustomUser

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['company_name', 'email', 'username', 'first_name', 'last_name', 'phone_number']  # Add fields you want to edit

from django import forms
from .models import *

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        exclude = ['created_by_user']
        fields = ['name', 'address', 'city', 'state', 'zip', 'country', 'description']

    def save(self, commit=True):
        location = super().save(commit=False)
        if commit:
            location.save()
        return location

class EquipmentForm(forms.ModelForm):
    location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        label="Location",
        widget=forms.Select,
        empty_label="Select a Location",
    )
    
    class Meta:
        model = Equipment
        fields = ['name', 'description', 'category', 'quantity', 'location', 'make', 'model', 'stock_number', 'year', 'miles_hours']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].label_from_instance = lambda Location: Location.name

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['assigned_user', 'employee_number', 'callsign', 'first_name', 'last_name', 'phone_number', 'position', 'department', 'group', 'date_hired', 'location', 'status', 'level']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extract the logged-in user
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'company') and user.company:
            # Limit `to_users` to users in the same company as the logged-in user
            self.fields['assigned_user'].queryset = CustomUser.objects.filter(company=user.company)


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ['customer', 'service_type', 'start_date', 'end_date', 'start_location', 'end_location', 'equipment', 'employee', 'start_time', 'end_time']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

from django import forms
from .models import ServiceType

class ServiceTypeForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = ['name', 'description', 'daily_rate']


class LocationAdminForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = '__all__'

    # Encrypt fields before saving
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Encrypt fields before saving them
        instance.name = encrypt(self.cleaned_data['name'])
        instance.address = encrypt(self.cleaned_data['address'])
        instance.city = encrypt(self.cleaned_data['city'])
        instance.state = encrypt(self.cleaned_data['state'])
        instance.country = encrypt(self.cleaned_data['country'])
        instance.description = encrypt(self.cleaned_data['description'])
        if commit:
            instance.save()
        return instance
    
from .models import Company

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'address', 'city', 'state', 'zip']


from .models import Directmessage

class DirectmessageForm(forms.ModelForm):
    to_users = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.none(),  # Dynamically set in __init__
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Recipients"
    )

    class Meta:
        model = Directmessage
        fields = ['body', 'to_users']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extract the logged-in user
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'company') and user.company:
            # Limit `to_users` to users in the same company as the logged-in user
            self.fields['to_users'].queryset = CustomUser.objects.filter(company=user.company)

class PostingForm(forms.ModelForm):
    to_users = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.none(),  
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Select Users"
    )

    class Meta:
        model = Posting
        fields = ['body', 'to_users']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extract user from kwargs
        super().__init__(*args, **kwargs)
        if CustomUser and CustomUser.company:
            # Limit `to_users` to those in the same company as the logged-in user
            self.fields['to_users'].queryset = CustomUser.objects.filter(company=CustomUser.company)



class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'text']

from .models import CostSheet

class CostSheetForm(forms.ModelForm):
    class Meta:
        model = CostSheet
        fields = [
            'employee',
            'equipment',
            'location',
            'service_type',
            'start_date',
            'end_date',
            'labor_cost',
            'equipment_cost',
        ]

    def clean(self):
        cleaned_data = super().clean()
        labor = cleaned_data.get('labor_cost') or 0
        equip = cleaned_data.get('equipment_cost') or 0
        cleaned_data['total_cost'] = labor + equip
        return cleaned_data