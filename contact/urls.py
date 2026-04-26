from django.urls import path
from . import views

urlpatterns = [
    path("", views.contact_us_view, name="contact_us"),
    path("success/", views.contact_success_view, name="contact_success"),
]