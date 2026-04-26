from django.shortcuts import render, redirect
from .forms import ContactUsRequestForm

def contact_us_view(request):
    if request.method == "POST":
        form = ContactUsRequestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("contact_success")
    else:
        form = ContactUsRequestForm()
    return render(request, "contact_form.html", {"form": form})

def contact_success_view(request):
    return render(request, "contact_success.html")