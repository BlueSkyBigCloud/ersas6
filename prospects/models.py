import uuid
from django.conf import settings
from django.db import models
from business.models import Customer  # assuming Customer is in a 'customers' app
from django.core.validators import RegexValidator
import string
import random

def generate_company_id():
    """Generate a random 10-character alphanumeric ID."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

class Prospect(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('CONTACTED', 'Contacted'),
        ('QUALIFIED', 'Qualified'),
        ('CONVERTED', 'Converted'),
        ('LOST', 'Lost'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prospects'
    ) 

    name = models.CharField(max_length=255)
    business_type = models.CharField(max_length=255)
    contact = models.CharField(max_length=255)
    website = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    products = models.CharField(max_length=255)
    company_size = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    account_rep = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='NEW')
    created_at = models.DateTimeField(auto_now_add=True)
    converted_customer = models.OneToOneField(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prospect_origin"
    )

    def __str__(self):
        return self.name

    def convert_to_customer(self, payment_terms, payment_method):
        """
        Convert this prospect into a Customer and link it.
        """
        customer = Customer.objects.create(
            created_by_user=self.created_by_user,
            name=self.name,
            address=self.address or "",
            email=self.email or "",
            phone_number=self.phone_number or "",
            account_rep=self.account_rep or "",
            payment_terms=payment_terms,
            payment_method=payment_method,
        )
        self.status = 'CONVERTED'
        self.converted_customer = customer
        self.save()
        return customer


class Action(models.Model):
    ACTION_TYPE_CHOICES = [
        ('CALL', 'Call'),
        ('EMAIL', 'Email'),
        ('NOTE', 'Note'),
        ('MEETING', 'Meeting'),
        ('OTHER', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prospect = models.ForeignKey(
        Prospect,
        on_delete=models.CASCADE,
        related_name="actions"
    )
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES, default='NOTE')
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prospect_actions"
    )

    def __str__(self):
        return f"{self.action_type} - {self.prospect.name} ({self.date.strftime('%Y-%m-%d')})"
