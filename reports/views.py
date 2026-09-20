from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from app.decorators import onboarded


@onboarded()
@login_required
def reports_dashboard(request):
    """
    Reports dashboard for the user's company.
    """

    user_company = getattr(request.user, "company", None)

    if not user_company:
        return render(
            request,
            "reports_dashboard.html",
            {
                "reports": [],
                "user_company": None,
            },
        )

    reports = [
        {
            "name": "Service Requests",
            "url": "service_request_report",
            "description": "View service request activity and details.",
        },
        {
            "name": "Invoices",
            "url": "invoice_report",
            "description": "View invoice and billing information.",
        },
        {
            "name": "Employees",
            "url": "employee_report",
            "description": "View employee-related information.",
        },
        {
            "name": "Equipment",
            "url": "equipment_report",
            "description": "View equipment and utilization information.",
        },
    ]

    context = {
        "reports": reports,
        "user_company": user_company,
    }

    return render(
        request,
        "reports_dashboard.html",
        context,
    )

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from app.decorators import onboarded
from app.models import Employee, Equipment
from business.models import Invoice
from app.models import ServiceRequest

@onboarded()
@login_required
def service_request_report(request):
    """
    Display service requests for the user's company.
    """

    user_company = getattr(request.user, "company", None)

    if not user_company:
        return render(
            request,
            "service_request_report.html",
            {
                "service_requests": ServiceRequest.objects.none(),
                "user_company": None,
            },
        )

    service_requests = (
        ServiceRequest.objects
        .filter(company=user_company)
        .select_related(
            "employee",
            "equipment",
            "start_location",
            "end_location",
            "service_type",
            "invoice",
        )
        .order_by("-created_timestamp")
    )

    context = {
        "service_requests": service_requests,
        "user_company": user_company,
        "report_title": "Service Request Report",
    }

    return render(
        request,
        "service_request_report.html",
        context,
    )



@onboarded()
@login_required
def invoice_report(request):
    """
    Display invoices for the user's company.
    """

    user_company = getattr(request.user, "company", None)

    if not user_company:
        return render(
            request,
            "invoice_report.html",
            {
                "invoices": Invoice.objects.none(),
                "user_company": None,
                "report_title": "Invoice Report",
            },
        )

    invoices = (
        Invoice.objects
        .filter(service_request__company=user_company)
        .order_by("-created_timestamp")
    )

    context = {
        "invoices": invoices,
        "user_company": user_company,
        "report_title": "Invoice Report",
    }

    return render(
        request,
        "invoice_report.html",
        context,
    )


@onboarded()
@login_required
def employee_report(request):
    """
    Display employees for the user's company.
    """

    user_company = getattr(request.user, "company", None)

    if not user_company:
        return render(
            request,
            "employee_report.html",
            {
                "employees": Employee.objects.none(),
                "user_company": None,
                "report_title": "Employee Report",
            },
        )

    employees = (
        Employee.objects
        .filter(company=user_company)
        .order_by("last_name", "first_name")
    )

    context = {
        "employees": employees,
        "user_company": user_company,
        "report_title": "Employee Report",
    }

    return render(
        request,
        "employee_report.html",
        context,
    )


@onboarded()
@login_required
def equipment_report(request):
    """
    Display equipment for the user's company.
    """

    user_company = getattr(request.user, "company", None)

    if not user_company:
        return render(
            request,
            "equipment_report.html",
            {
                "equipment": Equipment.objects.none(),
                "user_company": None,
                "report_title": "Equipment Report",
            },
        )

    equipment = (
        Equipment.objects
        .filter(company=user_company)
        .order_by("name")
    )

    context = {
        "equipment": equipment,
        "user_company": user_company,
        "report_title": "Equipment Report",
    }

    return render(
        request,
        "equipment_report.html",
        context,
    )
