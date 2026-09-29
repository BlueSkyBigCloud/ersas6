import uuid
from django.db import models
from django.conf import settings
# Create your models here.


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

    company = models.ForeignKey(
        "app.Company",
        on_delete=models.CASCADE,
        related_name="qualifications",
    )

    name = models.CharField(
        max_length=255
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

        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"],
                name="unique_qualification_per_company",
            )
        ]

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
        "app.Employee",
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
