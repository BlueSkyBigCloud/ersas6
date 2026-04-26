from django.db import models
from business.models import *
from app.models import *
# Create your models here.
class Opportunity(models.Model):
    STAGE_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('negotiating', 'Negotiating'),
        ('closed', 'Closed'),
    ]
    stage = models.CharField(
        max_length=50,
        choices=STAGE_CHOICES,  # Add choices here
    )
    converted_to_customer = models.BooleanField()
    value = models.DecimalField(max_digits=10, decimal_places=2)
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)