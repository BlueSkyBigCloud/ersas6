from django.urls import path

from . import views


app_name = "reports"


urlpatterns = [
    path("reports_dashboard", views.reports_dashboard, name="reports_dashboard"),
    path( "", views.reports_dashboard, name="reports_dashboard", ),
    path( "service-requests/", views.service_request_report, name="service_request_report", ), 
    path( "invoices/", views.invoice_report, name="invoice_report", ), 
    path( "employees/", views.employee_report, name="employee_report", ),
    path( "equipment/", views.equipment_report, name="equipment_report", ),
    path("interactive/", views.reports_interactive, name="reports_interactive",
    ),
]