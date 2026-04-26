from django import forms

class FileUploadForm(forms.Form):
    file = forms.FileField()


    class BulkEmployeeForm(forms.Form):
        data = forms.JSONField(help_text="Enter employee data in JSON format")

    def clean_data(self):
        employees = self.cleaned_data["data"]

        # Validate each employee entry
        for emp in employees:
            required_fields = ["first_name", "last_name", "employee_number", "callsign", "position", "department"]
            for field in required_fields:
                if field not in emp or not emp[field]:
                    raise forms.ValidationError(f"Missing field: {field}")

        return employees