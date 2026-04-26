from django.urls import path
from . import views

urlpatterns = [
    path("", views.prospect_dashboard, name="prospect_dashboard"),
    path("create/", views.create_prospect, name="create_prospect"),
    path("<uuid:pk>/", views.prospect_profile, name="prospect_profile"),
    path("<uuid:pk>/convert/", views.convert_prospect_to_customer, name="convert_prospect_to_customer"),
    path('prospects/<uuid:pk>/edit/', views.edit_prospect, name='edit_prospect'),

]