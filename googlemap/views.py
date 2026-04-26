from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from app.decorators import onboarded, staff_required
import googlemaps
import os
from .forms import *
import requests

@login_required
@onboarded()
def map_view(request):
    context = {}

    # Initialize Google Maps API client
    gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))

    if request.method == "POST":
        address = request.POST.get('address')
        if address:
            # Geocode the address to get latitude and longitude
            geocode_result = gmaps.geocode(address)
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                lat = location['lat']
                lng = location['lng']
                context['latitude'] = lat
                context['longitude'] = lng

                # Pass API key to the context
    context['google_maps_api_key'] = os.getenv('GOOGLE_MAPS_API_KEY')

    return render(request, 'map.html', context)

from .models import *
@login_required
@onboarded()
def map_location_view(request):
    context = {}
    gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))
    if request.method == "POST":
        address = request.POST.get('address')
        if address:
            # Geocode the address to get latitude and longitude
            geocode_result = gmaps.geocode(address)
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                lat = location['lat']
                lng = location['lng']
                context['latitude'] = lat
                context['longitude'] = lng

    locations = MapLocation.objects.all()
    return render(request, 'map_markers.html', {'locations': locations})

@login_required
@onboarded()
def create_map_location(request):
    if request.method == 'POST':
        form = MapLocationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('map_location_list')  # Redirect to the list of map locations
    else:
        form = MapLocationForm()

    return render(request, 'create_map_location.html', {
        'form': form,
        'GOOGLE_MAPS_API_KEY': os.getenv('GOOGLE_MAPS_API_KEY')
    })

from django.http import JsonResponse
from .utils import geocode_address

def geocode_page(request):
    return render(request, "geocode.html")


@onboarded()
@login_required
def geocode_view(request):
    """Handles geocoding requests and returns JSON with latitude and longitude."""
    if request.method == "GET":
        address = request.GET.get("address", "").strip()

        if not address:
            return JsonResponse({"error": "No address provided"}, status=400)

        lat, lng = geocode_address(address)

        if lat is None or lng is None:
            return JsonResponse({"error": "Geocoding failed"}, status=500)

        return JsonResponse({"latitude": lat, "longitude": lng})

    return JsonResponse({"error": "Invalid request method"}, status=405)


from django.shortcuts import render
from .models import MapLocation

@staff_required(redirect_view='home')
@onboarded()
@login_required
def map_location_list(request):
    locations = MapLocation.objects.all()
    return render(request, 'map_location_list.html', {'locations': locations})

@staff_required(redirect_view='home')
@onboarded()
@login_required
def geocode1_page(request):
    return render(request, "geocode1.html")

@staff_required(redirect_view='home')
def geocode2_view(request):
    geocode_result = None
    address = ''
    
    if request.method == 'POST':
        address = request.POST.get('address')
        if address:
            # Initialize Google Maps Client with the API key
            gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
            
            # Perform geocoding
            geocode_result = gmaps.geocode(address)
    
    return render(request, 'geocode2.html', {'geocode_result': geocode_result, 'address': address})

from app.models import Location

@staff_required(redirect_view='home')
def address_to_coordinates(request, location_id):
    # Fetch the Location object
    location = Location.objects.get(id=location_id)
    gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))

    # Get the address to geocode
    address = location.address
    geocode_result = gmaps.geocode(address)

    if geocode_result:
        # Get the latitude and longitude from the first result
        latitude = geocode_result[0]['geometry']['location']['lat']
        longitude = geocode_result[0]['geometry']['location']['lng']

        # Update the Location object with the new coordinates
        location.latitude = latitude
        location.longitude = longitude
        location.save()

        # Redirect or return a success response
        return JsonResponse({'status': 'success', 'latitude': latitude, 'longitude': longitude})
    else:
        return JsonResponse({'status': 'error', 'message': 'Unable to geocode address'})
    
@staff_required(redirect_view='home')
@onboarded()
@login_required
def geocode3_view(request):
    return render(request, "geocode3.html")



@staff_required(redirect_view='home')
@onboarded()
@login_required
def geocode4_view(request):
    geocode_result = None
    address = None

    if request.method == "POST":
        address = request.POST.get('address')
        
        # Use the Google Maps Geocoding API to get the coordinates for the address
        api_key = settings.GOOGLE_MAPS_API_KEY
        url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}'
        
        # Make the API request
        response = requests.get(url)
        data = response.json()
        
        # Check if there are any results from the API
        if data['status'] == 'OK':
            geocode_result = data['results']
        else:
            geocode_result = None

    return render(request, "geocode4.html", {
        'geocode_result': geocode_result,
        'address': address
    })

@onboarded()
@login_required
def geocode5_view(request):
    geocode_result = None
    address = None

    if request.method == "POST":
        address = request.POST.get('address')
        
        # Use the Google Maps Geocoding API to get the coordinates for the address
        api_key = settings.GOOGLE_MAPS_API_KEY
        url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}'
        
        # Make the API request
        response = requests.get(url)
        data = response.json()
        
        # Check if there are any results from the API
        if data['status'] == 'OK':
            geocode_result = data['results']
        else:
            geocode_result = None

    return render(request, "geocode5.html", {
        'geocode_result': geocode_result,
        'address': address
    })


from django.shortcuts import render
from app.models import Location
import json

def map_locations(request):
    locations = Location.objects.all()  # Fetch all locations from the database
    
    # Prepare the locations data for use in JavaScript
    locations_data = [
        {
            "name": location.name,
            "latitude": location.latitude,
            "longitude": location.longitude,
        }
        for location in locations
    ]
    
    # Pass locations data as JSON to the template
    return render(request, 'maplocations.html', {
        'locations': locations,
        'locations_json': json.dumps(locations_data)  # Serialize locations data to JSON
    })




@login_required
@onboarded()
def geocode6_view(request):
    user = request.user
    locations = Location.objects.filter(company=user.company)

    for loc in locations:
        loc.decrypt_fields(user=user)

        # If lat/lng missing, geocode and save
        if loc.latitude is None or loc.longitude is None:
            full_address = f"{loc.address}, {loc.city}, {loc.state}, {loc.country}"
            lat, lng = geocode_address(full_address)
            if lat and lng:
                loc.latitude = lat
                loc.longitude = lng
                loc.save()  # Saves encrypted lat/lng
                loc.decrypt_fields(user=user)  # Re-decrypt to display

    return render(request, "geocode6.html", {
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
        "locations": locations
    })


@login_required
@onboarded()
def geocode7_view(request):
    user = request.user
    locations = Location.objects.filter(company=user.company).prefetch_related(
        'service_requests_start',
        'service_requests_end'
    )

    for loc in locations:
        loc.decrypt_fields(user=user)

        # Fill missing lat/lng via geocode
        if loc.latitude is None or loc.longitude is None:
            full_address = f"{loc.address}, {loc.city}, {loc.state}, {loc.country}"
            lat, lng = geocode_address(full_address)
            if lat is not None and lng is not None:
                loc.latitude = lat
                loc.longitude = lng
                loc.save()
                loc.decrypt_fields(user=user)

        # Merge service requests (start + end) and remove duplicates
        reqs = list(loc.service_requests_start.all()) + list(loc.service_requests_end.all())
        seen_ids = set()
        unique_requests = []
        for r in reqs:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                unique_requests.append(r)
        loc.unique_service_requests = unique_requests  # attach for template
        

    return render(request, "geocode7.html", {
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
        "locations": locations
    })