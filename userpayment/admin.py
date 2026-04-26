from django.contrib import admin
from .models import UserPayment


class UserPaymentAdmin(admin.ModelAdmin):
    list_display = ('app_user', 'company', 'payment_bool', 'stripe_customer_id', 'stripe_subscription_id')  # <-- updated
    list_filter = ('payment_bool', 'company')
    search_fields = ('app_user__email', 'company__name')

admin.site.register(UserPayment, UserPaymentAdmin)