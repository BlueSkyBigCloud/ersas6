import stripe
from django.conf import settings
from business.models import Product

stripe.api_key = settings.STRIPE_SECRET_KEY

def sync_products_to_stripe():
    products = Product.objects.all()
    for product in products:
        if not product.stripe_price_id:
            # Create Stripe Product
            stripe_product = stripe.Product.create(
                name=product.name,
                description=f"{product.color} / {product.size}" if product.color or product.size else None,
                metadata={"part_number": product.part_number}
            )
            # Create Stripe Price in cents
            stripe_price = stripe.Price.create(
                unit_amount=int(product.price * 100),
                currency="usd",
                product=stripe_product.id
            )
            # Save Stripe price ID
            product.stripe_price_id = stripe_price.id
            product.save()
            print(f"Synced {product.name} to Stripe")