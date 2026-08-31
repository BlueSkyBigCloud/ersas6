import boto3
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth import logout
from .forms import LocationForm
from .models import *
from .forms import *
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
import cryptography
from django.template.loader import render_to_string
from django.core.mail import send_mail
import stripe
from .decorators import onboarded
from business.forms import *

def staff_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect("dashboard")  # 👈 change "home" to your actual home view name
        return view_func(request, *args, **kwargs)
    return _wrapped_view


stripe.api_key = settings.STRIPE_SECRET_KEY

def home1_view(request):
    slides = SlideshowImage.objects.all()
    return render(request, 'home2.html', {'slides': slides})

def security_crm_view(request):
    return render(request, 'security_crm.html')

def security_software_view(request):
    return render(request, 'security_software.html')

def security_solutions_view(request):
    return render(request, 'security_solutions.html')


def home_view(request):
    return render(request, 'home.html')

def start_view(request):
    return render(request, 'start.html')

def products_view(request):
    apk = APKFile.objects.all()
    if request.method == 'POST':
        # Get the selected product option
        product_option = request.POST.get('product_option', None)

        if product_option:
            # Define pricing for each product option
            product_prices = {
                "Pro Plan": 599000,  # Amount in cents for Stripe (e.g., $5990)
                "Pro Plus": 799000,  # Amount in cents for Stripe (e.g., $7990)
            }

            # Ensure the product exists in the price list
            if product_option not in product_prices:
                return redirect('products')  # Handle invalid product choice gracefully

            # Create a Stripe Checkout session
            try:
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    mode='payment',
                    line_items=[
                        {
                            'price_data': {
                                'currency': 'usd',
                                'product_data': {
                                    'name': product_option,
                                },
                                'unit_amount': product_prices[product_option],
                            },
                            'quantity': 1,
                        }
                    ],
                    success_url=request.build_absolute_uri('/success/') + '?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=request.build_absolute_uri('/cancel/'),
                )

                # Redirect to Stripe's hosted checkout page
                return redirect(checkout_session.url)

            except Exception as e:
                # Handle Stripe errors (e.g., log error and display a message)
                print(f"Stripe error: {e}")
                return redirect('products')  # Redirect back to the products page

    # Render the products page for GET requests
    return render(request, 'products.html', {'apk': apk})

def products1_view(request):
    apk = APKFile.objects.all()
    if request.method == 'POST':
        price_id = request.POST.get('price_id', None)

        if price_id:
            try:
                # Create a Stripe Checkout Session for subscriptions
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    mode='subscription',  # <-- FIX: subscription mode
                    line_items=[{
                        'price': price_id,
                        'quantity': 1,
                    }],
                    success_url=request.build_absolute_uri('/success/') + '?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=request.build_absolute_uri('/cancel/'),
                )

                return redirect(checkout_session.url, code=303)

            except Exception as e:
                print(f"Stripe error: {e}")
                return redirect('products')

    return render(request, 'products2.html', {'apk': apk})


def store1_view(request):
    if request.method == "POST":
        # Get user-entered amount (convert dollars to cents)
        try:
            amount_dollars = float(request.POST.get("custom_amount", 0))
            amount_cents = int(amount_dollars * 100)
        except ValueError:
            return redirect("store1")

        if amount_cents <= 0:
            return redirect("store1")

        product_option = "Custom Checkout"

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                mode="payment",
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": product_option},
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }],
                success_url=request.build_absolute_uri("/success/") + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=request.build_absolute_uri("/cancel/"),
            )
            return redirect(checkout_session.url, code=303)

        except Exception as e:
            print(f"Stripe error: {e}")
            return redirect("store1")

    return render(request, "store1.html")


def store_view(request):
    if request.method == 'POST':
        price_id = request.POST.get('price_id', None)

        if price_id:
            try:
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    mode='payment', 
                    line_items=[{
                        'price': price_id,
                        'quantity': 1,
                    }],
                    success_url=request.build_absolute_uri('/success/') + '?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=request.build_absolute_uri('/cancel/'),
                )

                return redirect(checkout_session.url, code=303)

            except Exception as e:
                print(f"Stripe error: {e}")
                return redirect('store')
            
    return render(request, 'store.html')

import os
from django.http import FileResponse, Http404
from file_store.models import APKFile


def download_apk(request, apk_id):
    # Get the APK file instance by its ID
    apk_file = get_object_or_404(APKFile, id=apk_id)
    
    # Create a boto3 client for S3
    s3 = boto3.client('s3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    
    # Define the file's key and the S3 bucket
    file_key = apk_file.file.name  # This gets the relative path like 'apk/app-release.apk'
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    
    # Generate a pre-signed URL to access the file
    url = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': bucket_name, 'Key': file_key},
        ExpiresIn=3600  # 1 hour expiration time
    )
    
    # Redirect to the pre-signed URL to allow the user to download the file
    return redirect(url)

def about_view(request, apk_id=None):
        apk = APKFile.objects.all()
        return render(request, 'about.html', {'apk': apk})



def config_view(request):
    return render(request, 'config.html')

from django.shortcuts import render
from django.db.models import Count, Sum
from .models import Location, Equipment, Employee, ServiceRequest
from django.http import HttpResponse
import csv

from .decorators import onboarded

@login_required
@onboarded()
def reports1_view(request):
    # Check if the user wants to download the report as a CSV file
    if request.GET.get('export') == 'csv':
        # Create the HTTP response with CSV content type
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reports.csv"'

        # Create a CSV writer
        writer = csv.writer(response)

        # Write headers
        writer.writerow(['Location Name', 'Address', 'City', 'State', 'Country', 'Description'])

        locations = Location.objects.filter(created_by_user=request.user)
        for location in locations:
            location.decrypt_fields(request.user)
            writer.writerow([
                location.name or "N/A",
                location.address or "N/A",
                location.city or "N/A",
                location.state or "N/A",
                location.country or "N/A",
                location.description or "N/A",
            ])

        # Fetch and write Equipment data
        writer.writerow([])
        writer.writerow(['Equipment'])
        equipments = Equipment.objects.filter(created_by_user=request.user)
        for equipment in equipments:
            equipment.decrypt_fields(request.user)
            writer.writerow([
                equipment.name or "N/A",
                equipment.category or "N/A",
                equipment.quantity if equipment.quantity is not None else 0,  # Ensuring integer field has a default value
                equipment.location.name if equipment.location else "N/A",
                equipment.created_at or "N/A",
            ])

        # Fetch and write Employee data
        writer.writerow([])
        writer.writerow(['Employees'])
        employees = Employee.objects.filter(created_by_user=request.user)

        for employee in employees:
            employee.decrypt_fields(request.user)
            writer.writerow([
                employee.first_name or "N/A",
                employee.last_name or "N/A",
                employee.assigned_user.email if employee.assigned_user else 0,  # Handle None case
                employee.position or "N/A",
                employee.department or "N/A",
                employee.location.name if employee.location else "N/A",
            ])

        # Fetch and write Service Request data
        writer.writerow([])
        writer.writerow(['Service Requests'])
        service_requests = ServiceRequest.objects.all()
        for service_request in service_requests:
            writer.writerow([
                service_request.id or "N/A",
                service_request.start_date or "N/A",
                service_request.end_date or "N/A",
                service_request.start_location.name if service_request.start_location else "N/A",
                service_request.end_location.name if service_request.end_location else "N/A",
            ])

        return response

    return render(request, 'reports.html')

def logout_view(request):
    logout(request)  # Log the user out
    return redirect('home')  # Redirect to the home page or any desired URL

@login_required
@onboarded()
def account_view(request):
    """
    Redirect users based on their onboarding status and company association.
    Also renders account dashboard with service request summaries.
    """
    user = request.user

    # Redirect if not onboarded or no company
    if not user.is_onboarded:
        if user.company:
            return redirect('dashboard')
        else:
            return redirect('companyonboarding')

    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)

    # Service request counts
    service_requests_today = ServiceRequest.objects.filter(
        created_by_user=user,
        start_date__lte=today,
        end_date__gte=today
    ).count()

    service_requests_week = ServiceRequest.objects.filter(
        created_by_user=user,
        start_date__lte=week_end,
        end_date__gte=week_start
    ).count()

    context = {
        'user': user,
        'total_locations': user.company.locations.count(),
        'total_equipment': user.company.equipments.count(),
        'total_employees': user.company.employees.count(),
        'total_service_requests': ServiceRequest.objects.filter(created_by_user=user).count(),
        'equipment_by_category': user.company.equipments.values('category').annotate(total=Count('id')),
        'employees_by_location': user.company.employees.values('location__name').annotate(count=Count('id')),
        'service_requests_today': service_requests_today,
        'service_requests_week': service_requests_week,
    }

    return render(request, 'dashboard.html', context)


@login_required
@onboarded()
def accountedit_view(request):
    user = request.user  # Get the current logged-in user

    if request.method == 'POST':
        form = CustomUserForm(request.POST, instance=user)  # Pre-fill the form with user data
        if form.is_valid():
            form.save()  # Save the updated user information
            messages.success(request, 'Your account information has been updated successfully.')
            return redirect('account')  # Redirect to the account page after updating
    else:
        form = CustomUserForm(instance=user)  # Display the form with current user data

    return render(request, 'accountedit.html', {'form': form})

@login_required
@onboarded()
def dashboard_view(request):
    user_company = getattr(request.user, 'company', None) 

    total_locations = Location.objects.filter(created_by_user__company=user_company).count()
    total_equipment = Equipment.objects.filter(created_by_user__company=user_company).aggregate(total=Sum('quantity'))['total'] or 0
    total_employees = Employee.objects.filter(company=user_company).count()
    total_service_requests = ServiceRequest.objects.filter(created_by_user__company=user_company).count()


    # Active employees grouped by location
    employees_by_location = (
        Employee.objects.filter(status='ACTIVE')
        .values('location__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Context to pass to the template
    context = {
        'total_locations': total_locations,
        'total_equipment': total_equipment,
        'total_employees': total_employees,
        'total_service_requests': total_service_requests,
        'employees_by_location': employees_by_location,
        'user': request.user,  # Include the logged-in user
    }
    return render(request, 'dashboard.html', context)

@login_required
@onboarded()
def location_list(request):
    # Ensure the user's company attribute exists
    user_company = getattr(request.user, 'company', None)
    if not user_company:
        return render(request, 'location_list.html', {
            'locations': [],
            'message': "No company associated with the current user.",
        })

    # Retrieve and order the QuerySet, filtered by company
    locations = Location.objects.filter(
        created_by_user__company=user_company
    ).order_by('id')

    # Paginate the QuerySet
    paginator = Paginator(locations, 20)  # Show 20 locations per page
    page_number = request.GET.get('page')  # Get the current page number from the query string
    page_obj = paginator.get_page(page_number)  # Get the locations for the current page

    # Decrypt fields for each location only if the company matches
    for location in page_obj.object_list:
        created_by_company = getattr(location.created_by_user, 'company', None)
        if created_by_company == user_company:
            location.decrypt_fields(user=request.user)

    # Check if no locations exist
    message = "No locations found." if not locations.exists() else None

    # Render the template with the context
    return render(request, 'location_list.html', {
        'locations': page_obj.object_list,
        'message': message,
        'page_obj': page_obj,
    })


@login_required
@onboarded()
def location_detail(request, location_id):
    location = get_object_or_404(Location, id=location_id)
    location.decrypt_fields(user=request.user)
    return render(request, 'location_detail.html', {'location': location})


@login_required
@onboarded()
def location_create(request):
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            location.created_by_user = request.user
            try:
                location.save()
                messages.success(request, 'Location successfully created!')
                return redirect('location_list')  # Redirect to location list after success
            except InvalidToken:
                messages.error(request, 'An error occurred while encrypting location data.')
        else:
            messages.error(request, 'There was an error with your form. Please try again.')
    else:
        form = LocationForm()

    return render(request, 'location_form.html', {'form': form})

@login_required
@onboarded()
def company_create(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.created_by_user = request.user
            try:
                company.save()
                messages.success(request, 'Company successfully created!')
                return redirect('company_list')  # Redirect to company list after success
            except InvalidToken:
                messages.error(request, 'An error occurred while encrypting company data.')
        else:
            messages.error(request, 'There was an error with your form. Please try again.')
    else:
        form = CompanyForm()

    return render(request, 'company_form.html', {'form': form})

@login_required
@onboarded()
def company_edit(request, pk):
    company = get_object_or_404(Company, pk=pk)

    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Company details updated successfully!')
                return redirect('company')  # Redirect to the company list or another page
            except InvalidToken:
                messages.error(request, 'An error occurred while saving company data.')
        else:
            messages.error(request, 'There was an error with your form. Please try again.')
    else:
        # Prepopulate the form with the company's existing data
        form = CompanyForm(instance=company)

    return render(request, 'company_form.html', {'form': form})



from cryptography.fernet import InvalidToken
@login_required
@onboarded()
def equipment_list(request):
    # Ensure the user's company attribute exists
    user_company = getattr(request.user, 'company', None)
    if not user_company:
        return render(request, 'equipment_list.html', {
            'equipments': [],
            'message': "No company associated with the current user.",
        })

    # Retrieve and order the QuerySet, filtered by company
    equipments = Equipment.objects.filter(
        created_by_user__company=user_company
    ).order_by('id')

    # Paginate the QuerySet
    paginator = Paginator(equipments, 10)  # Show 10 equipments per page
    page_number = request.GET.get('page')  # Get the current page number from the query string
    page_obj = paginator.get_page(page_number)  # Get the equipments for the current page

    # Decrypt fields for each equipment only if the company matches
    for equipment in page_obj.object_list:
        created_by_company = getattr(equipment.created_by_user, 'company', None)
        if created_by_company == user_company:
            equipment.decrypt_fields(user=request.user)

    # Check if no equipment exists
    message = "No equipment found." if not equipments.exists() else None

    # Render the template with the context
    return render(request, 'equipment_list.html', {
        'equipments': page_obj.object_list,
        'message': message,
        'page_obj': page_obj,
    })


@onboarded()
@login_required
def equipment_detail(request, equipment_id):
    equipment = get_object_or_404(Equipment, id=equipment_id)
    equipment.decrypt_fields(user=request.user)
    return render(request, 'equipment_detail.html', {'equipment': equipment})

from cryptography.fernet import InvalidToken

@onboarded()
@login_required
def equipment_create(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            # Create the Equipment instance but don't save it yet
            equipment = form.save(commit=False)
            equipment.created_by_user = request.user  # Assign the user creating the equipment

            try:
                # Encrypt fields like 'name', 'category', and 'description' if necessary
                if equipment.location:
                    # Assuming location is encrypted, decrypt here if necessary
                    equipment.location = equipment.location
                equipment.save()  # Save the equipment to the database
                messages.success(request, 'Equipment successfully created!')
            except InvalidToken:
                messages.error(request, 'An error occurred while encrypting location data.')
            return redirect('equipment_list')  # Redirect to the list view after creation
        else:
            messages.error(request, 'There was an error with your form. Please try again.')
    else:
        form = EquipmentForm()

    form.fields['location'].queryset = Location.objects.filter(created_by_user=request.user)
    
    # Pass the locations to the form context if needed
    return render(request, 'equipment_form.html', {'form': form})

@onboarded()
@login_required
def equipment_edit(request, equipment_id):
    equipment = get_object_or_404(Equipment, id=equipment_id)
    equipment.decrypt_fields(user=request.user)  # Decrypt fields directly
    
    if request.method == 'POST':
        form = EquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            form.save()  # Save the updated equipment
            return redirect('equipment_detail', equipment_id=equipment.id)  # Redirect to the equipment detail page
    else:
        form = EquipmentForm(instance=equipment)  # Pre-fill the form with existing equipment data
        form.fields['location'].queryset = Location.objects.filter(company=request.user.company)

    return render(request, 'equipment_form.html', {'form': form, 'equipment': equipment})


@onboarded()
@login_required
def equipment_delete(request, equipment_id):  # Accepts pk as an argument
    equipment = get_object_or_404(Equipment, id=equipment_id)  # Uses pk to get the Employee
    try:
        equipment.delete()
        messages.success(request, "Equipment deleted successfully.")
    except ProtectedError:
        messages.error(request, "This equipment cannot be deleted because they are linked to a Service Request.")

    return redirect('equipment_list')

@onboarded()
@login_required
def employee_list(request):

    
    # Ensure the user's company attribute exists
    user_company = getattr(request.user, 'company', None)
    if not user_company:
        return render(request, 'employee_list.html', {
            'employees': [],
            'message': "No company associated with the current user.",
        })

    # Retrieve and order the QuerySet, filtered by company
    employees = Employee.objects.filter(
        company=user_company
    ).order_by('id')  # Explicit ordering to avoid UnorderedObjectListWarning
    # Paginate the QuerySet
    paginator = Paginator(employees, 25)  # Show 10 employees per page
    page_number = request.GET.get('page')  # Get the current page number from the query string
    page_obj = paginator.get_page(page_number)  # Get the employees for the current page

    # Decrypt fields for each employee on the current page
    for employee in page_obj.object_list:
            employee.decrypt_fields(user=request.user)

    # Check if no employees exist
    message = "No employees found." if not employees.exists() else None

    # Render the template with the context
    return render(request, 'employee_list.html', {
        'employees': page_obj.object_list,  # Only pass the current page's employees
        'message': message,
        'page_obj': page_obj,
    })

@onboarded()
@login_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            
            employee = form.save(commit=False)
            employee.created_by_user = request.user  # Associate the employee with the current user
            employee.save()
            messages.success(request, 'Employee successfully created!')
            return redirect('employee_list')  # Redirect to the employee list after saving
        else:
            messages.error(request, 'There was an error with your form. Please try again.')
    else:
        form = EmployeeForm()

        form.fields['location'].queryset = Location.objects.filter(created_by_user=request.user)

        form.fields['assigned_user'].queryset = CustomUser.objects.filter(company=request.user.company)

    return render(request, 'employee_form.html', {'form': form})


@onboarded()
@login_required
def employee_edit(request, employee_id):
    
    employee = get_object_or_404(Employee, id=employee_id)
    employee.decrypt_fields(user=request.user)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()  # Save the updated employee
            return redirect('employee_detail', employee_id=employee.id)  # Redirect to the employee detail page
    else:
        form = EmployeeForm(instance=employee)  # Pre-fill the form with existing employee data

        form.fields['location'].queryset = Location.objects.filter(company=request.user.company)
        form.fields['assigned_user'].queryset = CustomUser.objects.filter(company=request.user.company)

    
    return render(request, 'employee_form.html', {'form': form, 'employee': employee})
from .forms import ServiceRequestForm


@onboarded()
@login_required
def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    employee.decrypt_fields(user=request.user)
    return render(request, 'employee_detail.html', {'employee': employee})

from django.urls import reverse_lazy
from django.views.generic import DeleteView

from django.db.models.deletion import ProtectedError

@onboarded()
@login_required
def employee_delete(request, pk):  # Accepts pk as an argument
    employee = get_object_or_404(Employee, id=pk)  # Uses pk to get the Employee
    try:
        employee.delete()
        messages.success(request, "Employee deleted successfully.")
    except ProtectedError:
        messages.error(request, "This employee cannot be deleted because they are linked to a Service Request.")

    return redirect('employee_list')


@onboarded()
@login_required
def location_edit(request, location_id):

    location = get_object_or_404(Location, id=location_id)
    location.decrypt_fields(user=request.user)
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()  # Save the updated location
            return redirect('location_detail', location_id=location.id)  # Redirect to the location detail page
    else:
        form = LocationForm(instance=location)  # Pre-fill the form with existing location data

    return render(request, 'location_form.html', {'form': form, 'location': location})


@onboarded()
@login_required
def location_delete(request, location_id):  # Accepts pk as an argument
    location = get_object_or_404(Location, id=location_id)  # Uses pk to get the Employee
    try:
        location.delete()
        messages.success(request, "Location deleted successfully.")
    except ProtectedError:
        messages.error(request, "This location cannot be deleted because they are linked to a Service Request.")

    return redirect('location_list')

@onboarded()
@login_required
def create_service_request(request):
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.created_by_user = request.user
            service_request.save()
            return redirect('service_list')
    else:
        form = ServiceRequestForm()

        # Filter based on matching company of the logged-in user and the created_by_user
        company = request.user.company  # Get the logged-in user's company

        form.fields['customer'].queryset = Customer.objects.filter(created_by_user__company=company)
        form.fields['start_location'].queryset = Location.objects.filter(created_by_user__company=company)
        form.fields['end_location'].queryset = Location.objects.filter(created_by_user__company=company)
        form.fields['employee'].queryset = Employee.objects.filter(created_by_user__company=company)
        form.fields['equipment'].queryset = Equipment.objects.filter(created_by_user__company=company)
        form.fields['service_type'].queryset = ServiceType.objects.filter(created_by_user__company=company)
    
    return render(request, 'service_request_form.html', {'form': form})

@onboarded()
@login_required
def edit_service_request(request, id):
    service_request = get_object_or_404(ServiceRequest, id=id)

    if request.method == 'POST':
        form = ServiceRequestForm(request.POST, instance=service_request)
        if form.is_valid():
            form.save()
            return redirect('servicerequest_detail', id=service_request.id)
    else:
        form = ServiceRequestForm(instance=service_request)
        company = request.user.company
        form.fields['customer'].queryset = Customer.objects.filter(created_by_user__company=company)
        form.fields['start_location'].queryset = Location.objects.filter(created_by_user__company=company)
        form.fields['end_location'].queryset = Location.objects.filter(created_by_user__company=company)
        form.fields['employee'].queryset = Employee.objects.filter(created_by_user__company=company)
        form.fields['equipment'].queryset = Equipment.objects.filter(created_by_user__company=company)
        form.fields['service_type'].queryset = ServiceType.objects.filter(created_by_user__company=company)

    return render(request, 'service_request_form.html', {'form': form, 'service_request': service_request})

from .models import ServiceRequest
from django.http import JsonResponse
from django.utils.dateformat import format

import calendar
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta
import calendar
from .models import ServiceRequest
from django.contrib.auth.decorators import login_required
from django.utils.dateformat import format as date_format
from datetime import date, datetime, timedelta
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from app.decorators import onboarded
from app.models import Location, Equipment, Employee, ServiceRequest


@onboarded()
@login_required
def calendar_view(request, year=None, month=None):
    # Get current date if year/month not provided
    today = date.today()
    if year is None or month is None:
        year = today.year
        month = today.month

    # Ensure valid month range
    month = max(1, min(12, month))

    # Get month name
    month_name = date_format(date(year, month, 1), "F")

    # Generate calendar structure
    cal = calendar.Calendar()
    days = [day if day != 0 else 0 for week in cal.monthdayscalendar(year, month) for day in week]

    # Calculate previous and next month for navigation
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    prev_url = reverse('calendar_by_month', args=[prev_year, prev_month])
    next_url = reverse('calendar_by_month', args=[next_year, next_month])

    events = ServiceRequest.objects.filter(start_date__year=year, start_date__month=month)

    event_dict = {}
    for event in events:
        event_dict.setdefault(event.start_date.day, []).append(event)

    sr_count = [0] * 32
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        date_obj = date(year, month, day)
        sr_count[day] = ServiceRequest.objects.filter(start_date__lte=date_obj, end_date__gte=date_obj, created_by_user=request.user).count()

    context = {
        "year": year,
        "month": month,
        "month_name": month_name,
        "days": days,
        "prev_url": prev_url,
        "next_url": next_url,
        "event_dict": event_dict,  
        "sr_count": sr_count, 
    }
    return render(request, "calendar.html", context)

from django.contrib import messages

@onboarded()
@login_required
def calendar_view_date(request, year, month, day):
    date_obj = date(year, month, day)
    service_requests = ServiceRequest.objects.filter(
        start_date__lte=date_obj,
        end_date__gte=date_obj,
        created_by_user=request.user
    )


    for service_request in service_requests:
        service_request.employee.decrypt_fields(user=request.user)
        

    prev_day = date_obj - timedelta(days=1)
    next_day = date_obj + timedelta(days=1)

    context = {
        'year': year,
        'month': month,
        'day': day,
        'date_obj': date_obj,
        'service_requests': service_requests,
        'prev_url': reverse('calendar_by_day', args=[prev_day.year, prev_day.month, prev_day.day]),
        'next_url': reverse('calendar_by_day', args=[next_day.year, next_day.month, next_day.day]),
    }

    return render(request, 'calendar_day.html', context)

@onboarded()
@login_required
def fetch_service_requests(request):
    service_requests = ServiceRequest.objects.all()
    events = []

    for request in service_requests:
        events.append({
            'id': str(request.id),
            'title': str(request.service_type),  # You can customize the title as needed
            'start': request.start_date.isoformat(),  # or use `request.start_date.strftime('%Y-%m-%d')`
            'end': request.end_date.isoformat(),  # same for end date
        })

    return JsonResponse(events, safe=False)

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import ServiceRequest
from .serializers import ServiceRequestSerializer
from django.core.paginator import Paginator
from django.shortcuts import render


@onboarded()   
@login_required
def service_request_list(request):
    services = ServiceRequest.objects.filter(created_by_user=request.user)
    paginator = Paginator(services, 10)  # Show 10 services per page
    page_number = request.GET.get('page')  # Get the current page number from the query string
    page_obj = paginator.get_page(page_number)  # Get the services for the current page

    for service in services:
        service.user=request.user
    if not services:
        message = "No service requests found."
    else:
        message = None
    return render(request, 'service_list.html', {'services': services, 'message': message, 'page_obj': page_obj})

@onboarded()
@login_required
def assign_employee_servicerequest(request, id):
    service_request = ServiceRequest.objects.get(id=id)
    employees = Employee.objects.all()

    if request.method == 'POST':
        employee_id = request.POST.get('employee')
        employee = Employee.objects.get(id=employee_id)
        service_request.assigned_employees.add(employee)
        return redirect('servicerequest_detail', id=service_request.id)

    return render(request, 'assign_employee_servicerequest.html', {
        'employees': employees,
        'service_request': service_request
    })


#SERVicE TYPES
@onboarded()
@login_required
def create_servicetype(request):
    if request.method == 'POST':
        form = ServiceTypeForm(request.POST)
        if form.is_valid():
            servicetype = form.save(commit=False)
            # Optionally, you can associate the created service type with the user
            servicetype.created_by_user = request.user
            servicetype.save()
            # Optionally, add a success message
            messages.success(request, 'Service Type successfully created!')
            return redirect('servicetype_list')  # Redirect to a list of service types
        else:
            # If the form is not valid, optionally add an error message
            messages.error(request, 'There was an error with your form. Please try again.')
    else:
        form = ServiceTypeForm()
    return render(request, 'servicetype_form.html', {'form': form})

@login_required
@onboarded()
def servicetype_list(request):
    # Ensure the user's company attribute exists
    user_company = getattr(request.user, 'company', None)
    if not user_company:
        return render(request, 'servicetype_list.html', {
            'servicetypes': [],
            'message': "No company associated with the current user.",
        })

    # Retrieve and order the QuerySet, filtered by company
    servicetypes = ServiceType.objects.filter(
        created_by_user__company=user_company
    ).order_by('id')

    # Paginate the QuerySet
    paginator = Paginator(servicetypes, 10)  # Show 10 service types per page
    page_number = request.GET.get('page')  # Get the current page number from the query string
    page_obj = paginator.get_page(page_number)  # Get the service types for the current page

    # Decrypt fields for each servicetype only if the company matches
    for servicetype in page_obj.object_list:
        created_by_company = getattr(servicetype.created_by_user, 'company', None)
        if created_by_company == user_company:
            servicetype.decrypt_fields(user=request.user)

    # Check if no service types exist
    message = "No service types found." if not servicetypes.exists() else None

    # Render the template with the context
    return render(request, 'servicetype_list.html', {
        'servicetypes': page_obj.object_list,  # Only pass the current page's service types
        'message': message,
        'page_obj': page_obj,
    })


@onboarded()
@login_required
def servicetype_detail(request, servicetype_id):
    servicetype = get_object_or_404(ServiceType, id=servicetype_id)
    servicetype.decrypt_fields(user=request.user)  
    return render(request, 'servicetype_detail.html', {'servicetype': servicetype})

@onboarded()
@login_required
def servicetype_edit(request, servicetype_id):
    servicetype = get_object_or_404(ServiceType, id=servicetype_id)
    servicetype.decrypt_fields(user=request.user)

    
    if request.method == 'POST':
        form = ServiceTypeForm(request.POST, instance=servicetype)
        if form.is_valid():
            form.save()  # Save the updated location
            return redirect('servicetype_detail', servicetype_id=servicetype.id)  # Redirect to the location detail page
    else:
        form = ServiceTypeForm(instance=servicetype)  # Pre-fill the form with existing location data

    return render(request, 'servicetype_form.html', {'form': form, 'servicetype': servicetype})

@onboarded()
@login_required
def servicetype_delete(request, servicetype_id):  # Accepts pk as an argument
    servicetype = get_object_or_404(ServiceType, id=servicetype_id)  # Uses pk to get the Employee
    try:
        servicetype.delete()
        messages.success(request, "Service Type deleted successfully.")
    except ProtectedError:
        messages.error(request, "This servicetype cannot be deleted because they are linked to a Service Request.")

    return redirect('servicetype_list')

@onboarded()
@login_required
def servicerequest_delete(request, id):
    servicerequest = get_object_or_404(ServiceRequest, id=id)
    
    if request.method == "POST":
        try:
            servicerequest.delete()
            messages.success(request, "Service Request deleted successfully.")
        except ProtectedError:
            messages.error(request, "This Service Request cannot be deleted because it is linked to other records.")
        return redirect('service_list')

    # Optional confirmation page
    return render(request, 'servicerequest_confirm_delete.html', {'servicerequest': servicerequest})

@onboarded()
@login_required
def message_list(request):
    # Fetch Directmessage objects where the user is a recipient
    directmessages = Directmessage.objects.filter(to_users=request.user).distinct()
    sent_messages = Directmessage.objects.filter(created_by_user=request.user).distinct()

    paginator = Paginator(directmessages, 10)  # Show 10 services per page
    page_number = request.GET.get('page')  # Get the current page number from the query string
    page_obj = paginator.get_page(page_number)  # Get the services for the current page

    
    # Decrypt fields for directmessages
    for directmessage in directmessages:
        directmessage.decrypt_fields(user=request.user)

    for sent_message in sent_messages:
        sent_message.decrypt_fields(user=request.user)

    # Fetch all postings
    postings = Posting.objects.all()

    # Decrypt fields for postings
    for posting in postings:
        posting.decrypt_fields(user=request.user)

    # Pass both querysets to the template
    return render(
        request,
        'message_list.html',
        {'directmessages': directmessages, 'sent_messages': sent_messages, 'postings': postings, 'page_obj': page_obj},
    )

@onboarded()
@login_required
def create_posting(request):
    if request.method == 'POST':
        form = PostingForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            # Optionally, you can associate the created service type with the user
            message.created_by_user = request.user
            message.save()
            # Optionally, add a success message
            messages.success(request, 'Service Type successfully created!')
            return redirect('message_list')  # Redirect to a list of service types
        else:
            # If the form is not valid, optionally add an error message
            messages.error(request, 'There was an error with your form. Please try again.')
    else:
        form = DirectmessageForm()
    return render(request, 'message_form.html', {'form': form})

from app.serializers import DirectmessageSerializer

@onboarded()
@login_required
def create_message(request):
    if request.method == 'POST':
        form = DirectmessageForm(request.POST, user=request.user)
        if form.is_valid():
            direct_message = form.save(commit=False)
            direct_message.created_by_user = request.user
            direct_message.save()
            form.save_m2m()
            messages.success(request, 'Message successfully created!')
            return redirect('message_list')
        else:
            messages.error(request, 'There was an error with your form. Please try again.')
    else:
        form = DirectmessageForm(user=request.user)  # Pass the user

    return render(request, 'message_form.html', {'form': form}) 

@onboarded()
@login_required
def registration_view(request):

    if request.user.is_first_login:

        request.user.is_first_login = False
        request.user.save()

        return render(request, 'setupuser.html')

    # Render the regular registration page or other functionality
    return render(request, 'setupuser.html')

from business.models import *

@onboarded()
@login_required
def servicerequest_detail(request, id):
    service_request = get_object_or_404(ServiceRequest, id=id)
    service_request.decrypt_fields(user=request.user)
    if service_request.equipment:
        equipment = service_request.equipment
        # Decrypt only category and description for the equipment, not the name
        equipment.decrypt_fields(user=request.user)
        equipment_name = equipment.name  # This is the unencrypted name

    

    # Fetch notes and invoices associated with the service request
    notes = Note.objects.filter(service_request=service_request)
    invoices = Invoice.objects.filter(service_request=service_request)

    # Decrypt fields for each note
    for note in notes:
        note.decrypt_fields()
    
    # Pass all decrypted data to the template
    return render(
        request, 
        'servicerequest_detail.html', 
        {
            'service_request': service_request,
            'notes': notes,
            'invoices': invoices,
            'equipment_name': equipment_name,
        }
    )


@onboarded()
@login_required
def servicerequest_update(request, id):
    service_request = get_object_or_404(ServiceRequest, id=id)
    return render(request, 'servicerequest_detail.html', {'service_request': service_request})

@login_required
@onboarded()
def company_view(request):
    if request.user.is_authenticated:
        company = request.user.company  # Fetch the user's company
        if company:
            users_in_company = company.customusers.all()  # Access related users via `related_name`
        else:
            users_in_company = []
    else:
        company = None
        users_in_company = []

    return render(request, 'company.html', {
        'company': company,
        'users_in_company': users_in_company,
    })


from django.shortcuts import render
from django.http import HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import secrets
from django.urls import reverse


@onboarded()
@login_required
def create_invite(request):
    if request.method == 'POST':
        input_email = request.POST.get('email') or request.data.get('email')  # Handle both API & Form
        sender = request.user  

        if not input_email:
            if request.content_type == 'application/json':
                return JsonResponse({"error": "Email address is required."}, status=400)
            messages.error(request, "Email address is required.")
            return render(request, 'invite.html')

        # Ensure sender has a company
        if not hasattr(sender, 'company') or not sender.company:
            if request.content_type == 'application/json':
                return JsonResponse({"error": "Sender is not associated with a company."}, status=400)
            return HttpResponse("Sender is not associated with a company.", status=400)

        # Check for duplicate invitations
        existing_invitation = Invitation.objects.filter(email=input_email, company=sender.company).first()
        if existing_invitation:
            if request.content_type == 'application/json':
                return JsonResponse({"error": "Invitation already sent."}, status=400)
            return render(request, 'invite_duplicate.html')

        # Check if the email belongs to an existing user with a company
        assigned_user = CustomUser.objects.filter(email=input_email).first()
        if assigned_user and hasattr(assigned_user, 'company') and assigned_user.company:
            if request.content_type == 'application/json':
                return JsonResponse({"error": "User already belongs to another company."}, status=400)
            return render(request, 'invite_duplicate_company.html')

        # Generate invitation
        token = uuid.uuid4().hex
        Invitation.objects.create(email=input_email, token=token, company=sender.company)

        signup_url = request.build_absolute_uri(
            reverse('signup') + f"?email={input_email}&token={token}"
        )

        # Send email
        invite_content = render_to_string('invite_form.html', {'signup_url': signup_url})
        try:
            send_mail(
                'You are invited!',
                '',
                settings.DEFAULT_FROM_EMAIL,
                [input_email],
                html_message=invite_content
            )
            if request.content_type == 'application/json':
                return JsonResponse({"message": "Invite sent successfully!"}, status=201)
            messages.success(request, "Invite sent successfully!")
            return render(request, 'invite.html')
        except Exception as e:
            if request.content_type == 'application/json':
                return JsonResponse({"error": f"Failed to send invite: {e}"}, status=500)
            messages.error(request, f"Failed to send invite. Error: {e}")
            return render(request, 'invite.html')

    return render(request, 'invite.html')


def companyonboarding_view(request):
    user = request.user
    company = user.company if hasattr(user, "company") else None
    invitation = Invitation.objects.filter(email=user.email, accepted=False).first()

    # Handle company creation
    if request.method == 'POST' and not company:
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.created_by_user = user  # Assign creator
            company.save()
            user.company = company  # Assign new company to user
            user.save()
            messages.success(request, "Company created successfully.")
            return redirect('company')
    else:
        form = CompanyForm()

    if request.method == 'POST' and 'accept_invitation' in request.POST:
        if invitation:
            user.company = invitation.company
            user.save()
            invitation.accepted = True
            invitation.save()
            messages.success(request, f"You have accepted the invitation to join {invitation.company.name}.")
            return redirect('dashboard')  # Redirect after accepting


    # Determine the display case: company, invitation, or create form
    if company:
        display_case = "company_assigned"
    elif invitation:
        display_case = "invitation_pending"
    else:
        display_case = "create_company"

    return render(request, 'companyonboarding.html', {
        'form': form,
        'company': company,
        'invitation': invitation,
        'display_case': display_case,
    })

from django.db.models.signals import post_save
from django.dispatch import receiver
from userpayment.models import UserPayment

@receiver(post_save, sender=UserPayment)
def activate_company_subscription(sender, instance, **kwargs):
    if instance.payment_bool:
        user = instance.app_user
        if hasattr(user, "company") and user.company:
            user.company.is_company_subscription_active = True
            user.company.save()

@onboarded()
@login_required
def location_edit(request, location_id):
    location = get_object_or_404(Location, id=location_id)
    location.decrypt_fields(user=request.user)  # Decrypt fields directly
    

    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()  # Save the updated location
            return redirect('location_detail', location_id=location.id)  # Redirect to the location detail page
    else:
        form = LocationForm(instance=location)  # Pre-fill the form with existing location data

    return render(request, 'location_form.html', {'form': form, 'location': location})


from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse


def accept_invite(request):
    token = request.GET.get('token')
    email = request.GET.get('email')

    # Validate the invitation
    invitation = get_object_or_404(Invitation, token=token, email=email, accepted=False)

    if request.method == 'POST':
        # Get user details from the form
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')

        # Create the user
        CustomUser = CustomUser.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            company=invitation.company  # Associate with the company
        )

        # Mark the invitation as accepted
        invitation.accepted = True
        invitation.save()

        return HttpResponse("Your account has been created! You can now log in.")

    # Render the acceptance form
    return render(request, 'accept_invite.html', {'email': email, 'token': token})


@onboarded()
@login_required
def add_note(request, id):
    service_request = get_object_or_404(ServiceRequest, id=id)
    service_request = service_request
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.created_by_user = request.user
            note.service_request = service_request 
            try:
                note.save()
                messages.success(request, 'Note successfully created!')
                return redirect('service_list')
            except InvalidToken:
                messages.error(request, 'An error occurred while encrypting location data.')
        else:
            messages.error(request, 'There was an error with your form. Please try again.')
    else:
        form = NoteForm()
    return render(request, 'note_form.html', {'form': form, 'service_request': service_request})


def businesspartners_view(request):
    return render(request, 'businesspartners.html')


from django.core.files.storage import FileSystemStorage

import io
from django.db.utils import IntegrityError
@onboarded()
@login_required
def validate_date_hired(date_str):
    if not date_str or date_str == "":  # Check for empty or invalid date
        return None  # Return None for invalid dates
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()  # Convert to date object
    except ValueError:
        return None  # Return None if date format is invalid

@staff_required
@onboarded()
@login_required
def bulkupload_employee_view(request):
    if request.method == "POST" and request.FILES.get("file"):
        csv_file = request.FILES["file"]
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Error: The uploaded file is not a CSV.")
            return redirect('bulkuploademployees')

        data_set = csv_file.read().decode('utf-8')
        io_string = io.StringIO(data_set)
        reader = csv.reader(io_string)
        header = next(reader, None)  # Skip header row

        if header is None:
            messages.error(request, "Error: CSV file is empty or has no header.")
            return redirect('bulkuploademployees')

        employees = []
        existing_employee_numbers = set(Employee.objects.values_list('employee_number', flat=True))
        duplicate_entries = []
        row_errors = []

        for i, row in enumerate(reader, start=2):  # Start at row 2 (considering header)
            try:
                if len(row) < 9:
                    row_errors.append(f"Row {i}: Missing required fields.")
                    continue

                employee_number = row[0]
                if employee_number in existing_employee_numbers:
                    # Handle duplicate employee number, either skip or assign a new one
                    new_employee_number = get_next_employee_number(employee_number)
                    duplicate_entries.append(f"{employee_number} (assigned new number {new_employee_number})")
                    employee_number = new_employee_number  # Assign the new employee number

                user_company = request.user.company

                # Encrypt sensitive fields
                encrypted_first_name = encrypt(row[1])
                encrypted_last_name = encrypt(row[2])
                callsign = row[3]
                encrypted_phone_number = encrypt(row[4]) if row[4] else None
                encrypted_position = encrypt(row[5])
                encrypted_department = encrypt(row[6])
                encrypted_group = encrypt(row[7])

                # Handle date format error
                try:
                    date_hired = datetime.strptime(row[8], '%Y-%m-%d').date()
                except ValueError:
                    row_errors.append(f"Row {i}: Invalid date format for 'Date Hired'. Use YYYY-MM-DD format.")
                    continue

                # Append employee with encrypted fields
                employees.append(Employee(
                    employee_number=employee_number,
                    first_name=encrypted_first_name,
                    last_name=encrypted_last_name,
                    callsign=callsign,
                    phone_number=encrypted_phone_number,
                    position=encrypted_position,
                    department=encrypted_department,
                    group=encrypted_group,
                    date_hired=date_hired,
                    company=user_company,
                    created_by_user=request.user 
                ))

            except Exception as e:
                row_errors.append(f"Row {i}: {str(e)}")

        try:
            # Attempt to bulk create employee records
            Employee.objects.bulk_create(employees)
            messages.success(request, f"Successfully uploaded {len(employees)} employees.")
        except IntegrityError as e:
            print(f"IntegrityError: {str(e)}")  # Print the database error
            messages.error(request, f"Database error: {str(e)}")
            return redirect('bulkuploademployees')

        if duplicate_entries:
            messages.warning(request, f"Skipped or modified {len(duplicate_entries)} duplicate entries: {', '.join(duplicate_entries[:5])}...")

        if row_errors:
            for error in row_errors:
                messages.error(request, error)

        return redirect('bulkuploademployees')

    return render(request, "bulkuploademployees.html")

@onboarded()
@login_required
def get_next_employee_number(existing_number):
    """
    Generate the next available employee number.
    Assumes employee_number is in a format that can be incremented (e.g., "EMP001", "EMP002").
    """
    prefix = existing_number[:3]  # Assuming first 3 chars are prefix (e.g., "EMP")
    base_number = int(existing_number[3:])  # Assuming remaining part is numeric (e.g., 1, 2, 3)
    
    new_number = f"{prefix}{base_number + 1:03}"  # Increment number and pad with leading zeros
    
    while Employee.objects.filter(employee_number=new_number).exists():
        base_number += 1
        new_number = f"{prefix}{base_number + 1:03}"

    return new_number

@staff_required
@onboarded()
@login_required
def bulkupload_view(request):
    return render(request,'bulkupload.html')

@staff_required
@onboarded()
@login_required
def bulkupload_equipment_view(request):
    if request.method == "POST" and request.FILES.get("file"):
        csv_file = request.FILES["file"]

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Error: The uploaded file is not a CSV.")
            return redirect('bulkuploadequipment')

        data_set = csv_file.read().decode('utf-8')
        io_string = io.StringIO(data_set)
        reader = csv.reader(io_string)
        header = next(reader, None)

        if header is None:
            messages.error(request, "Error: CSV file is empty or has no header.")
            return redirect('bulkuploadequipment')

        equipments = []
        existing_names = set(Equipment.objects.values_list('name', flat=True))
        row_errors = []

        for i, row in enumerate(reader, start=2):  # Start at row 2 (after header)
            try:
                if len(row) < 5:
                    row_errors.append(f"Row {i}: Missing required fields.")
                    continue

                name = row[0]
                description = row[1]
                category = row[2]
                quantity = int(row[3]) if row[3].isdigit() else 0
                location_name = row[4]

                if name in existing_names:
                    row_errors.append(f"Row {i}: Equipment '{name}' already exists.")
                    continue

                # Fetch location object
                try:
                    location = Location.objects.get(name=location_name)
                except Location.DoesNotExist:
                    row_errors.append(f"Row {i}: Location '{location_name}' not found.")
                    continue

                # Encrypt sensitive fields
                encrypted_category = encrypt(category)
                encrypted_description = encrypt(description)

                equipments.append(Equipment(
                    name=name,
                    description=encrypted_description,
                    category=encrypted_category,
                    quantity=quantity,
                    location=location,
                    company=request.user.company,  
                    created_by_user=request.user
                ))

            except Exception as e:
                row_errors.append(f"Row {i}: {str(e)}")

        try:
            Equipment.objects.bulk_create(equipments)
            messages.success(request, f"Successfully uploaded {len(equipments)} equipment entries.")
        except IntegrityError as e:
            messages.error(request, f"Database error: {str(e)}")
            return redirect('bulkuploadequipment')

        if row_errors:
            for error in row_errors[:5]:  # Limit displayed errors
                messages.error(request, error)

        return redirect('bulkuploadequipment')

    return render(request, "bulkuploadequipment.html")

@staff_required
@onboarded()
@login_required
def bulkupload_location_view(request):
    if request.method == "POST" and request.FILES.get("file"):
        csv_file = request.FILES["file"]

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Error: The uploaded file is not a CSV.")
            return redirect('bulkuploadlocations')

        data_set = csv_file.read().decode('utf-8')
        io_string = io.StringIO(data_set)
        reader = csv.reader(io_string)
        header = next(reader, None)  # Read header row

        if header is None:
            messages.error(request, "Error: CSV file is empty or has no header.")
            return redirect('bulkuploadlocations')

        locations = []
        existing_names = set(Location.objects.values_list('name', flat=True))
        row_errors = []

        for i, row in enumerate(reader, start=2):  # Start at row 2 (after header)
            try:
                if len(row) < 3:
                    row_errors.append(f"Row {i}: Missing required fields.")
                    continue

                name = row[0]
                address = row[1]
                location_type = row[2]  # Internal, Customer, Other

                if name in existing_names:
                    row_errors.append(f"Row {i}: Location '{name}' already exists.")
                    continue

                # Encrypt sensitive fields
                encrypted_address = encrypt(address)
                encrypted_location_type = encrypt(location_type)

                locations.append(Location(
                    name=name,
                    address=encrypted_address,
                    location_type=encrypted_location_type,
                    company=request.user.company,
                    created_by_user=request.user
                ))

            except Exception as e:
                row_errors.append(f"Row {i}: {str(e)}")

        try:
            Location.objects.bulk_create(locations)
            messages.success(request, f"Successfully uploaded {len(locations)} locations.")
        except IntegrityError as e:
            messages.error(request, f"Database error: {str(e)}")
            return redirect('bulkuploadlocations')

        if row_errors:
            for error in row_errors[:5]:  # Limit displayed errors
                messages.error(request, error)

        return redirect('bulkuploadlocations')

    return render(request, "bulkuploadlocations.html")


import requests
from django.conf import settings
from django.shortcuts import render


@staff_required
@onboarded()
@login_required
def iplookup_view(request):
    result = None
    if request.method == "POST":
        ip_address = request.POST.get('ip_address')
        api_key = os.environ.get('YOUR_IPINFO_API_KEY') 
        url = f"https://ipinfo.io/{ip_address}?token={api_key}"
        
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
        else:
            result = {"error": "Unable to fetch IP information."}

    return render(request, 'iplookup.html', {'result': result})


COUPON_MAP = {
    "DFW2025": "promo_1S8qNmGLcTDJWbqV0GuDEWMx",
}


def store_view3(request):
    products = Product.objects.all()

    if request.method == 'POST':
        # -----------------------------
        # Collect user / guest info
        # -----------------------------
        guest_email = request.POST.get('guest_email', '').strip()
        guest_name = request.POST.get('guest_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        coupon_code = request.POST.get('coupon_code', '').upper()
        same_as_billing = request.POST.get('same_as_billing') == 'on'

        if not request.user.is_authenticated and not guest_email:
            return render(request, 'store3.html', {
                'products': products,
                'error': 'Please provide your email.'
            })

        # -----------------------------
        # Create Billing Address
        # -----------------------------
        billing_address = Address.objects.create(
            full_name=guest_name,
            line1=request.POST.get('line1', ''),
            line2=request.POST.get('line2', ''),
            city=request.POST.get('city', ''),
            state=request.POST.get('state', ''),
            postal_code=request.POST.get('postal_code', ''),
            country=request.POST.get('country', ''),
            phone_number=phone,
        )

        # -----------------------------
        # Create Shipping Address
        # -----------------------------
        if same_as_billing:
            shipping_address = billing_address
        else:
            shipping_address = Address.objects.create(
                full_name=request.POST.get('ship_name', guest_name),
                line1=request.POST.get('ship_line1', ''),
                line2=request.POST.get('ship_line2', ''),
                city=request.POST.get('ship_city', ''),
                state=request.POST.get('ship_state', ''),
                postal_code=request.POST.get('ship_postal_code', ''),
                country=request.POST.get('ship_country', ''),
                phone_number=phone,
            )

        # -----------------------------
        # Create Order
        # -----------------------------
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            guest_email=guest_email if not request.user.is_authenticated else None,
            guest_name=guest_name if not request.user.is_authenticated else None,
            is_guest_order=not request.user.is_authenticated,
            shipping_address=shipping_address,
            billing_address=billing_address,
        )

        # -----------------------------
        # Build Line Items & OrderItems
        # -----------------------------
        line_items = []
        order_items = []

        for product in products:
            quantities = request.POST.getlist(f'quantity_{product.id}[]')
            size_ids = request.POST.getlist(f'size_{product.id}[]')
            color_ids = request.POST.getlist(f'color_{product.id}[]')

            for i, qty in enumerate(quantities):
                if not qty or not qty.isdigit() or int(qty) <= 0:
                    continue
                qty = int(qty)
                size_obj = ProductSize.objects.filter(id=size_ids[i]).first() if i < len(size_ids) else None
                color_obj = ProductColor.objects.filter(id=color_ids[i]).first() if i < len(color_ids) else None

                # Use Stripe Price ID if available
                if not product.stripe_price_id:
                    continue  # skip products without a Stripe Price ID

                line_items.append({
                    "price": product.stripe_price_id,
                    "quantity": qty
                })

                order_items.append({
                    "product": product,
                    "quantity": qty,
                    "size_obj": size_obj,
                    "color_obj": color_obj
                })

        if not line_items:
            return render(request, 'store3.html', {
                'products': products,
                'error': 'Please select at least one product with a valid Stripe price.'
            })

        # -----------------------------
        # Save OrderItems
        # -----------------------------
        for item in order_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                selected_size=item['size_obj'],
                selected_color=item['color_obj'],
            )

        # -----------------------------
        # Prepare Stripe Discounts
        # -----------------------------
        discounts = []
        if coupon_code in COUPON_MAP:
            discounts = [{"promotion_code": COUPON_MAP[coupon_code]}]

        # -----------------------------
        # Create Stripe Checkout Session
        # -----------------------------
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                mode='payment',
                line_items=line_items,
                customer_email=guest_email if not request.user.is_authenticated else request.user.email,
                success_url=request.build_absolute_uri('/success/') + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri('/cancel/'),
                metadata={
                    'order_id': str(order.id),
                    'guest_name': guest_name,
                    'phone': phone,
                },
                discounts=discounts,
                allow_promotion_codes=True,
            )
        except stripe.error.StripeError as e:
            return render(request, 'store3.html', {
                'products': products,
                'error': f"Stripe error: {getattr(e, 'user_message', str(e))}"
            })

        return redirect(checkout_session.url, code=303)

    return render(request, 'store3.html', {'products': products})


from django.shortcuts import render, redirect
from business.models import *
from app.utils.cart_utils import get_cart, add_to_cart, remove_from_cart, save_cart
from users.utils import generate_coupon_code
from stripe import StripeError, InvalidRequestError

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .decorators import onboarded
import stripe
from stripe import StripeError, InvalidRequestError
from users.utils import generate_coupon_code  # your helper function

@onboarded()
@login_required
def generate_promo_code(request):
    user = request.user

    try:
        # If the user already has a coupon, use it; otherwise create one
        if not user.coupon_code:
            # Create a Stripe Coupon
            coupon = stripe.Coupon.create(
                percent_off=10,  # 10% discount
                duration="once",
            )
            user.coupon_code = coupon.id
            user.save()

        # Now create a Promotion Code linked to that coupon
        promo_code = stripe.PromotionCode.create(
            code=f"{user.coupon_code.upper()}PROMO",  # optional custom code
            promotion={
                "type": "coupon",
                "coupon": user.coupon_code,
            }
        )

        # Store the promotion code ID on the user if desired
        user.promotion_code = promo_code.id
        user.save()

        messages.success(request, f"Promo code created: {promo_code.code}")
    except stripe.StripeError as e:
        messages.error(request, f"Stripe error: {e.user_message or str(e)}")

    return redirect("dashboard")




def store_view4(request):
    """Display store page and session-based cart."""
    products = Product.objects.all()
    cart = request.session.get('cart', {})

    items = []
    total_price = 0
    invalid_keys = []

    for key, entry in cart.items():
        # Validate entry structure
        if not isinstance(entry, dict) or 'product_id' not in entry:
            invalid_keys.append(key)
            continue

        try:
            product = Product.objects.get(id=entry['product_id'])
        except Product.DoesNotExist:
            invalid_keys.append(key)
            continue

        size = ProductSize.objects.filter(id=entry.get('size_id')).first() if entry.get('size_id') else None
        color = ProductColor.objects.filter(id=entry.get('color_id')).first() if entry.get('color_id') else None
        qty = int(entry.get('quantity', 1))
        subtotal = qty * float(product.price)
        total_price += subtotal

        items.append({
            'key': key,
            'product': product,
            'size': size,
            'color': color,
            'quantity': qty,
            'subtotal': subtotal
        })

    # Clean up invalid entries from cart
    if invalid_keys:
        for k in invalid_keys:
            cart.pop(k, None)
        request.session['cart'] = cart
        request.session.modified = True

    return render(request, 'store4.html', {
        'products': products,
        'cart_items': items,
        'total_price': total_price
    })



def add_to_cart(request, product_id):
    if request.method == "POST":
        quantity = int(request.POST.get('quantity', 1))
        size_id = request.POST.get('size_id')  # NEW
        color_id = request.POST.get('color_id')  # NEW

        key = f"{product_id}-{size_id or '0'}-{color_id or '0'}"

        cart = request.session.get('cart', {})

        if key in cart:
            # Increment quantity and update size/color if changed
            cart[key]['quantity'] += quantity
            if size_id:
                cart[key]['size_id'] = int(size_id)
            if color_id:
                cart[key]['color_id'] = int(color_id)
        else:
            cart[key] = {
                'product_id': product_id,
                'quantity': quantity,
                'size_id': int(size_id) if size_id else None,
                'color_id': int(color_id) if color_id else None,
            }

        request.session['cart'] = cart
        request.session.modified = True

        total_items = sum(item['quantity'] for item in cart.values())
        return JsonResponse({'cart_count': total_items})

    return JsonResponse({'error': 'Invalid request'}, status=400)

def remove_from_cart(request):
    if request.method == "POST":
        key = request.POST.get('key')
        cart = request.session.get('cart', {})
        if key in cart:
            del cart[key]
        request.session['cart'] = cart
        request.session.modified = True
        total_items = sum(item['quantity'] for item in cart.values())
        return JsonResponse({'cart_count': sum(i['quantity'] for i in cart.values())})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def view_cart(request):
    """Display cart page and handle checkout."""
    cart = request.session.get('cart', {})
    items = []

    for key, entry in cart.items():
        product = Product.objects.get(id=entry['product_id'])
        size = ProductSize.objects.filter(id=entry.get('size_id')).first() if entry.get('size_id') else None
        color = ProductColor.objects.filter(id=entry.get('color_id')).first() if entry.get('color_id') else None
        qty = int(entry.get('quantity', 0))
        subtotal = qty * float(product.price)
        items.append({
            'key': key,
            'product': product,
            'size': size,
            'color': color,
            'quantity': qty,
            'subtotal': subtotal
        })

    if request.method == "POST":
        # Collect billing/shipping info
        guest_name = request.POST.get('guest_name', '').strip()
        guest_email = request.POST.get('guest_email', '').strip()
        phone = request.POST.get('phone', '').strip()
        same_as_billing = request.POST.get('same-as-billing') == 'on'
        promo_code = request.POST.get('promo_code', '').upper()

        # Validate size/color for items
        for item in items:
            if item['product'].sizes.exists() and not item['size']:
                return render(request, 'cart.html', {'items': items, 'error': f"Select size for {item['product'].name}"})
            if item['product'].colors.exists() and not item['color']:
                return render(request, 'cart.html', {'items': items, 'error': f"Select color for {item['product'].name}"})

        # Billing address
        billing_address = Address.objects.create(
            full_name=guest_name,
            line1=request.POST.get('line1', ''),
            line2=request.POST.get('line2', ''),
            city=request.POST.get('city', ''),
            state=request.POST.get('state', ''),
            postal_code=request.POST.get('postal_code', ''),
            country=request.POST.get('country', ''),
            phone_number=phone
        )

        shipping_address = billing_address if same_as_billing else Address.objects.create(
            full_name=request.POST.get('ship_name', guest_name),
            line1=request.POST.get('ship_line1', ''),
            line2=request.POST.get('ship_line2', ''),
            city=request.POST.get('ship_city', ''),
            state=request.POST.get('ship_state', ''),
            postal_code=request.POST.get('ship_postal_code', ''),
            country=request.POST.get('ship_country', ''),
            phone_number=phone
        )

        # Create Order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            guest_name=guest_name if not request.user.is_authenticated else None,
            guest_email=guest_email if not request.user.is_authenticated else None,
            is_guest_order=not request.user.is_authenticated,
            billing_address=billing_address,
            shipping_address=shipping_address
        )

        stripe_line_items = []
        for item in items:
            qty = int(item['quantity'])
            if not item['product'].stripe_price_id:
                continue
            stripe_line_items.append({
                'price': item['product'].stripe_price_id,
                'quantity': qty
            })
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=qty,
                selected_size=item['size'],
                selected_color=item['color']
            )

        if not stripe_line_items:
            return render(request, 'cart.html', {'items': items, 'error': "No valid items to checkout."})

        discounts = [{"promotion_code": COUPON_MAP[promo_code]}] if promo_code in COUPON_MAP else []

        # Stripe Checkout
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            line_items=stripe_line_items,
            customer_email=guest_email if not request.user.is_authenticated else request.user.email,
            success_url=request.build_absolute_uri('/success/') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri('/cancel/'),
            metadata={'order_id': str(order.id), 'guest_name': guest_name, 'phone': phone},
            discounts=discounts,
            allow_promotion_codes=True
        )

        return redirect(checkout_session.url, code=303)

    return render(request, 'cart.html', {'items': items})

from django.db import IntegrityError, transaction
from prospects.models import Prospect, Action


import csv
import io
import re
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.shortcuts import render, redirect

from prospects.models import Prospect, Action

def safe_get(row, field):
    return (row.get(field) or "").strip()


import csv, io, uuid
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from prospects.models import Prospect, Action

@onboarded()
@staff_required
@login_required
def bulkupload_prospect_view(request):
    if request.method == "POST" and request.FILES.get("file"):
        csv_file = request.FILES["file"]

        if not csv_file.name.endswith(".csv"):
            messages.error(request, "Error: The uploaded file is not a CSV.")
            return redirect("bulkupprospects")

        # Read and decode
        data_set = csv_file.read().decode("utf-8")
        io_string = io.StringIO(data_set)
        reader = csv.DictReader(io_string, delimiter=",")

        # --- Clean BOM + whitespace from headers ---
        reader.fieldnames = [name.lstrip("\ufeff").strip() for name in reader.fieldnames]
        print(f"[UPLOAD] Cleaned headers: {reader.fieldnames}")

        prospects = []
        actions = []
        row_errors = []
        duplicate_entries = []

        existing_emails = set(
            Prospect.objects.values_list("email", flat=True)
        )
        print(f"[UPLOAD] Existing emails in DB: {len(existing_emails)}")

        for i, row in enumerate(reader, start=2):  # start=2 because row 1 = header
            try:
                # Normalize values
                company = row.get("Company", "").strip()
                business_type = row.get("Business Type", "").strip()
                address = row.get("Address", "").strip()
                contact = row.get("Contact", "").strip()
                phone = row.get("Phone", "").strip()
                website = row.get("Website", "").strip()
                email = row.get("Email", "").strip()
                products = row.get("Products", "").strip()
                company_size = row.get("Company Size", "").strip()
                note1 = row.get("Notes", "").strip()
                note2 = row.get("Notes2", "").strip()

                print(f"[ROW {i}] Company='{company}', Email='{email}', Notes='{note1[:30]}|{note2[:30]}'")

                if not company:
                    row_errors.append(f"Row {i}: Missing company name.")
                    print(f"[ROW {i}] ❌ Missing company name, skipped")
                    continue

                # Skip duplicate emails
                if email and email in existing_emails:
                    duplicate_entries.append(email)
                    print(f"[ROW {i}] ⚠️ Duplicate email '{email}', skipped")
                    continue

                # Prospect instance
                prospect = Prospect(
                    created_by_user=request.user,
                    name=company,
                    business_type=business_type,
                    contact=contact,
                    website=website,
                    address=address,
                    products=products,
                    company_size=company_size,
                    email=email if email else None,
                    phone_number=phone if phone else None,
                    account_rep="",
                    status="NEW",
                )
                prospects.append(prospect)
                print(f"[ROW {i}] Prospect staged: {company}")

                if email:
                    existing_emails.add(email)

                # Collect notes for actions
                if note1:
                    actions.append((prospect, note1))
                if note2:
                    actions.append((prospect, note2))

            except Exception as e:
                row_errors.append(f"Row {i}: {str(e)}")
                print(f"[ROW {i}] ❌ Error: {str(e)}")

        try:
            with transaction.atomic():
                created_prospects = Prospect.objects.bulk_create(prospects)
                print(f"[UPLOAD] Bulk created {len(created_prospects)} prospects")

                action_objs = []
                for prospect, note_text in actions:
                    created = next(
                        (p for p in created_prospects if p.name == prospect.name and p.email == prospect.email),
                        None
                    )
                    if created:
                        action_objs.append(
                            Action(
                                prospect=created,
                                action_type="NOTE",
                                description=note_text,
                                created_by_user=request.user,
                            )
                        )

                if action_objs:
                    Action.objects.bulk_create(action_objs)
                print(f"[UPLOAD] Bulk created {len(action_objs)} actions")

            messages.success(
                request,
                f"✅ Uploaded {len(prospects)} prospects and {len(actions)} notes."
            )

        except IntegrityError as e:
            messages.error(request, f"Database error: {str(e)}")
            print(f"[UPLOAD] ❌ Database error: {str(e)}")
            return redirect("bulkupprospects")

        if duplicate_entries:
            msg = f"⚠️ Skipped {len(duplicate_entries)} duplicates (emails)"
            messages.warning(request, msg)
            print(f"[UPLOAD] {msg} -> {duplicate_entries[:5]}")

        if row_errors:
            for error in row_errors:
                messages.error(request, error)
            print(f"[UPLOAD] Row errors: {row_errors}")

        return redirect("bulkupprospects")

    return render(request, "bulkuploadprospects.html")



from priceanalysis.models import Analysis_ZipPrice, Analysis_State, Analysis_ServiceType
from .decorators import onboarded  # your onboarded decorator


BULK_CHUNK_SIZE = 1000  # Number of rows to insert per bulk_create


@staff_required
@onboarded()
@login_required
def bulkpricing_upload(request):
    """
    Efficient, atomic CSV upload for Analysis_ZipPrice.
    The entire upload is committed only if no critical errors occur.
    """
    if request.method == "POST" and request.FILES.get("file"):
        csv_file = request.FILES["file"]

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Error: The uploaded file is not a CSV.")
            return redirect('bulkpricing_upload')

        try:
            data_set = csv_file.read().decode('utf-8')
            io_string = io.StringIO(data_set)
            reader = csv.reader(io_string)
            header = next(reader, None)
        except Exception as e:
            messages.error(request, f"Error reading CSV: {str(e)}")
            return redirect('bulkpricing_upload')

        if header is None:
            messages.error(request, "CSV file is empty or missing header.")
            return redirect('bulkpricing_upload')

        row_errors = []
        batch = []

        # Cache service types and states
        service_type_cache = {}
        state_cache = {}

        try:
            with transaction.atomic():  # Begin atomic transaction
                for i, row in enumerate(reader, start=2):
                    if len(row) < 6:
                        row_errors.append(f"Row {i}: Missing required fields.")
                        continue

                    zip_code, state_code, service_type_name, avg_raw, min_raw, max_raw = row[:6]

                    # Validate prices
                    try:
                        avg_price = float(avg_raw)
                        min_price = float(min_raw)
                        max_price = float(max_raw)
                    except ValueError:
                        row_errors.append(f"Row {i}: Invalid price values.")
                        continue

                    # Get or create service type
                    if service_type_name in service_type_cache:
                        service_type_obj = service_type_cache[service_type_name]
                    else:
                        service_type_obj, _ = Analysis_ServiceType.objects.get_or_create(name=service_type_name)
                        service_type_cache[service_type_name] = service_type_obj

                    # Get or create state
                    state_code_upper = state_code.upper()
                    if state_code_upper in state_cache:
                        state_obj = state_cache[state_code_upper]
                    else:
                        state_obj, _ = Analysis_State.objects.get_or_create(
                            code=state_code_upper,
                            defaults={"name": state_code_upper}
                        )
                        state_cache[state_code_upper] = state_obj

                    # Add to batch
                    batch.append(Analysis_ZipPrice(
                        zip_code=zip_code,
                        state=state_obj,
                        service_type=service_type_obj,
                        avg_price=avg_price,
                        min_price=min_price,
                        max_price=max_price
                    ))

                    # Insert in chunks
                    if len(batch) >= BULK_CHUNK_SIZE:
                        Analysis_ZipPrice.objects.bulk_create(batch)
                        batch = []

                # Insert any remaining rows
                if batch:
                    Analysis_ZipPrice.objects.bulk_create(batch)

        except IntegrityError as e:
            messages.error(request, f"Critical database error: {str(e)}. No data has been saved.")
            return redirect('bulkpricing_upload')

        # Show first 5 row errors (non-critical)
        for error in row_errors[:5]:
            messages.error(request, error)

        messages.success(request, "Pricing CSV uploaded successfully!")
        return redirect('bulkpricing_upload')

    return render(request, "bulkpricing_upload.html")


@onboarded()
@login_required
def cost_sheet_view(request, service_request_id):
    service_request = get_object_or_404(ServiceRequest, id=service_request_id)
    
    # Try to find existing cost sheet for this service request
    cost_sheet, created = CostSheet.objects.get_or_create(
        service_request=service_request,
        defaults={
            'employee': service_request.employee,
            'equipment': service_request.equipment,
            'location': service_request.start_location,
            'service_type': service_request.service_type,
            'start_date': service_request.start_date,
            'end_date': service_request.end_date,
            'created_by_user': request.user,
        }
    )

    return render(request, 'cost_sheet_detail.html', {
        'cost_sheet': cost_sheet,
        'service_request': service_request,
        'created': created
    })

@onboarded()
@login_required
def cost_sheet_edit(request, service_request_id):
    service_request = get_object_or_404(ServiceRequest, id=service_request_id)
    cost_sheet = get_object_or_404(CostSheet, service_request=service_request)

    if request.method == "POST":
        form = CostSheetForm(request.POST, instance=cost_sheet)
        if form.is_valid():
            form.save()
            return redirect('cost_sheet_view', service_request_id=service_request.id)
    else:
        form = CostSheetForm(instance=cost_sheet)

    return render(request, 'cost_sheet_edit.html', {
        'form': form,
        'cost_sheet': cost_sheet,
        'service_request': service_request
    })