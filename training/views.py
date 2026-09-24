from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from app.models import (
    Employee,
    Qualification,
    EmployeeQualification,
)


@login_required
def training_dashboard(request):
    user_company = getattr(request.user, "company", None)

    if not user_company:
        return render(
            request,
            "training_dashboard.html",
            {
                "employees": [],
                "qualifications": [],
                "employee_qualifications": [],
            },
        )

    employees = list(
        Employee.objects
        .filter(company=user_company)
        .order_by("employee_number")
    )

    # Decrypt employee fields.
    for employee in employees:
        employee.decrypt_fields(user=request.user)

        # Replace None values with N/A for display.
        employee.phone_number = employee.phone_number if employee.phone_number else "N/A"
        employee.position = employee.position if employee.position else "N/A"
        employee.department = employee.department if employee.department else "N/A"
        employee.group = employee.group if employee.group else "N/A"
        employee.status = employee.status if employee.status else "N/A"
        employee.level = employee.level if employee.level else "N/A"
        employee.location.name = employee.location.name if employee.location.name else "N/A"

    qualifications = list(
        Qualification.objects
        .all()
        .order_by("name")
    )

    for qualification in qualifications:
        qualification.type = qualification.type if qualification.type else "N/A"
        qualification.rep_count = (
            qualification.rep_count
            if qualification.rep_count is not None
            else "N/A"
        )
        qualification.field_1 = qualification.field_1 if qualification.field_1 else "N/A"
        qualification.field_2 = qualification.field_2 if qualification.field_2 else "N/A"
        qualification.field_3 = qualification.field_3 if qualification.field_3 else "N/A"

    employee_qualifications = list(
        EmployeeQualification.objects
        .filter(employee__company=user_company)
        .select_related(
            "employee",
            "qualification",
        )
        .order_by(
            "employee__employee_number",
            "qualification__name",
        )
    )

    for record in employee_qualifications:
        record.employee.decrypt_fields(user=request.user)

        record.date_completed = (
            record.date_completed
            if record.date_completed is not None
            else "N/A"
        )

        record.expiration_date = (
            record.expiration_date
            if record.expiration_date is not None
            else "N/A"
        )

        record.notes = record.notes if record.notes else "N/A"

    return render(
        request,
        "training_dashboard.html",
        {
            "employees": employees,
            "qualifications": qualifications,
            "employee_qualifications": employee_qualifications,
        },
    )