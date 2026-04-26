from .forms import TransactionForm, ItemForm
from django.shortcuts import render, get_object_or_404, redirect
from .models import Item, Transaction
from django.contrib.auth.decorators import login_required, user_passes_test
from app.decorators import onboarded

def staff_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect("dashboard")  # 👈 change "home" to your actual home view name
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@staff_required
@login_required
@onboarded()
def item_list(request):
    items = Item.objects.all()
    transactions = Transaction.objects.all().order_by("-date")

    # Handle Item form submission
    if request.method == 'POST' and 'add_item' in request.POST:
        item_form = ItemForm(request.POST)
        if item_form.is_valid():
            item_form.save()
            return redirect('item_list')
    else:
        item_form = ItemForm()

    # Handle Transaction form submission
    if request.method == 'POST' and 'add_transaction' in request.POST:
        transaction_form = TransactionForm(request.POST)
        if transaction_form.is_valid():
            transaction_form.save()
            return redirect('item_list')
    else:
        transaction_form = TransactionForm()

    return render(request, "item_list.html", {
        "items": items,
        "transactions": transactions,
        "item_form": item_form,
        "transaction_form": transaction_form,
    })

@staff_required
@login_required
@onboarded()
def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    transactions = Transaction.objects.filter(item=item).order_by("-date")
    return render(request, "item_detail.html", {
        "item": item,
        "transactions": transactions
    })

from .forms import TransactionForm

@staff_required
@login_required
@onboarded()
def transaction_create(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("item_list")
    else:
        form = TransactionForm()
    return render(request, "transaction_form.html", {"form": form})