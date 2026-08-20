from django.urls import path

from .views import (
    integration_dashboard,
    integration_upload,
    integration_analyze,
    integration_mapping,
    integration_validate,
    integration_import,
    integration_results,
)


app_name = "dataintegration"


urlpatterns = [

    # ---------------------------------------------------------
    # Dashboard
    # ---------------------------------------------------------

    path(
        "",
        integration_dashboard,
        name="integration_dashboard",
    ),

    # ---------------------------------------------------------
    # Upload
    # ---------------------------------------------------------

    path(
        "upload/",
        integration_upload,
        name="integration_upload",
    ),

    # ---------------------------------------------------------
    # File analysis
    # ---------------------------------------------------------

    path(
        "<uuid:import_id>/analyze/",
        integration_analyze,
        name="integration_analyze",
    ),

    # ---------------------------------------------------------
    # Column mapping
    # ---------------------------------------------------------

    path(
        "<uuid:import_id>/mapping/",
        integration_mapping,
        name="integration_mapping",
    ),

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    path(
        "<uuid:import_id>/validate/",
        integration_validate,
        name="integration_validate",
    ),

    # ---------------------------------------------------------
    # Import
    # ---------------------------------------------------------

    path(
        "<uuid:import_id>/import/",
        integration_import,
        name="integration_import",
    ),

    # ---------------------------------------------------------
    # Results
    # ---------------------------------------------------------

    path(
        "<uuid:import_id>/results/",
        integration_results,
        name="integration_results",
    ),
]