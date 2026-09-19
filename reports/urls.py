from django.urls import path

from . import views


app_name = "reports"


urlpatterns = [
    path("reports_dashboard", views.reports_dashboard, name="reports_dashboard"),
]