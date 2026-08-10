from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

class UserAdmin(BaseUserAdmin):
    model = CustomUser
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    fieldsets = (
        (None, {'fields': ('id', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number')}),  # Add phone_number here
        ('Permissions', {'fields': ('signup_ip_address', 'is_active', 'is_staff', 'is_account_admin', 'is_superuser', 'groups', 'user_permissions', 'is_onboarded', 'company', 'stripe_coupon_id', 'coupon_code', 'promotion_code')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'phone_number'),  # Add phone_number here
        }),
    )
    list_display = ('date_joined', 'id', 'email', 'first_name', 'last_name', 'phone_number', 'signup_ip_address', 'is_onboarded','is_staff', 'is_account_admin', 'promotion_code', 'stripe_coupon_id', 'coupon_code')  # Add phone_number here
    search_fields = ('id', 'email', 'first_name', 'last_name', 'phone_number')  # Add phone_number here
    ordering = ('id', 'email',)
    readonly_fields = ['date_joined', 'id', 'first_name', 'last_name', 'phone_number', 'signup_ip_address']

admin.site.register(CustomUser, UserAdmin)
