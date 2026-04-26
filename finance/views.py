from django.shortcuts import render
from app.views import *
from django.contrib.auth.decorators import login_required
from app. models import *

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import timedelta

# Define constants
PRICE_PER_DAY = 100  # Example flat daily rate
EQUIPMENT_MULTIPLIER = {
    "TypeA": 1.0,  # Multiplier for equipment type "TypeA"
    "TypeB": 1.5,  # Multiplier for equipment type "TypeB"
    "TypeC": 2.0,  # Multiplier for equipment type "TypeC"
}

@login_required
def finance_view(request):
    # Fetch service requests created by the logged-in user
    service_requests = ServiceRequest.objects.filter(created_by_user=request.user)

    total_cost = 0
    service_data = []

    for sr in service_requests:
        # Calculate the number of days
        number_of_days = (sr.end_date - sr.start_date).days + 1  # Include both start and end dates

        # Get the equipment multiplier based on equipment type
        equipment_type = sr.equipment.type  # Assuming `type` exists in the Equipment model
        multiplier = EQUIPMENT_MULTIPLIER.get(equipment_type, 1.0)

        # Calculate the total cost for this service request
        request_total = PRICE_PER_DAY * number_of_days * multiplier

        # Add to the total cost
        total_cost += request_total

        # Prepare data for the template
        service_data.append({
            'id': sr.id,
            'start_date': sr.start_date,
            'end_date': sr.end_date,
            'start_location': sr.start_location.name,  # Assuming `name` exists in the Location model
            'end_location': sr.end_location.name,      # Assuming `name` exists in the Location model
            'equipment_type': equipment_type,
            'employee_name': sr.employee.name,         # Assuming `name` exists in the Employee model
            'service_type': sr.service_type.name,      # Assuming `name` exists in the ServiceType model
            'number_of_days': number_of_days,
            'total_cost': request_total,
        })

    context = {
        'service_data': service_data,
        'total_cost': total_cost,
    }

    return render(request, 'finance.html', context)