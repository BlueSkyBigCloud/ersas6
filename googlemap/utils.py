import googlemaps
from django.conf import settings
import os

def geocode_address(address):
    """Geocodes an address and returns latitude and longitude as a tuple."""
    try:
        gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))
        geocode_result = gmaps.geocode(address)

        # Debugging: Print API response
        print("Geocode API Response:", geocode_result)

        if geocode_result and isinstance(geocode_result, list):
            first_result = geocode_result[0] if len(geocode_result) > 0 else {}

            location = first_result.get("geometry", {}).get("location", {})

            lat = location.get("lat")
            lng = location.get("lng")

            if lat is not None and lng is not None:
                return lat, lng

        return None, None  # Explicitly return both values if geocoding fails

    except Exception as e:
        print(f"Geocoding error: {e}")
        return None, None  # Ensure function always returns two values