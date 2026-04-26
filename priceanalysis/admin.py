from django.contrib import admin
from .models import (
    Analysis_ServiceType,
    Analysis_ServiceRequest,
    Analysis_State,
    Analysis_ZipPrice,
    Analysis_ZipCode
)

# ---------- ServiceType ----------
@admin.register(Analysis_ServiceType)
class AnalysisServiceTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)

# ---------- ServiceRequest ----------
@admin.register(Analysis_ServiceRequest)
class AnalysisServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("service_type", "state", "price", "created_at")
    list_filter = ("state", "service_type")
    search_fields = ("state", "service_type__name")

# ---------- State ----------
@admin.register(Analysis_State)
class AnalysisStateAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")
    ordering = ("name",)


# ---------- State ----------
@admin.register(Analysis_ZipCode)
class AnalysisZipCodeAdmin(admin.ModelAdmin):
    list_display = ("zip_code", "state_code")
    search_fields = ("zip_code", "state_code")
    ordering = ("state_code",)


from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
import csv, io
from .models import Analysis_ZipPrice, Analysis_ServiceType, Analysis_State



@admin.register(Analysis_ZipPrice)
class AnalysisZipPriceAdmin(admin.ModelAdmin):
    list_display = ("zip_code", "state", "service_type", "avg_price", "min_price", "max_price", "variance")
    list_filter = ("state", "service_type")
    search_fields = ("zip_code", "state__code", "service_type__name")

    change_list_template = "admin/analysis_zipprice_changelist.html"  # custom template for upload

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-pricing/', self.admin_site.admin_view(self.bulk_upload_view), name='bulk_pricing_upload')
        ]
        return custom_urls + urls

    def bulk_upload_view(self, request):
        if request.method == "POST" and request.FILES.get("csv_file"):
            csv_file = request.FILES["csv_file"]
            if not csv_file.name.endswith('.csv'):
                self.message_user(request, "Please upload a CSV file.", level=messages.ERROR)
                return redirect("..")

            data_set = csv_file.read().decode("utf-8")
            io_string = io.StringIO(data_set)
            reader = csv.DictReader(io_string)

            created_count = 0
            errors = []

            for i, row in enumerate(reader, start=2):
                zip_code = row.get("zip_code")
                state_code = row.get("state_code")
                service_type_name = row.get("service_type")
                avg_price = row.get("avg_price")
                min_price = row.get("min_price")
                max_price = row.get("max_price")

                # Validate fields
                if not (zip_code and state_code and service_type_name and avg_price and min_price and max_price):
                    errors.append(f"Row {i}: Missing fields.")
                    continue

                try:
                    state = Analysis_State.objects.get(code=state_code)
                except Analysis_State.DoesNotExist:
                    errors.append(f"Row {i}: State '{state_code}' not found.")
                    continue

                try:
                    service_type = Analysis_ServiceType.objects.get(name=service_type_name)
                except Analysis_ServiceType.DoesNotExist:
                    errors.append(f"Row {i}: Service Type '{service_type_name}' not found.")
                    continue

                try:
                    zip_price_obj, created = Analysis_ZipPrice.objects.update_or_create(
                        zip_code=zip_code,
                        state=state,
                        service_type=service_type,
                        defaults={
                            "avg_price": avg_price,
                            "min_price": min_price,
                            "max_price": max_price
                        }
                    )
                    created_count += 1
                except Exception as e:
                    errors.append(f"Row {i}: {str(e)}")
                    continue

            if created_count:
                self.message_user(request, f"Successfully uploaded {created_count} ZIP pricing records.")
            for e in errors[:10]:
                self.message_user(request, e, level=messages.ERROR)

            return redirect("..")

        return render(request, "admin/bulk_pricing_upload.html")