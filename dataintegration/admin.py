from django.contrib import admin

from .models import (
    DataImport,
    DataImportColumn,
)


@admin.register(DataImport)
class DataImportAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "company",
        "original_filename",
        "status",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "company",
        "created_at",
    )

    search_fields = (
        "id",
        "original_filename",
        "company__name",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 50


@admin.register(DataImportColumn)
class DataImportColumnAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "data_import",
        "source_column",
        "target_field",
        "column_order",
        "is_required",
        "is_mapped",
    )

    list_filter = (
        "is_required",
        "is_mapped",
    )

    search_fields = (
        "source_column",
        "target_field",
        "data_import__original_filename",
    )

    ordering = (
        "data_import",
        "column_order",
    )

    list_per_page = 100