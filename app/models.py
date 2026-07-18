import uuid
from django.db import models
from app.encryption import encrypt, decrypt
from users.models import CustomUser
from django.conf import settings
from app.utils import *
from datetime import datetime
from users.models import *
from googlemap.models import *



class Location(models.Model):
    TYPE_CHOICES = [
        ('Internal', 'Internal'),
        ('Customer', 'Customer'),
        ('Other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        'app.Company', 
        on_delete=models.CASCADE, 
        related_name='locations', 
        null=True, 
        blank=True
    )
    created_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_timestamp = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=300)
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=300)
    zip = models.IntegerField()
    state = models.CharField(max_length=300)
    country = models.CharField(max_length=300)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='Other')
    latitude = models.FloatField(null=True, blank=True)  # Latitude field
    longitude = models.FloatField(null=True, blank=True)  # Longitude field


    def save(self, *args, **kwargs):
        if self.created_by_user and not self.company:
            self.company = self.created_by_user.company

        if self.name:
            self.name = self.name
        if self.address:
            self.address = encrypt(self.address)
        if self.city:
            self.city = encrypt(self.city)
        if self.state:
            self.state = encrypt(self.state)
        if self.country:
            self.country = encrypt(self.country)
        if self.description:
            self.description = encrypt(self.description)


        super().save(*args, **kwargs)

    # Method to decrypt fields
    def decrypt_fields(self, user=None):
        if user and self.created_by_user and self.created_by_user.company == user.company:
        
            try:
                self.name = self.name  # Not encrypted
                self.address = decrypt(self.address)
                self.city = decrypt(self.city)
                self.state = decrypt(self.state) 
                self.country = decrypt(self.country)
                if self.description:
                    self.description = decrypt(self.description)

                return True
            except Exception as e:
                return False
    
    def __str__(self):
        try:
            if self.name:
                return str(self.name)  # Name is not encrypted in this model
        except Exception as e:
            return f"Location {self.id}"



class Equipment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    make = models.TextField(blank=True, null=True)
    model = models.TextField(blank=True, null=True)
    stock_number = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100)
    year = models.PositiveIntegerField(default=1990)
    miles_hours = models.PositiveIntegerField(default=0000)
    quantity = models.PositiveIntegerField(default=0)
    location = models.ForeignKey('Location', on_delete=models.CASCADE)  # Assuming Location model exists
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    loc_last_updated = models.DateTimeField(null=True, blank=True)
    
    company = models.ForeignKey(
        'app.Company', 
        on_delete=models.CASCADE, 
        related_name='equipments', 
        null=True, 
        blank=True
    )


    created_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.category:
            self.category = encrypt(self.category)
        if self.description:
            self.description = encrypt(self.description) # Add this field to store encrypted location
        super().save(*args, **kwargs)
    
    def decrypt_fields(self, user=None):
        if user and self.created_by_user and self.created_by_user.company == user.company:
        
            try:
                self.category = decrypt(self.category)
                self.description = decrypt(self.description)
                self.quantity = (self.quantity)
                return True
            except Exception as e:
                return False

    def __str__(self):
        try:
            return str(self.name)
        except Exception as e:
            return f"Equipment {self.id}"

class Employee(models.Model):
    LEVEL_CHOICES = [
        ('2', 'Level 2'),
        ('3', 'Level 3'),
        ('4', 'Level 4'),
        ('5+', 'Level 5+'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.ForeignKey(
        'app.Company', 
        on_delete=models.CASCADE, 
        related_name='employees', 
        null=True, 
        blank=True
    )

    qualifications = models.ManyToManyField(
        'Qualification',
        through='EmployeeQualification',
        blank=True,
        related_name='employees',
    )

    employee_number = models.CharField(max_length=255, unique=True)
    callsign = models.CharField(max_length=200, unique=True)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=200, blank=True, null=True)

    # New Level field
    level = models.CharField(
        max_length=3,
        choices=LEVEL_CHOICES,
        default='2'
    )

    position = models.CharField(max_length=200)
    department = models.CharField(max_length=200)
    group = models.CharField(max_length=200)
    date_hired = models.DateField()
    location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=200)

    created_by_user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigneduser")
    created_timestamp = models.DateTimeField(auto_now_add=True)


    def save(self, *args, **kwargs):
        if self.created_by_user and not self.company:
            self.company = self.created_by_user.company

        # Encrypt sensitive fields
        if self.position:
            self.position = encrypt(self.position)
        if self.department:
            self.department = encrypt(self.department)
        if self.first_name:
            self.first_name = encrypt(self.first_name)
        if self.last_name:
            self.last_name = encrypt(self.last_name)
        if self.status:
            self.status = encrypt(self.status)
        if self.phone_number:
            self.phone_number = encrypt(self.phone_number)
        if self.group:
            self.group = encrypt(self.group)

        super().save(*args, **kwargs)

    def decrypt_fields(self, user=None):
        if user and self.created_by_user and self.created_by_user.company == user.company:
            try:
                self.position = decrypt(self.position)
                self.department = decrypt(self.department)
                self.first_name = decrypt(self.first_name)
                self.last_name = decrypt(self.last_name)
                self.phone_number = decrypt(self.phone_number)
                self.status = decrypt(self.status)
                self.group = decrypt(self.group)
                return True
            except Exception:
                return False

    def __str__(self):
        return f"{self.callsign}"
    

class Qualification(models.Model):
    TYPE_CHOICES = [
        ("training", "Training"),
        ("certification", "Certification"),
        ("license", "License"),
        ("medical", "Medical"),
        ("equipment", "Equipment"),
        ("other", "Other"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(
        max_length=255,
        unique=True
    )

    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        default="training"
    )

    rep_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of repetitions or renewals required."
    )

    date_created = models.DateTimeField(
        auto_now_add=True
    )

    required_approval = models.BooleanField(
        default=False
    )

    field_1 = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    field_2 = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    field_3 = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Qualification"
        verbose_name_plural = "Qualifications"

    def __str__(self):
        return self.name
    
class EmployeeQualification(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("expired", "Expired"),
        ("revoked", "Revoked"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="employee_qualifications",
    )

    qualification = models.ForeignKey(
        Qualification,
        on_delete=models.CASCADE,
        related_name="employee_qualifications",
    )

    date_completed = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="approved",
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("employee", "qualification")
        ordering = ["qualification__name"]

    def __str__(self):
        return f"{self.employee.callsign} - {self.qualification.name}"


class ServiceType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    created_by_user = models.ForeignKey(CustomUser , on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)


    def save(self, *args, **kwargs):
        if self.name:
            self.name = encrypt(self.name)
        if self.description:
            self.description = encrypt(self.description)
        super().save(*args, **kwargs)

    def decrypt_fields(self, user=None):
        if user and self.created_by_user and self.created_by_user.company == user.company:
            self.name = decrypt(self.name)
            self.description = decrypt(self.description)

    def __str__(self):
        return decrypt(self.name)
    

from datetime import time

class ServiceRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    invoice = models.ForeignKey('business.Invoice', on_delete=models.PROTECT, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    start_location = models.ForeignKey(
        'Location', 
        on_delete=models.CASCADE, 
        related_name='service_requests_start'
    )
    end_location = models.ForeignKey(
        'Location', 
        on_delete=models.CASCADE, 
        related_name='service_requests_end'
    )
    customer = models.ForeignKey('business.Customer', on_delete=models.PROTECT, null=False, blank=False)
    equipment = models.ForeignKey('Equipment', on_delete=models.PROTECT)
    employee = models.ForeignKey('Employee', on_delete=models.PROTECT)
    assigned_employees = models.ManyToManyField('Employee', related_name='assigned_service_requests', blank=True)
    service_type = models.ForeignKey('ServiceType', on_delete=models.PROTECT)
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    created_timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=255)

    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    all_day = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """Ensure start_time and end_time are properly set if all_day is True."""
        if self.all_day:
            self.start_time = time(0, 0)  # 12:00 AM
            self.end_time = time(23, 59)  # 11:59 PM
        super().save(*args, **kwargs)
    

    def add_note(self, content):
        """Add a note to the service request."""
        note = Note.create(content)
        self.notes.add(note)  # Add the newly created note to the service request
        self.save()

    def get_notes(self):
        """Retrieve all notes associated with this service request."""
        return self.notes.all()

    def decrypt_fields(self, user=None):
        if user and self.created_by_user == user:
            self.service_type.name = decrypt(self.service_type.name)
            self.employee.first_name = decrypt(self.employee.first_name)
            self.employee.last_name = decrypt(self.employee.last_name)
 
    def __str__(self):
        return f"ServiceRequest {self.id}"
    
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now
    
@receiver(pre_save, sender=ServiceRequest)
def generate_service_request_number(sender, instance, **kwargs):
    """
    Generates a unique service_request_number in the format YYYYMMDD00001
    """
    if not instance.service_request_number:
        today_str = now().strftime('%Y%m%d')
        last_sr = ServiceRequest.objects.filter(service_request_number__startswith=today_str).order_by('-service_request_number').first()

        if last_sr and last_sr.service_request_number:
            last_number = int(last_sr.service_request_number[-5:])
            new_number = last_number + 1
        else:
            new_number = 1

        instance.service_request_number = f"{today_str}{new_number:05d}"

    
class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zip = models.IntegerField()
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='companies_created',
        on_delete=models.CASCADE
    )
    primary_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='primary_companies',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    secondary_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='secondary_companies',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='associated_companies',
        blank=True
    )
    is_company_subscription_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self:
            self.company_name = self.name
        return self.name
    
class Directmessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    body = models.TextField()
    created_by_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    to_users = models.ManyToManyField(CustomUser, related_name='received_messages')
    created_timestamp = models.DateTimeField(auto_now_add=True)
    marked_for_deletion = models.ManyToManyField(CustomUser, related_name='marked_for_deletion', blank=True)

    def save(self, *args, **kwargs):
        if self.body:
            self.body = encrypt(self.body)
        super().save(*args, **kwargs)
    
    def decrypt_fields(self, user=None):
        if user and (self.created_by_user == user or self.to_users.filter(id=user.id).exists()):
            self.body = decrypt(self.body)

    def __str__(self):
        return f"{(self.id)}"
    

class Posting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    
    created_by_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.subject:
            self.subject = encrypt(self.subject)
        if self.body:
            self.body = encrypt(self.body)
        super().save(*args, **kwargs)
    
    def decrypt_fields(self, user=None):
        if self.subject:
            self.subject = decrypt(self.subject)
        if self.body:
            self.body = decrypt(self.body)

    def __str__(self):
        return f"{(self.id)}"
    

from django.utils.timezone import now

class Invitation(models.Model):
    email = models.EmailField(unique=True)
    token = models.CharField(max_length=32, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=now)
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"Invitation to {self.email} for {self.company.name}"




class Note(models.Model):
    title = models.CharField(max_length=1000)
    text = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    service_request = models.ForeignKey('ServiceRequest', related_name='notes', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self.title:
            self.title = encrypt(self.title)
        if self.text:
            self.text = encrypt(self.text)
        super().save(*args, **kwargs)
    
    def decrypt_fields(self):
        if self.title:
            self.title = decrypt(self.title)
        if self.text:
            self.text = decrypt(self.text)

    def __str__(self):
        return f"Note {(self.id)} created at {self.created_at}"




class SlideshowImage(models.Model):
    title = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='slides/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title if self.title else f"Slide {self.id}"
    


class APIObject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class Stripe_Transaction(models.Model):
    invoice_number = models.CharField(max_length=50)
    stripe_session_id = models.CharField(max_length=255)
    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='usd')
    customer_email = models.EmailField(blank=True, null=True)
    payment_status = models.CharField(max_length=50)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.amount} {self.currency}"
    

class CostSheet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    equipment = models.ForeignKey('Equipment', on_delete=models.PROTECT)
    employee = models.ForeignKey('Employee', on_delete=models.PROTECT)
    location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, blank=True)
    service_type = models.ForeignKey('ServiceType', on_delete=models.PROTECT)
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_timestamp = models.DateTimeField(auto_now_add=True)

    # Optional: link back to a ServiceRequest
    service_request = models.ForeignKey(
        'ServiceRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cost_sheets'
    )

    # Optional fields for cost tracking
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    equipment_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def calculate_total_cost(self):
        """Recalculate total cost based on labor + equipment."""
        self.total_cost = (self.labor_cost or 0) + (self.equipment_cost or 0)
        return self.total_cost

    def save(self, *args, **kwargs):
        # Auto-calculate total before saving
        self.calculate_total_cost()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"CostSheet {self.id} for {self.employee} ({self.start_date} - {self.end_date})"