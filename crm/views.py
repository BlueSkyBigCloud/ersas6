from django.shortcuts import render, redirect
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
from app.decorators import onboarded
# Create your views here.

@login_required
@onboarded()
def opportunity_list(request):
    opportunities = Opportunity.objects.all()
    return render(request, 'opportunity_list.html', {'opportunities': opportunities})

@login_required
@onboarded()
def opportunity_create(request):
    if request.method == 'POST':
        form = OpportunityForm(request.POST, current_user=request.user)
        if form.is_valid():
            form.save()
            return redirect('opportunity_list')  # Redirect to opportunity list after saving
    else:
        form = OpportunityForm(current_user=request.user)
    return render(request, 'opportunity_form.html', {'form': form})