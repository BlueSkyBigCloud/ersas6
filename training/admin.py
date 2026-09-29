from django.contrib import admin

from training.models import Qualification, EmployeeQualification

# Register your models here.
@admin.register(EmployeeQualification)
class EmployeeQualificationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'qualification', 'status', 'date_completed', 'expiration_date')
    list_filter = ('status', 'date_completed', 'expiration_date')
    search_fields = ('employee__callsign', 'qualification__name')
    readonly_fields = []

@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'rep_count', 'required_approval')
    list_filter = ('type', 'required_approval')
    search_fields = ('name',)
    readonly_fields = []