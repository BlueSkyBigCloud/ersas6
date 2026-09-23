from django.db import models
from django.conf import settings
from app.models import *
from django.db.models.signals import pre_save
from django.dispatch import receiver
import uuid
import random
import string
from django.core.validators import RegexValidator
from django.contrib.postgres.fields import ArrayField


class Customer(models.Model):

    PAYMENT_TERMS = [
        ('MONTHLY', 'MONTHLY'),
        ('30DAYS', '30DAYS'),
        ('DUEONINVOICE', 'DUEONINVOICE'),
        ('ANNUAL', 'ANNUAL'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('CREDIT_CARD', 'Credit Card'),
        ('BANK_TRANSFER', 'Bank Transfer'),
    ]

    ADDRESS_TYPE_CHOICES = [
        ('BILLING', 'Billing'),
        ('SHIPPING', 'Shipping'),
        ('MAILING', 'Mailing'),
        ('OTHER', 'Other'),
    ]

    customer_number_validator = RegexValidator(
        regex=r'^[A-Za-z0-9]{6,16}$',
        message=(
            'Customer number must contain only letters and numbers '
            'and be 6 to 16 characters long.'
        )
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    customer_number = models.CharField(
        max_length=16,
        blank=True,
        null=True,
        validators=[customer_number_validator]
    )

    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers'
    )

    name = models.CharField(
        max_length=255
    )

    # ---------------------------------------------------------
    # Primary / Structured Address
    # ---------------------------------------------------------

    address_type = models.CharField(
        max_length=20,
        choices=ADDRESS_TYPE_CHOICES,
        default='MAILING'
    )

    address_line_1 = models.CharField(
        max_length=255,
        blank=True
    )

    address_line_2 = models.CharField(
        max_length=255,
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    state = models.CharField(
        max_length=100,
        blank=True
    )

    postal_code = models.CharField(
        max_length=20,
        blank=True
    )

    country = models.CharField(
        max_length=100,
        default='United States',
        blank=True
    )

    # ---------------------------------------------------------
    # Combined Address
    # ---------------------------------------------------------

    address = models.TextField(
        blank=True
    )

    # ---------------------------------------------------------
    # Additional Customer Addresses
    #
    # Each item is a complete address stored as a string.
    #
    # Example:
    #
    # [
    #     "123 Main Street\nHouston, Texas 77001\nUnited States",
    #     "500 Market Street\nDallas, Texas 75201\nUnited States"
    # ]
    # ---------------------------------------------------------

    address_list = ArrayField(
        base_field=models.TextField(),
        default=list,
        blank=True
    )

    email = models.CharField(
        max_length=255
    )

    payment_terms = models.CharField(
        max_length=50,
        choices=PAYMENT_TERMS
    )

    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES
    )

    phone_number = models.CharField(
        max_length=15
    )

    account_rep = models.CharField(
        max_length=255
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    company = models.ForeignKey(
        'app.Company',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='company_customers'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'customer_number'],
                name='unique_customer_number_per_company'
            ),
        ]

    def generate_customer_number(self):
        """
        Generate a random 6-character alphanumeric customer number.

        Examples:
            ABC001
            X7K92P
            4F8B21
        """

        characters = string.ascii_uppercase + string.digits

        while True:
            customer_number = ''.join(
                random.choices(characters, k=6)
            )

            if not Customer.objects.filter(
                company=self.company,
                customer_number=customer_number
            ).exists():
                return customer_number

    def build_address(self):
        """
        Combine the structured address fields into
        the primary address text field.
        """

        address_parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state,
            self.postal_code,
            self.country,
        ]

        return '\n'.join(
            part.strip()
            for part in address_parts
            if part and part.strip()
        )

    def save(self, *args, **kwargs):
        """
        Automatically generate a customer number if one
        was not provided.

        Also rebuild the primary address from the
        structured address fields.
        """

        if not self.customer_number:
            self.customer_number = self.generate_customer_number()

        self.address = self.build_address()

        if self.addres_list is None:
            self.addres_list = []

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


    

class Invoice(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    ]

    id = models.AutoField(primary_key=True)
    invoice_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, related_name='invoices')
    created_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    issue_date = models.DateField(default=now)
    due_date = models.DateField()
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey( 'app.Company', on_delete=models.PROTECT, null=True, blank=True, related_name='invoice_customers', )
    

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer.name}"

    @property
    def subtotal(self):
        """Calculate subtotal as the sum of all line item totals."""
        return sum(item.total_price for item in self.line_items.all())

    @property
    def total(self):
        """Return the subtotal (extend for taxes/discounts if needed)."""
        return self.subtotal

    @property
    def is_overdue(self):
        """Check if the invoice is overdue."""
        return self.payment_status == 'PENDING' and now().date() > self.due_date


@receiver(pre_save, sender=Invoice)
def generate_invoice_number(sender, instance, **kwargs):
    """Generates a unique invoice number using date + 5-digit sequence."""
    if not instance.invoice_number:  # Only generate if it's not set
        today_str = now().strftime('%Y%m%d')
        last_invoice = Invoice.objects.filter(invoice_number__startswith=today_str).order_by('-invoice_number').first()

        if last_invoice:
            last_number = int(last_invoice.invoice_number[-5:])  # Get last 5 digits
            new_number = last_number + 1
        else:
            new_number = 1  # Start sequence at 1

        instance.invoice_number = f"{today_str}{new_number:05d}"
        
from decimal import Decimal, InvalidOperation
from django.db import models

class LineItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="line_items")  # Add this
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        try:
            self.quantity = int(self.quantity)  # Ensure quantity is an integer
        except ValueError:
            raise ValueError("Invalid quantity. Must be a whole number.")

        try:
            self.unit_price = Decimal(self.unit_price)  # Ensure unit_price is a Decimal
        except (ValueError, InvalidOperation):
            raise ValueError("Invalid unit price. Must be a decimal number.")

        self.total_price = self.quantity * self.unit_price  # Calculate total price
        super().save(*args, **kwargs)  # Save to database

    
class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Quote(models.Model):
    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Sent", "Sent"),
        ("Accepted", "Accepted"),
        ("Declined", "Declined"),
    ]

    quote_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name="quotes")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    created_by_user = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Draft")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quote {self.quote_number} - {self.customer}"

    @property
    def line_items(self):
        """Return all line items for this quote."""
        return self.quotelineitem_set.all()

    @property
    def subtotal(self):
        """Sum of all line item totals."""
        return sum(item.total_price for item in self.line_items.all())

    @property
    def total(self):
        """Total amount (can extend for taxes/discounts later)."""
        return self.subtotal
    
@receiver(pre_save, sender=Quote)
def generate_quote_number(sender, instance, **kwargs):
    """
    Generates a unique quote number using the date + 5-digit sequence.
    Format: YYYYMMDD00001
    """
    if not instance.quote_number:
        today_str = now().strftime('%Y%m%d')
        # Get last quote created today
        last_quote = Quote.objects.filter(quote_number__startswith=today_str).order_by('-quote_number').first()

        if last_quote and last_quote.quote_number:
            last_number = int(last_quote.quote_number[-5:])
            new_number = last_number + 1
        else:
            new_number = 1

        instance.quote_number = f"{today_str}{new_number:05d}"
    
class QuoteLineItem(models.Model):
    quote = models.ForeignKey(Quote, related_name="line_items", on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        try:
            self.quantity = int(self.quantity)
        except ValueError:
            raise ValueError("Invalid quantity. Must be a whole number.")

        try:
            self.unit_price = Decimal(self.unit_price)
        except (ValueError, InvalidOperation):
            raise ValueError("Invalid unit price. Must be a decimal number.")

        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


    
class Address(models.Model):
    full_name = models.CharField(max_length=255)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, null=True)  # Added phone


    def __str__(self):
        return f"{self.full_name}, {self.line1}, {self.city}"
    

    

class Order(models.Model):
    # If the buyer is a logged-in account user
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="orders"
    )

    # Guest checkout info
    guest_email = models.EmailField(blank=True, null=True)
    guest_name = models.CharField(max_length=255, blank=True, null=True)
    is_guest_order = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    shipping_address = models.ForeignKey(
        "Address",
        on_delete=models.SET_NULL,
        null=True,
        related_name="shipping_orders"
    )
    billing_address = models.ForeignKey(
        "Address",
        on_delete=models.SET_NULL,
        null=True,
        related_name="billing_orders"
    )
    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True)
    paid = models.BooleanField(default=False)

    def total_amount(self):
        return sum(item.total_price() for item in self.items.all())

    def __str__(self):
        if self.user:
            return f"Order {self.id} by {self.user.email}"
        return f"Order {self.id} (Guest: {self.guest_email})"
    

    
class Product(models.Model):
    part_number = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)
    image_filename = models.CharField(max_length=255, blank=True, null=True)

    order_number = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        help_text="Controls display order in store"
    )

    class Meta:
        ordering = ["order_number", "name"]

    def __str__(self):
        return f"{self.name} ({self.part_number})"


class ProductSize(models.Model):
    product = models.ForeignKey(Product, related_name="sizes", on_delete=models.CASCADE)
    size = models.CharField(max_length=20)

    def __str__(self):
        return self.size


class ProductColor(models.Model):
    product = models.ForeignKey(Product, related_name="colors", on_delete=models.CASCADE)
    color = models.CharField(max_length=20)

    def __str__(self):
        return self.color
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    selected_size = models.ForeignKey(ProductSize, null=True, blank=True, on_delete=models.SET_NULL)
    selected_color = models.ForeignKey(ProductColor, null=True, blank=True, on_delete=models.SET_NULL)

    def total_price(self):
        return self.quantity * self.product.price
    

class SubscriptionPlan(models.Model):
    """Defines an available plan users can subscribe to."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")

    # Billing interval: monthly, yearly, etc.
    INTERVAL_CHOICES = [
        ("day", "Daily"),
        ("week", "Weekly"),
        ("month", "Monthly"),
        ("year", "Yearly"),
    ]
    billing_interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES, default="month")

    # Stripe integration
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)

    # Optional metadata
    features = models.JSONField(blank=True, null=True, help_text="List of included features")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.price} {self.currency}/{self.billing_interval}"
    

class Subscription(models.Model):
    """Represents a user's active or past subscription."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to your CustomUser model
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions"
    )

    plan = models.ForeignKey(
    "SubscriptionPlan",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="subscriptions"
)
    
    description = models.TextField(blank=True, null=True)

    # Subscription lifecycle
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    next_billing_date = models.DateTimeField(blank=True, null=True)

    # Stripe integration
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_invoice_id = models.CharField(max_length=255, blank=True, null=True)

    # Billing
    billing_address = models.ForeignKey(
        "Address",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="billing_subscriptions"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default="USD")

    # Status
    STATUS_CHOICES = [
        ("active", "Active"),
        ("canceled", "Canceled"),
        ("expired", "Expired"),
        ("trialing", "Trialing"),
        ("past_due", "Past Due"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    auto_renew = models.BooleanField(default=True)
    canceled_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def cancel(self):
        """Cancel this subscription."""
        self.status = "canceled"
        self.auto_renew = False
        self.canceled_at = timezone.now()
        self.save()

    def is_active(self):
        """Return True if subscription is currently active."""
        return self.status == "active" and (
            not self.end_date or self.end_date > timezone.now()
        )

    def __str__(self):
        return f"{self.plan_name} ({self.user.email}) - {self.status}"