from django.contrib import admin
from .models import Prospect, Action

class ActionInline(admin.TabularInline):
    model = Action
    extra = 0  # no extra blank forms
    readonly_fields = ('date', 'created_by_user')
    fields = ('action_type', 'description', 'date', 'created_by_user')
    can_delete = True

@admin.register(Prospect)
class ProspectAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_type', 'contact', 'status', 'created_at', 'account_rep')
    list_filter = ('status', 'business_type', 'created_at')
    search_fields = ('name', 'contact', 'email', 'phone_number', 'account_rep')
    readonly_fields = ('created_at', 'converted_customer')
    inlines = [ActionInline]
    actions = ['convert_selected_prospects']

    def convert_selected_prospects(self, request, queryset):
        """
        Custom admin action to convert multiple prospects to customers.
        """
        for prospect in queryset.filter(status='NEW'):
            # Provide defaults for payment_terms and payment_method or prompt elsewhere
            prospect.convert_to_customer(payment_terms='Net 30', payment_method='Default')
        self.message_user(request, f"{queryset.count()} prospects converted to customers.")
    convert_selected_prospects.short_description = "Convert selected prospects to customers"

@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'prospect', 'created_by_user', 'date')
    list_filter = ('action_type', 'date')
    search_fields = ('description', 'prospect__name', 'created_by_user__username')
    readonly_fields = ('date',)
