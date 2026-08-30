import uuid

from django.conf import settings
from django.db import models


class DataImport(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "UPLOADED", "Uploaded"
        ANALYZING = "ANALYZING", "Analyzing"
        MAPPING = "MAPPING", "Mapping"
        VALIDATING = "VALIDATING", "Validating"
        READY = "READY", "Ready"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    class SourceType(models.TextChoices):
        CSV = "CSV", "CSV"
        XLSX = "XLSX", "Excel"
        XLS = "XLS", "Excel 97-2003"
        DAT = "DAT", "DAT"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    company = models.ForeignKey(
        "app.Company",
        on_delete=models.CASCADE,
        related_name="data_imports",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="data_imports",
    )

    file = models.FileField(
        upload_to="data_imports/%Y/%m/%d/",
    )

    filename = models.CharField(
        max_length=255,
    )

    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.OTHER,
    )

    target_model = models.CharField(
        max_length=100,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED,
    )

    total_rows = models.PositiveIntegerField(
        default=0,
    )

    valid_rows = models.PositiveIntegerField(
        default=0,
    )

    error_rows = models.PositiveIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["company", "-created_at"]),
            models.Index(fields=["uploaded_by", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.filename} - {self.get_status_display()}"


class DataImportColumn(models.Model):
    """
    Stores the mapping between a source-file column
    and a target Django model field.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    data_import = models.ForeignKey(
        DataImport,
        on_delete=models.CASCADE,
        related_name="columns",
    )

    source_column = models.CharField(
        max_length=255,
    )

    target_field = models.CharField(
    max_length=255,
    blank=True,
    default="",
    )

    column_order = models.PositiveIntegerField(
        default=0,
    )

    is_required = models.BooleanField(
        default=False,
    )

    is_mapped = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["column_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["data_import", "source_column"],
                name="unique_import_source_column",
            ),
        ]
        indexes = [
            models.Index(
                fields=["data_import", "column_order"]
            ),
        ]

    def __str__(self):
        return (
            f"{self.data_import.filename}: "
            f"{self.source_column} → {self.target_field}"
        )