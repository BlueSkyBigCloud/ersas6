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

    # ---------------------------------------------------------
    # Helper: Return N/A for None or empty string values
    # ---------------------------------------------------------
    def display_value(value):
        if value is None or value == "":
            return "N/A"
        return value

    # ---------------------------------------------------------
    # Service Requests
    # ---------------------------------------------------------
    service_requests = (
        ServiceRequest.objects
        .filter(company=user_company)
        .select_related(
            "customer",
            "manager_employee",
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
        service_type_name = "N/A"

        if service_request.service_type:
            service_type = service_request.service_type
            service_type.decrypt_fields(user=request.user)
            service_type_name = display_value(service_type.name)

        service_request_data.append({
            "id": str(service_request.id),
            "number": display_value(
                service_request.service_request_number
            ),
            "start_date": (
                service_request.start_date.isoformat()
                if service_request.start_date
                else "N/A"
            ),
            "end_date": (
                service_request.end_date.isoformat()
                if service_request.end_date
                else "N/A"
            ),
            "status": display_value(service_request.status),
            "service_type": service_type_name,
            "customer": (
                display_value(str(service_request.customer))
                if service_request.customer
                else "N/A"
            ),
            "created": (
                service_request.created_timestamp.isoformat()
                if service_request.created_timestamp
                else "N/A"
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
            "number": display_value(invoice.invoice_number),
            "issue_date": (
                invoice.issue_date.isoformat()
                if invoice.issue_date
                else "N/A"
            ),
            "due_date": (
                invoice.due_date.isoformat()
                if invoice.due_date
                else "N/A"
            ),
            "status": display_value(invoice.payment_status),
            "customer": (
                display_value(str(invoice.customer))
                if invoice.customer
                else "N/A"
            ),
            "created": (
                invoice.created_at.isoformat()
                if invoice.created_at
                else "N/A"
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
        # Decrypt fields using the current logged-in user.
        employee.decrypt_fields(user=request.user)

        employee_data.append({
            "id": str(employee.id),
            "employee_number": display_value(
                employee.employee_number
            ),
            "first_name": display_value(employee.first_name),
            "last_name": display_value(employee.last_name),
            "position": display_value(employee.position),
            "department": display_value(employee.department),
            "status": (
                display_value(str(employee.status))
                if employee.status
                else "N/A"
            ),
        })

    logger.info(
        "INTERACTIVE REPORT - employee count=%s",
        employees.count(),
    )

    logger.info(
        "EMPLOYEE REPORT - queryset=%s serialized=%s unique_ids=%s",
        employees.count(),
        len(employee_data),
        len({row["id"] for row in employee_data}),
    )

    # ---------------------------------------------------------
    # Equipment
    # ---------------------------------------------------------
    equipment_queryset = (
        Equipment.objects
        .filter(company=user_company)
        .order_by("name")
    )

    equipment_data = []

    for equipment in equipment_queryset:
        # Decrypt fields using the current logged-in user.
        equipment.decrypt_fields(user=request.user)

        equipment_data.append({
            "id": str(equipment.id),
            "name": display_value(equipment.name),
            "category": display_value(equipment.category),
            "make": display_value(equipment.make),
            "model": display_value(equipment.model),
            "stock_number": display_value(equipment.stock_number),
            "quantity": (
                equipment.quantity
                if equipment.quantity is not None
                else "N/A"
            ),
        })

    # ---------------------------------------------------------
    # Report Data
    # ---------------------------------------------------------
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
def reports_interactive2(request):
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

    # ---------------------------------------------------------
    # Helper: Return N/A for None or empty string values
    # ---------------------------------------------------------
    def display_value(value):
        if value is None or value == "":
            return "N/A"
        return value

    # ---------------------------------------------------------
    # Service Requests
    # ---------------------------------------------------------
    service_requests = (
        ServiceRequest.objects
        .filter(company=user_company)
        .select_related(
            "customer",
            "manager_employee",
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
        service_type_name = "N/A"

        if service_request.service_type:
            service_type = service_request.service_type
            service_type.decrypt_fields(user=request.user)
            service_type_name = display_value(service_type.name)

        service_request_data.append({
            "id": str(service_request.id),
            "number": display_value(
                service_request.service_request_number
            ),
            "start_date": (
                service_request.start_date.isoformat()
                if service_request.start_date
                else "N/A"
            ),
            "end_date": (
                service_request.end_date.isoformat()
                if service_request.end_date
                else "N/A"
            ),
            "status": display_value(service_request.status),
            "service_type": service_type_name,
            "customer": (
                display_value(str(service_request.customer))
                if service_request.customer
                else "N/A"
            ),
            "created": (
                service_request.created_timestamp.isoformat()
                if service_request.created_timestamp
                else "N/A"
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
            "number": display_value(invoice.invoice_number),
            "issue_date": (
                invoice.issue_date.isoformat()
                if invoice.issue_date
                else "N/A"
            ),
            "due_date": (
                invoice.due_date.isoformat()
                if invoice.due_date
                else "N/A"
            ),
            "status": display_value(invoice.payment_status),
            "customer": (
                display_value(str(invoice.customer))
                if invoice.customer
                else "N/A"
            ),
            "created": (
                invoice.created_at.isoformat()
                if invoice.created_at
                else "N/A"
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
        # Decrypt fields using the current logged-in user.
        employee.decrypt_fields(user=request.user)

        employee_data.append({
            "id": str(employee.id),
            "employee_number": display_value(
                employee.employee_number
            ),
            "first_name": display_value(employee.first_name),
            "last_name": display_value(employee.last_name),
            "position": display_value(employee.position),
            "department": display_value(employee.department),
            "status": (
                display_value(str(employee.status))
                if employee.status
                else "N/A"
            ),
        })

    logger.info(
        "INTERACTIVE REPORT - employee count=%s",
        employees.count(),
    )

    logger.info(
        "EMPLOYEE REPORT - queryset=%s serialized=%s unique_ids=%s",
        employees.count(),
        len(employee_data),
        len({row["id"] for row in employee_data}),
    )

    # ---------------------------------------------------------
    # Equipment
    # ---------------------------------------------------------
    equipment_queryset = (
        Equipment.objects
        .filter(company=user_company)
        .order_by("name")
    )

    equipment_data = []

    for equipment in equipment_queryset:
        # Decrypt fields using the current logged-in user.
        equipment.decrypt_fields(user=request.user)

        equipment_data.append({
            "id": str(equipment.id),
            "name": display_value(equipment.name),
            "category": display_value(equipment.category),
            "make": display_value(equipment.make),
            "model": display_value(equipment.model),
            "stock_number": display_value(equipment.stock_number),
            "quantity": (
                equipment.quantity
                if equipment.quantity is not None
                else "N/A"
            ),
        })

    # ---------------------------------------------------------
    # Report Data
    # ---------------------------------------------------------
    report_data = {
        "service_requests": service_request_data,
        "invoices": invoice_data,
        "employees": employee_data,
        "equipment": equipment_data,
    }

    return render(
        request,
        "reports_interactive2.html",
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
