from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Prospect
from .forms import ProspectForm, ActionForm, ConvertToCustomerForm
from django.contrib import messages
from django.db.models import Q
from django.db.models import Max, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.template.loader import render_to_string
import datetime

from django.contrib.auth.decorators import login_required
from app.decorators import onboarded

@login_required
@onboarded()
def prospect_dashboard(request):
    user_company = getattr(request.user, 'company', None)
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', '-created_at')

    prospects = Prospect.objects.filter(
    created_by_user__company=user_company
).annotate(
    last_action_date=Coalesce(Max('actions__date'), Value(datetime.datetime(1900, 1, 1)))
)

    # Filter by search
    if search_query:
        prospects = prospects.filter(
            Q(name__icontains=search_query) |
            Q(business_type__icontains=search_query) |
            Q(contact__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(website__icontains=search_query) |
            Q(products__icontains=search_query) |
            Q(company_size__icontains=search_query) |
            Q(status__icontains=search_query)
        )

    # Sort
    allowed_sorts = [
        'name', '-name', 'business_type', '-business_type', 'contact', '-contact',
        'email', '-email', 'phone_number', '-phone_number', 'company_size', '-company_size',
        'status', '-status', 'created_at', '-created_at', 'last_action_date', '-last_action_date'
    ]
    if sort_by in allowed_sorts:
        prospects = prospects.order_by(sort_by)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string(
            'partials/prospect_table_rows.html',
            {'prospects': prospects}
        )
        return JsonResponse({'html': html})

    return render(request, 'prospect_dashboard.html', {
        'prospects': prospects,
        'search_query': search_query,
        'sort_by': sort_by
    })


@login_required
@onboarded()
def create_prospect(request):
    if request.method == "POST":
        form = ProspectForm(request.POST)
        if form.is_valid():
            prospect = form.save(commit=False)
            prospect.created_by_user = request.user if request.user.is_authenticated else None
            prospect.save()
            return redirect("prospect_dashboard")
    else:
        form = ProspectForm()

    return render(request, "create_prospect.html", {"form": form})

from django.core.exceptions import PermissionDenied


@login_required
@onboarded()
def prospect_profile(request, pk):
    prospect = get_object_or_404(Prospect, pk=pk)

    if prospect.created_by_user.company != getattr(request.user, 'company', None):
        raise PermissionDenied
    
    actions = prospect.actions.all().order_by("-date")

    if request.method == "POST":
        action_form = ActionForm(request.POST)
        if action_form.is_valid():
            action = action_form.save(commit=False)
            action.prospect = prospect
            if request.user.is_authenticated:
                action.created_by_user = request.user
            action.save()
            return redirect("prospect_profile", pk=prospect.pk)
    else:
        action_form = ActionForm()

    return render(
        request,
        "prospect_profile.html",
        {"prospect": prospect, "actions": actions, "action_form": action_form},
    )

@login_required
@onboarded()
def edit_prospect(request, pk):
    prospect = get_object_or_404(Prospect, pk=pk)

    if prospect.created_by_user.company != getattr(request.user, 'company', None):
        raise PermissionDenied

    if request.method == 'POST':
        form = ProspectForm(request.POST, instance=prospect)
        if form.is_valid():
            form.save()
            return redirect('prospect_profile', pk=prospect.pk)
    else:
        form = ProspectForm(instance=prospect)

    return render(request, 'edit_prospect.html', {'form': form, 'prospect': prospect})


@login_required
@onboarded()
def convert_prospect_to_customer(request, pk):
    prospect = get_object_or_404(Prospect, pk=pk)

    if prospect.created_by_user.company != getattr(request.user, 'company', None):
        raise PermissionDenied

    if prospect.converted_customer:
        messages.warning(request, "This prospect has already been converted to a customer.")
        return redirect("prospect_profile", pk=prospect.pk)

    if request.method == "POST":
        form = ConvertToCustomerForm(request.POST)
        if form.is_valid():
            customer = prospect.convert_to_customer(
                payment_terms=form.cleaned_data["payment_terms"],
                payment_method=form.cleaned_data["payment_method"],
            )
            messages.success(request, f"Prospect '{prospect.name}' converted to Customer.")
            return redirect("prospect_profile", pk=prospect.pk)
    else:
        form = ConvertToCustomerForm()

    return render(request, "convert_prospect.html", {"prospect": prospect, "form": form})