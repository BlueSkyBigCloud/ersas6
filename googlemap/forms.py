from django import forms
from .models import MapLocation

class MapLocationForm(forms.ModelForm):
    latitude = forms.FloatField(label='Latitude')
    longitude = forms.FloatField(label='Longitude')

    class Meta:
        model = MapLocation
        fields = ['name', 'description', 'latitude', 'longitude']

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Create a Point object with the latitude and longitude
        point = (self.cleaned_data['longitude'], self.cleaned_data['latitude'])
        instance.coordinates = point
        if commit:
            instance.save()
        return instance