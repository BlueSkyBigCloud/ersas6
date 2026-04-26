from django.shortcuts import render
from .models import Analysis_ServiceRequest
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Avg
from django.db.models import Avg, Min, Max, Variance
from django.contrib.auth.decorators import login_required
from app.decorators import onboarded


@login_required
@onboarded()
def priceanalysis_dashboard(request):
    """
    Render the US map + chart template.
    """
    return render(request, "market_analysis2.html")

@login_required
@onboarded()
def priceanalysis_dashboard1(request):
    """
    Render the US map + chart template.
    """
    return render(request, "market_analysis3.html")

@login_required
@onboarded()
def priceanalysis_dashboard2(request):
    """
    Render the US map + chart template.
    """
    return render(request, "market_analysis4.html")

@login_required
@onboarded()
def priceanalysis_dashboard3(request):
    """
    Render the US map + chart template.
    """
    return render(request, "market_analysis5.html")


@login_required
@onboarded()
def price_data(request):
    """
    JSON endpoint to return average prices by service type for a given state.

    Query params:
      - state: two-letter US state code (e.g., 'CA')
    Response:
      {
        "state": "CA",
        "data": [
          {"service_type": "Plumbing", "avg_price": 120.5},
          {"service_type": "Electrical", "avg_price": 95.0},
          ...
        ]
      }
    """
    state = request.GET.get("state", "").strip().upper()
    if not state or len(state) != 2:
        return JsonResponse(
            {"error": "Provide a valid two-letter state code (?state=CA)"},
            status=400,
        )

    qs = (
        Analysis_ServiceRequest.objects.filter(state=state)
        .values("service_type__name")
        .annotate(avg_price=Avg("price"))
        .order_by("-avg_price")
    )

    data = [
        {"service_type": item["service_type__name"], "avg_price": float(item["avg_price"] or 0)}
        for item in qs
    ]

    return JsonResponse({"state": state, "data": data})

from django.db.models import Avg, Min, Max
from django.http import JsonResponse
from .models import Analysis_ServiceRequest, Analysis_ServiceType, Analysis_State, Analysis_ZipPrice

@login_required
@onboarded()
def zip_price_data(request):
    state_code = request.GET.get("state")
    zip_code = request.GET.get("zip")

    if not state_code:
        return JsonResponse({"error": "State is required"}, status=400)

    try:
        state_obj = Analysis_State.objects.get(code=state_code)
    except Analysis_State.DoesNotExist:
        return JsonResponse({"error": f"State {state_code} not found"}, status=404)

    # ZIP-level detail
    if zip_code:
        prices = Analysis_ZipPrice.objects.filter(state=state_obj, zip_code=zip_code)
        if not prices.exists():
            return JsonResponse({"error": f"No price data for ZIP {zip_code} in {state_code}"}, status=404)

        data = [{
            "service_type": p.service_type.name,
            "avg_price": float(p.avg_price),
            "min_price": float(p.min_price),
            "max_price": float(p.max_price),
            "variance": float(p.variance),
            "zip_code": p.zip_code,
        } for p in prices]

        return JsonResponse({"state": state_code, "zip": zip_code, "data": data})

    # STATE summary: list ZIPs in that state
    zip_prices = Analysis_ZipPrice.objects.filter(state=state_obj).values("zip_code").distinct()
    if not zip_prices.exists():
        return JsonResponse({"error": f"No ZIP data for {state_code}"}, status=404)

    data = [{"zip_code": z["zip_code"]} for z in zip_prices]
    return JsonResponse({"state": state_code, "zip": "", "data": data})