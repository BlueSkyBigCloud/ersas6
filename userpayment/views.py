from django.shortcuts import redirect, render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from userpayment.models import UserPayment
import stripe
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from users.models import CustomUser

import logging

logger = logging.getLogger(__name__)


def send_admin_payment_email(customer_email, amount_total, currency):
    """Send notification email to contact@tradesec.us when payment succeeds."""
    subject = "✅ New Stripe Payment Successful"
    message = f"""
A payment has been successfully completed on TradeSec.

Customer Email: {customer_email}
Amount: {amount_total:.2f} {currency.upper()}

Please verify this payment in the Stripe dashboard.
"""

    msg = MIMEMultipart()
    msg['From'] = 'TradeSec <contact@tradesec.us>'
    msg['To'] = 'contact@tradesec.us', 'nrsimports@nrsimports.com'
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.sendmail(msg['From'], msg['To'], msg.as_string())
        logger.info(f"Payment notification email sent for {customer_email}")
    except Exception as e:
        logger.error(f"Error sending admin email: {e}")


def payment_successful(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    checkout_session_id = request.GET.get('session_id')

    if not checkout_session_id:
        return render(request, 'success.html', {'error': 'Missing session ID.'})

    try:
        session = stripe.checkout.Session.retrieve(checkout_session_id)

        # Prefer customer_details (which is always populated)
        customer_details = session.get('customer_details', {})

        # Save payment record
        user_payment, _ = UserPayment.objects.get_or_create(app_user=request.user)
        user_payment.stripe_checkout_id = checkout_session_id
        user_payment.save()

        context = {
            'customer_name': customer_details.get('name', 'Customer'),
            'customer_email': customer_details.get('email', 'N/A'),
            'amount_total': session.get('amount_total', 0) / 100,  # convert cents to dollars
            'currency': session.get('currency', 'usd').upper(),
        }

        return render(request, 'success.html', context)

    except Exception as e:
        print(f"Stripe success error: {e}")
        return render(request, 'success.html', {'error': str(e)})


def payment_cancelled(request):
	stripe.api_key = settings.STRIPE_SECRET_KEY
	return render(request, 'cancel.html')


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Handle successful subscription
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        customer_email = session.get('customer_details', {}).get('email', 'Unknown')
        amount_total = session.get('amount_total', 0) / 100  # cents → dollars
        currency = session.get('currency', 'usd')

        try:
            user_payment = UserPayment.objects.get(stripe_customer_id=customer_id)
            user_payment.payment_bool = True
            user_payment.stripe_subscription_id = subscription_id
            user_payment.save()
        except UserPayment.DoesNotExist:
            pass

        send_admin_payment_email(customer_email, amount_total, currency)

    return HttpResponse(status=200)




def send_email(user_email, city, product_option, quantity, start_date, end_date):
    subject = 'Booking Details'
    message = f"""
    Congratulations and welcome to Trade Sec!!! Your new  Resource Platform!
    
	Please complete your company onboarding and email contact@tradesec.us to request assistance completing your profile. If you have not already, ensure proper payment within 48 hours so that your account is not cancelled.

    Thank you and looking forward to serving you.
    """

    msg = MIMEMultipart()
    msg['From'] = 'TradeSec.us <contact@tradesec.us>'
    msg['To'] = user_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.sendmail(msg['From'], msg['To'], msg.as_string())
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending email: {e}")

@login_required
def product_page(request):
	stripe.api_key = settings.STRIPE_SECRET_KEY

	return render(request, 'product_page.html')

from django.utils import timezone
from datetime import timedelta

@login_required
def account_billing(request):
    user_payment = UserPayment.objects.filter(app_user=request.user).first()

    if not user_payment or not user_payment.stripe_checkout_id:
        return render(request, "account_billing.html", {"billing_history": None, "error": "No billing history found."})

    # Retrieve Stripe invoices
    invoices = stripe.Invoice.list(customer=user_payment.stripe_checkout_id, limit=10)

    # Format invoice data for display
    billing_history = [
        {
            "id": invoice.id,
            "amount_paid": invoice.amount_paid / 100,  # Convert cents to dollars
            "currency": invoice.currency.upper(),
            "status": invoice.status,
            "date": invoice.created,
            "pdf": invoice.invoice_pdf,
        }
        for invoice in invoices.auto_paging_iter()
    ]

    # Check if any payment was made within the last 60 days
    recent_payment = False
    for invoice in invoices.auto_paging_iter():
        invoice_date = timezone.datetime.fromtimestamp(invoice.created)
        if invoice_date >= timezone.now() - timedelta(days=45):
            recent_payment = True
            break

    # Set company to active if there is a payment within the last 60 days
    if recent_payment and request.user.company:
        request.user.company.is_company_subscription_active = True
        request.user.company.save()

    return render(request, "account_billing.html", {"billing_history": billing_history})


@login_required
def make_payment(request):
    subscription_price_id = settings.SUBSCRIPTION  # Stripe Price ID

    # Get or create UserPayment
    user_payment, _ = UserPayment.objects.get_or_create(app_user=request.user)

    # Create Stripe Customer if not exists
    if not user_payment.stripe_customer_id:
        customer = stripe.Customer.create(email=request.user.email)
        user_payment.stripe_customer_id = customer.id
        user_payment.save()

    if request.method == 'POST':
        try:
            checkout_session = stripe.checkout.Session.create(
                customer=user_payment.stripe_customer_id,
                payment_method_types=['card'],
                mode='subscription',
                line_items=[{
                    'price': subscription_price_id,
                    'quantity': 1,
                }],
                success_url=request.build_absolute_uri('/success/') + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri('/account_billing/'),
            )
            return redirect(checkout_session.url)

        except Exception as e:
            return render(request, "make_payment.html", {"error": str(e)})

    return render(request, "make_payment.html")



def create_checkout_session(amount, currency="usd", coupon_code=None):
    try:
        discounts = []

        coupon_map = {
            "DFW2025": "promo_1S8qNmGLcTDJWbqV0GuDEWMx",  # replace with your real coupon IDs from Stripe
        }
        

        # If coupon code entered and exists in map, apply discount
        if coupon_code and coupon_code.upper() in coupon_map:
            discounts = [{"promotion_code": coupon_map[coupon_code.upper()]}]

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": "Service Payment"},
                    "unit_amount": amount,
                },
                "quantity": 1,
            }],
            mode="payment",
            discounts=discounts,  # only applies if valid coupon code
            allow_promotion_codes=True,
            success_url="https://tradesec.us/success",
            cancel_url="https://tradesec.us/cancel",
        )
        return session

    except stripe.error.StripeError as e:
        return {"error": str(e)}

