from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from app.decorators import onboarded
from .models import *
from app.models import *
from .forms import *
# Create your views here.
from django.shortcuts import redirect, get_object_or_404
import stripe
from django.conf import settings
from django.shortcuts import redirect


@login_required
@onboarded()
def businesscenter_view(request):
    customers = Customer.objects.filter(created_by_user=request.user)  # Filter by user
    return render(request, 'businesscenter.html', {'customers': customers})


@login_required
@onboarded()
def add_customer_view(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)  # Do not save to the database yet
            customer.created_by_user = request.user  # Assign the logged-in user
            customer.save()  # Save with the assigned user
            return redirect('business_center')  # Redirect to the list view after saving
    else:
        form = CustomerForm()
    return render(request, 'add_customer.html', {'form': form})

@login_required
def invoicelist_view(request):
    invoices = Invoice.objects.filter(created_by_user=request.user)
    return render(request, 'invoice_list.html', {'invoices': invoices})

def invoicecustomerlist_view(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    invoices = Invoice.objects.filter(customer=customer)  # Filter invoices
    return render(request, 'invoice_customer_detail.html', {'invoices': invoices, 'customer': customer})


from app.models import *

@login_required
def create_invoice(request, id):
    # Get the actual ServiceRequest instance using the ID from the URL
    service_request = get_object_or_404(ServiceRequest, id=id)

    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by_user = request.user

            # Correctly link the ServiceRequest to the Invoice
            invoice.service_request = service_request
            invoice.customer = service_request.customer
            invoice.save()  

            # Calculate days and create a line item
            if service_request.start_date and service_request.end_date:
                days_difference = (service_request.end_date - service_request.start_date).days
                service_type = service_request.service_type

                if days_difference > 0 and service_type:
                    LineItem.objects.create(
                        invoice=invoice,
                        description=f"{service_type.decrypt_fields(request.user)} ({days_difference} days)",
                        quantity=days_difference,
                        unit_price=service_type.daily_rate,
                        total_price=days_difference * service_type.daily_rate
                    )

            return redirect('invoice_list')  
    else:
        form = InvoiceForm()

    return render(request, 'create_invoice.html', {
        'form': form,
        'servicerequest': service_request,
    })



@login_required
def edit_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    line_items = invoice.line_items.all()

    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=invoice)

        # Processing line items manually
        descriptions = request.POST.getlist("description")
        quantities = request.POST.getlist("quantity")
        unit_prices = request.POST.getlist("unit_price")
        line_item_ids = request.POST.getlist("line_item_id")

        # Update existing line items or create new ones
        for i in range(len(descriptions)):
            description = descriptions[i].strip()
            quantity = quantities[i].strip()
            unit_price = unit_prices[i].strip()
            line_item_id = line_item_ids[i].strip()

            if description and quantity and unit_price:
                total_price = float(quantity) * float(unit_price)

                if line_item_id:  # Update existing LineItem
                    line_item = LineItem.objects.get(id=line_item_id)
                    line_item.description = description
                    line_item.quantity = quantity
                    line_item.unit_price = unit_price
                    line_item.total_price = total_price
                    line_item.save()
                else:  # Create new LineItem
                    LineItem.objects.create(
                        invoice=invoice,
                        description=description,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price,
                    )

        if form.is_valid():
            form.save()
            return redirect('invoice_detail', id=invoice.id)

    else:
        form = InvoiceForm(instance=invoice)

    return render(request, 'edit_invoice.html', {'invoice': invoice, 'form': form, 'line_items': line_items})


@login_required
def invoice_detail(request, id):
    invoice = get_object_or_404(Invoice, id=id)
    return render(request, 'invoice_detail.html', {'invoice': invoice})

@login_required
def businesscustomer_view(request, customer_id):
    # Retrieve the BusinessCustomer object by its ID
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Render the details in a template
    return render(request, 'businesscustomer.html', {
        'customer': customer,
    })


@login_required
def edit_customer_view(request, id):
    customer = get_object_or_404(Customer, id=id)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('businesscustomer_view', customer_id=customer.id)  # Redirect after saving
    else:
        form = CustomerForm(instance=customer)

    return render(request, 'edit_customer.html', {'form': form, 'customer': customer})


@login_required
@onboarded()
def inventory_view(request):
    customers = Customer.objects.filter(created_by_user=request.user)  # Filter by user
    return render(request, 'businesscenter.html', {'customers': customers})



@login_required
def quotelist_view(request):
    quotes = Quote.objects.filter(created_by_user=request.user)
    return render(request, 'quote_list.html', {'quotes': quotes})

@login_required
def quotecustomerlist_view(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    quotes = Quote.objects.filter(customer=customer)
    return render(request, 'quote_customer_detail.html', {
        'quotes': quotes,
        'customer': customer,
    })

@login_required
def create_quote(request, id):
    service_request = get_object_or_404(ServiceRequest, id=id)

    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.created_by_user = request.user
            quote.service_request = service_request
            quote.customer = service_request.customer
            quote.save()

            # Auto-generate a default line item based on service type & duration
            if service_request.start_date and service_request.end_date:
                days_difference = (service_request.end_date - service_request.start_date).days
                service_type = service_request.service_type

                if days_difference > 0 and service_type:
                    QuoteLineItem.objects.create(
                        quote=quote,
                        description=f"{service_type.decrypt_fields(request.user)} ({days_difference} days)",
                        quantity=days_difference,
                        unit_price=service_type.daily_rate,
                        total_price=days_difference * service_type.daily_rate
                    )

            return redirect('quote_list')
    else:
        form = QuoteForm()

    return render(request, 'create_quote.html', {
        'form': form,
        'servicerequest': service_request,
    })
@login_required
def edit_quote(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)

    if request.method == "POST":
        form = QuoteForm(request.POST, instance=quote)

        # Extract line item data
        descriptions = request.POST.getlist("description")
        quantities = request.POST.getlist("quantity")
        unit_prices = request.POST.getlist("unit_price")
        line_item_ids = request.POST.getlist("line_item_id")
        delete_ids = request.POST.getlist("delete_item")  # checkboxes for deletion

        # First: delete items flagged for removal
        if delete_ids:
            QuoteLineItem.objects.filter(id__in=delete_ids, quote=quote).delete()

        # Process each submitted row
        for desc, qty, price, item_id in zip(descriptions, quantities, unit_prices, line_item_ids):
            desc, qty, price, item_id = desc.strip(), qty.strip(), price.strip(), item_id.strip()

            if not (desc and qty and price):
                continue  # skip incomplete rows

            try:
                qty = Decimal(qty)
                price = Decimal(price)
            except (ValueError, InvalidOperation):
                continue  # skip invalid inputs

            if item_id:
                # Update existing line item
                line_item = get_object_or_404(QuoteLineItem, id=item_id, quote=quote)
                line_item.description = desc
                line_item.quantity = qty
                line_item.unit_price = price
                line_item.save()  # model .save() recalculates total_price
            else:
                # Create a new line item
                QuoteLineItem.objects.create(
                    quote=quote,
                    description=desc,
                    quantity=qty,
                    unit_price=price,
                )

        # Save quote itself
        if form.is_valid():
            form.save()
            return redirect("quote_detail", id=quote.id)

    else:
        form = QuoteForm(instance=quote)

    return render(request, "edit_quote.html", {
        "quote": quote,
        "form": form,
        "line_items": quote.line_items.all(),  # use related_name
    })

@login_required
def quote_detail(request, id):
    quote = get_object_or_404(Quote, id=id)
    return render(request, 'quote_detail.html', {'quote': quote})


stripe.api_key = settings.STRIPE_SECRET_KEY



def checkout_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    line_items = [
        {
            'price': item.product.stripe_price_id,
            'quantity': item.quantity,
        } for item in order.items.all()
    ]

    checkout_session = stripe.checkout.Session.create(
        customer_email=order.user.email if order.user else order.guest_email,
        payment_method_types=['card'],
        mode='payment',
        line_items=line_items,
        success_url=request.build_absolute_uri('/success/') + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri('/cancel/'),
    )

    order.stripe_payment_intent = checkout_session.payment_intent
    order.save()

    return redirect(checkout_session.url, code=303)



from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def stripe_webhook(request):
    print(">>> VIEW TWO IS ACTIVE")
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        payment_intent = session.get('payment_intent')

        try:
            order = Order.objects.get(stripe_payment_intent=payment_intent)
            order.paid = True
            order.save()
        except Order.DoesNotExist:
            pass

    return HttpResponse(status=200)

def sync_products_to_stripe():
    products = Product.objects.all()
    for product in products:
        if not product.stripe_price_id:
            # Create a Stripe product
            stripe_product = stripe.Product.create(
                name=product.name,
                description=f"{product.color} / {product.size}" if product.color or product.size else None,
                metadata={
                    "part_number": product.part_number
                }
            )

            # Create a Stripe price (in cents)
            stripe_price = stripe.Price.create(
                unit_amount=int(product.price * 100),  # Stripe uses cents
                currency="usd",
                product=stripe_product.id
            )

            # Save Stripe price ID in Django
            product.stripe_price_id = stripe_price.id
            product.save()
            print(f"Synced {product.name} to Stripe")

from django.contrib import messages
from datetime import date, timedelta


@login_required
def convert_quote_to_invoice(request, pk):
    quote = get_object_or_404(Quote, pk=pk)

    # Set due date 30 days from today
    due_date = date.today() + timedelta(days=30)

    invoice = Invoice.objects.create(
        customer=quote.customer,
        service_request=quote.service_request,
        created_by_user=request.user,
        due_date=due_date,  # ✅ must set this
        notes=getattr(quote, "notes", ""),  # safely handle missing notes
    )

    # Copy line items
    for item in quote.line_items.all():
        LineItem.objects.create(
            invoice=invoice,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price,
        )

    messages.success(request, f"Quote {quote.quote_number} converted to Invoice {invoice.id}")
    return redirect("invoice_detail", id=invoice.id)