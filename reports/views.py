from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import json
from app.decorators import onboarded
import logging

logger = logging.getLogger(__name__)


@onboarded()
@login_required
def reports_interactive(request):
    user_company = getattr(request.user, "company", None)

    if not user_company:
        return render(
            request,
            "reports/reports_interactive.html",
            {
                "report_data": {
                    "service_requests": [],
                    "invoices": [],
                    "employees": [],
                    "equipment": [],
                }
            },
        )

    logger.info(
    "INTERACTIVE REPORT - user=%s company=%s",
    request.user.email,
    getattr(request.user, "company_id", None),
    )

    employees = Employee.objects.filter(
        company=request.user.company
    )

    logger.info(
        "INTERACTIVE REPORT - employee count=%s",
        employees.count(),
    )

    # ---------------------------------------------------------
    # Service Requests
    # ---------------------------------------------------------

    service_requests = (
        ServiceRequest.objects
        .filter(company=user_company)
        .select_related(
            "customer",
            "employee",
            "equipment",
            "service_type",
            "start_location",
            "end_location",
            "invoice",
        )
        .order_by("-created_timestamp")
    )

    service_request_data = []

    for service_request in service_requests:
        service_request_data.append({
            "id": str(service_request.id),
            "number": service_request.service_request_number or "",
            "start_date": (
                service_request.start_date.isoformat()
                if service_request.start_date
                else ""
            ),
            "end_date": (
                service_request.end_date.isoformat()
                if service_request.end_date
                else ""
            ),
            "status": service_request.status or "",
            "service_type": (
                service_request.service_type.name
                if service_request.service_type
                else ""
            ),
            "customer": (
                str(service_request.customer)
                if service_request.customer
                else ""
            ),
            "created": (
                service_request.created_timestamp.isoformat()
                if service_request.created_timestamp
                else ""
            ),
        })

    # ---------------------------------------------------------
    # Invoices
    # ---------------------------------------------------------

    invoices = (
        Invoice.objects
        .filter(service_request__company=user_company)
        .select_related(
            "customer",
            "service_request",
        )
        .order_by("-created_at")
    )

    invoice_data = []

    for invoice in invoices:
        invoice_data.append({
            "id": str(invoice.id),
            "number": invoice.invoice_number or "",
            "issue_date": (
                invoice.issue_date.isoformat()
                if invoice.issue_date
                else ""
            ),
            "due_date": (
                invoice.due_date.isoformat()
                if invoice.due_date
                else ""
            ),
            "status": invoice.payment_status or "",
            "customer": (
                str(invoice.customer)
                if invoice.customer
                else ""
            ),
            "created": (
                invoice.created_at.isoformat()
                if invoice.created_at
                else ""
            ),
        })

    # ---------------------------------------------------------
    # Employees
    # ---------------------------------------------------------

    employees = (
        Employee.objects
        .filter(company=user_company)
        .order_by("last_name", "first_name")
    )

    employee_data = []

    for employee in employees:
        # Decrypt fields using the current logged-in user
        employee.decrypt_fields(user=request.user)

        for employee in employees:
            employee_data.append({
                "id": str(employee.id),
                "employee_number": employee.employee_number or "",
                "first_name": employee.first_name or "",
                "last_name": employee.last_name or "",
                "position": employee.position or "",
                "department": employee.department or "",
                "status": employee.status or "",
            })

    # ---------------------------------------------------------
    # Equipment
    # ---------------------------------------------------------

    equipment = (
        Equipment.objects
        .filter(company=user_company)
        .order_by("name")
    )

    equipment_data = []

    for item in equipment:
        equipment_data.append({
            "id": str(item.id),
            "name": item.name or "",
            "category": item.category or "",
            "make": item.make or "",
            "model": item.model or "",
            "stock_number": item.stock_number or "",
            "quantity": item.quantity or 0,
        })

    report_data = {
        "service_requests": service_request_data,
        "invoices": invoice_data,
        "employees": employee_data,
        "equipment": equipment_data,
    }

    return render(
        request,
        "reports_interactive.html",
        {
            "report_data": report_data,
        },
    )


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
        .order_by("-created_at")
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
