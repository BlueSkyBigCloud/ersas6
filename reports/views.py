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
            "reports/dashboard.html",
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