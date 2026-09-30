from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from app.models import (
    Employee
)

from .models import EmployeeQualification, Qualification


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


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import Qualification
from app.decorators import onboarded


@onboarded()
@login_required
def create_qualification(request):
    user_company = getattr(request.user, "company", None)

    if not user_company:
        messages.error(
            request,
            "You are not associated with a company."
        )
        return redirect("training:training_dashboard")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        qualification_type = request.POST.get("type", "training").strip()
        rep_count = request.POST.get("rep_count", "0").strip()
        required_approval = request.POST.get("required_approval") == "on"
        field_1 = request.POST.get("field_1", "").strip()
        field_2 = request.POST.get("field_2", "").strip()
        field_3 = request.POST.get("field_3", "").strip()

        # Required field
        if not name:
            messages.error(
                request,
                "Qualification name is required."
            )

            return render(
                request,
                "training/create_qualification.html",
                {
                    "form_data": request.POST,
                    "type_choices": Qualification.TYPE_CHOICES,
                },
            )

        # Prevent duplicate qualification names within this company
        if Qualification.objects.filter(
            company=user_company,
            name__iexact=name,
        ).exists():
            messages.error(
                request,
                f'A qualification named "{name}" already exists.'
            )

            return render(
                request,
                "training/create_qualification.html",
                {
                    "form_data": request.POST,
                    "type_choices": Qualification.TYPE_CHOICES,
                },
            )

        # Validate repetition count
        try:
            rep_count = int(rep_count or 0)

            if rep_count < 0:
                raise ValueError

        except (TypeError, ValueError):
            messages.error(
                request,
                "Repetition count must be a valid number."
            )

            return render(
                request,
                "training/create_qualification.html",
                {
                    "form_data": request.POST,
                    "type_choices": Qualification.TYPE_CHOICES,
                },
            )

        qualification = Qualification(
            company=user_company,
            name=name,
            type=qualification_type,
            rep_count=rep_count,
            required_approval=required_approval,
            field_1=field_1 or None,
            field_2=field_2 or None,
            field_3=field_3 or None,
        )

        qualification.save()

        messages.success(
            request,
            f'Qualification "{qualification.name}" was created successfully.'
        )

        return redirect("training:training_dashboard")

    return render(
        request,
        "create_qualification.html",
        {
            "type_choices": Qualification.TYPE_CHOICES,
        },
    )
