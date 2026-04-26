from django.urls import path
from . import views

app_name = "priceanalysis"


urlpatterns = [

    path("", views.priceanalysis_dashboard, name="priceanalysis_dashboard"),
    path("1", views.priceanalysis_dashboard1, name="priceanalysis_dashboard1"),
    path("2", views.priceanalysis_dashboard2, name="priceanalysis_dashboard2"),
    path("3", views.priceanalysis_dashboard3, name="priceanalysis_dashboard3"),
    
    path("price-data/", views.price_data, name="price_data"),
    path("zip-price-data/", views.zip_price_data, name="zip_price_data"),

]