from django.urls import path

from .views import training_dashboard


app_name = "training"

urlpatterns = [
    path("", training_dashboard, name="training_dashboard"),
]