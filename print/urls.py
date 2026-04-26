from django.urls import path
from .views import print_invoice_pdf, print_quote_pdf

urlpatterns = [
    path('invoice/<int:pk>/print/', print_invoice_pdf, name='print_invoice_pdf'),
    path('quote/print/<int:pk>/', print_quote_pdf, name='print_quote_pdf'),

]