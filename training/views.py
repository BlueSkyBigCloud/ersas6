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
            "training/training_dashboard.html",
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

    # Employee fields are encrypted in the database.
    # Decrypt the objects before sending them to the template.
    for employee in employees:
        employee.decrypt_fields(user=request.user)

    qualifications = (
        Qualification.objects
        .all()
        .order_by("name")
    )

    employee_qualifications = (
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

    # Decrypt employee fields on the related objects.
    for employee_qualification in employee_qualifications:
        employee_qualification.employee.decrypt_fields(
            user=request.user
        )

    return render(
        request,
        "training/training_dashboard.html",
        {
            "employees": employees,
            "qualifications": qualifications,
            "employee_qualifications": employee_qualifications,
        },
    )