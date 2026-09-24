from django.urls import path

from app import views

from . import views
from .views import *

app_name = "training"

urlpatterns = [
    path("", views.training_dashboard, name="training_dashboard"),
    path("training_dashboard", views.training_dashboard, name="training_dashboard"),
]