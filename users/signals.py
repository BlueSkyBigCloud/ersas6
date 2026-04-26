# users/signals.py
import stripe
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import CustomUser
from .utils import generate_coupon_code

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_coupon(sender, instance, created, **kwargs):
    if created and not instance.stripe_coupon_id:
        # Generate a unique alphanumeric coupon code
        code = generate_coupon_code()

        # Create the coupon in Stripe
        coupon = stripe.Coupon.create(
            id=code,  # Use our custom code as the Stripe ID
            name=f"{instance.username}'s Coupon",
            percent_off=10,
            duration="once",
        )

        # Save both the code and Stripe ID
        instance.coupon_code = code
        instance.stripe_coupon_id = coupon.id
        instance.save()