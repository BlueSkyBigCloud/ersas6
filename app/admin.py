from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import *

admin.site.site_header = _("PROFOROPS ADMIN")  
admin.site.site_title = _("PROFOROPS Admin Portal")
admin.site.index_title = _("Welcome to PROFOROPS ADMIN")

from .models import Stripe_Transaction, ServiceType, ServiceRequest, Employee, Equipment, Location, Directmessage, Posting

@admin.register(Stripe_Transaction)
class Stripe_TransactionAdmin(admin.ModelAdmin):
    list_display = ('invoice_number',)  # Display the name in the admin list view
    search_fields = ('invoice_number',)  # Allow searching by name
    list_filter = ('invoice_number',)  # Filter by name in the sidebar
    readonly_fields = ['stripe_session_id', 'invoice_number', 'amount', 'currency', 'customer_email', 'payment_status']

@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)  # Display the name in the admin list view
    search_fields = ('name',)  # Allow searching by name
    list_filter = ('name',)  # Filter by name in the sidebar
    readonly_fields = ['daily_rate', 'name', 'description', 'created_by_user']

# Admin configuration for ServiceRequest
@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_date', 'end_date', 'start_location', 'end_location', 'service_type')
    list_filter = ('service_type', 'start_date', 'end_date')
    search_fields = ('id', 'start_location__name', 'end_location__name')  # Enable searching by location name
    readonly_fields = ['status', 'invoice', 'created_timestamp', 'created_by_user', 'start_date', 'end_date', 'start_location', 'end_location', 'equipment', 'employee', 'service_type']

@admin.register(EmployeeQualification)
class EmployeeQualificationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'qualification', 'status', 'date_completed', 'expiration_date')
    list_filter = ('status', 'date_completed', 'expiration_date')
    search_fields = ('employee__callsign', 'qualification__name')
    readonly_fields = ['employee', 'qualification', 'status', 'date_completed', 'expiration_date', 'approved_by', 'notes', 'created_at']

@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'rep_count', 'required_approval')
    list_filter = ('type', 'required_approval')
    search_fields = ('name',)
    readonly_fields = ['name', 'type', 'rep_count', 'required_approval', 'field_1', 'field_2', 'field_3', 'date_created']
    
# Admin configuration for Employee
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone_number')
    search_fields = ('first_name', 'last_name')
    readonly_fields = ['company', 'employee_number', 'assigned_user', 'callsign', 'date_hired', 'group', 'created_timestamp', 'created_by_user', 'first_name', 'last_name', 'position', 'phone_number', 'department', 'location', 'status']

# Admin configuration for Equipment
@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    list_filter = ('name',)  # Filter by equipment name
    readonly_fields = ['created_timestamp', 'created_by_user', 'name', 'description', 'category', 'quantity', 'location']

from django.utils.html import format_html


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    # Define the fields you want to display in the list view
    list_display = ('zip', 'latitude', 'longitude', 'description', 'created_by_user', 'created_by_user', 'name', 'address', 'city', 'state', 'country', 'created_timestamp')
    readonly_fields = ('company', 'type', 'zip', 'latitude', 'longitude', 'description', 'created_by_user', 'created_by_user', 'name', 'address', 'city', 'state', 'country', 'created_timestamp')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_by_user', 'primary_user', 'secondary_user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'address')
    readonly_fields = ['id', 'address', 'name', 'created_by_user', 'primary_user', 'secondary_user', 'created_at']


@admin.register(Directmessage)
class DirectmessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'body', 'created_timestamp')
    list_filter = ('created_timestamp',)
    search_fields = ('body', 'id')
    readonly_fields = ['marked_for_deletion', 'created_timestamp', 'created_by_user', 'to_users', 'body']


@admin.register(Posting)
class PostingAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'body')
    list_filter = ('created_timestamp',)
    search_fields = ('subject', 'body')
    readonly_fields = ['created_timestamp', 'created_by_user', 'subject', 'body']


@admin.register(Invitation)
class InvitationsAdmin(admin.ModelAdmin):
    list_display = ('email', 'company')
    list_filter = ('email',)
    readonly_fields = ['email', 'company']

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'text')
    list_filter = ('title',)
    readonly_fields = ['title', 'text', 'service_request']

@admin.register(APIObject)
class APIObjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'created_at')
    list_filter = ('id', 'name', 'description', 'created_at')



from .models import SlideshowImage
admin.site.register(SlideshowImage)