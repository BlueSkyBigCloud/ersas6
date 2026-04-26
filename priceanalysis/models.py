from django.db import models


class Analysis_ServiceType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Analysis_ServiceRequest(models.Model):
    service_type = models.ForeignKey(
        Analysis_ServiceType,
        on_delete=models.CASCADE,
        related_name="service_requests"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    state = models.CharField(
        max_length=2,
        help_text="Two-letter US state code (e.g. CA, TX)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_type} {self.state} ${self.price}"
    

class Analysis_State(models.Model):
    code = models.CharField(max_length=2, unique=True)  # e.g., 'TX'
    name = models.CharField(max_length=50)             # e.g., 'Texas'

    def __str__(self):
        return self.name

class Analysis_ZipPrice(models.Model):
    zip_code = models.CharField(max_length=5)
    state = models.ForeignKey(Analysis_State, on_delete=models.CASCADE)
    service_type = models.ForeignKey(Analysis_ServiceType, on_delete=models.CASCADE)
    avg_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def variance(self):
        return self.max_price - self.min_price

    def __str__(self):
        return f"{self.zip_code} - {self.service_type.name}"
    
class Analysis_ZipCode(models.Model):
    zip_code = models.CharField(max_length=5, unique=True)
    state_code = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.zip_code} ({self.state_code})"