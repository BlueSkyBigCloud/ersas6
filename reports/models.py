
import uuid

from django.conf import settings
from django.db import models


class ReportDefinition(models.Model):

    REPORT_TYPES = [
        (
            "employees_per_service_request",
            "Employees per Service Request",
        ),
        (
            "profitability_per_service_request",
            "Profitability per Service Request",
        ),
        (
            "service_requests_per_customer",
            "Service Requests per Customer",
        ),
        (
            "location_profitability",
            "Revenue and Profitability per Location",
        ),
        (
            "custom",
            "Custom Model Report",
        ),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    company = models.ForeignKey(
        "app.Company",
        on_delete=models.CASCADE,
        related_name="report_definitions",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_reports",
    )

    name = models.CharField(max_length=255)

    report_type = models.CharField(
        max_length=100,
        choices=REPORT_TYPES,
        default="custom",
    )

    # Model used for a general/custom report.
    model_name = models.CharField(
        max_length=100,
        blank=True,
    )

    # User-selected report columns.
    selected_columns = models.JSONField(
        default=list,
        blank=True,
    )

    # User-selected filters.
    filters = models.JSONField(
        default=dict,
        blank=True,
    )

    # Sorting configuration.
    sort_field = models.CharField(
        max_length=100,
        blank=True,
    )

    sort_direction = models.CharField(
        max_length=4,
        choices=[
            ("asc", "Ascending"),
            ("desc", "Descending"),
        ],
        default="asc",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "created_by", "name"],
                name="unique_saved_report_per_user_company",
            ),
        ]

    def __str__(self):
        return self.name