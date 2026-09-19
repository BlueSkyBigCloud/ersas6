from django.contrib import admin

from .models import ReportDefinition


@admin.register(ReportDefinition)
class ReportDefinitionAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "report_type",
        "company",
        "created_by",
        "created_at",
    )

    list_filter = (
        "report_type",
        "created_at",
    )

    search_fields = (
        "name",
        "created_by__email",
    )