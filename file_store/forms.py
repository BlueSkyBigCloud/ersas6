from django import forms
from .models import APKFile

class APKUploadForm(forms.ModelForm):
    class Meta:
        model = APKFile
        fields = ['name', 'file']