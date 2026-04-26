from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import *

# Customize admin site headers
admin.site.site_header = _("TRADE-SEC ADMIN")
admin.site.site_title = _("TRADESEC 1.0 PROTOTYPE ALPHA PLATFORM ADMIN Portal")
admin.site.index_title = _("Welcome to TRADESEC ADMIN")


# -------------------------------
# Customer Admin
# -------------------------------
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)
    readonly_fields = [
        'email', 'name', 'created_by_user', 'address',
        'payment_terms', 'payment_method', 'phone_number', 'account_rep'
    ]


# -------------------------------
# Invoice Admin
# -------------------------------
@admin.register(Invoice)
class CustomerInvoice(admin.ModelAdmin):
    list_display = ('id',)
    search_fields = ('id',)
    list_filter = ('id',)
    readonly_fields = [
        'service_request', 'customer', 'created_by_user',
        'created_at'
    ]

@admin.register(Quote)
class CustomerQuote(admin.ModelAdmin):
    list_display = ('quote_number', 'created_at')
    search_fields = ('quote_number', 'created_at')
    list_filter = ('quote_number', 'created_at')
    readonly_fields = [
        'service_request', 'created_by_user', 'quote_number',
        'customer', 'total'
    ]

# -------------------------------
# Product Admin
# -------------------------------
class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1

class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('part_number', 'name', 'display_sizes', 'display_colors', 'price', 'stripe_price_id', 'image_filename', 'order_number')
    list_editable = ('order_number',)
    list_filter = ('sizes__size', 'colors__color')
    inlines = [ProductSizeInline, ProductColorInline]
    ordering = ('order_number', 'name')

    def display_sizes(self, obj):
        return ", ".join([s.size for s in obj.sizes.all()])
    display_sizes.short_description = 'Sizes'

    def display_colors(self, obj):
        return ", ".join([c.color for c in obj.colors.all()])
    display_colors.short_description = 'Colors'

admin.site.register(Product, ProductAdmin)


# -------------------------------
# Order Item Inline (Read-only)
# -------------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_display', 'quantity', 'selected_size', 'selected_color', 'total_price')
    can_delete = False

    def total_price(self, obj):
        return obj.quantity * obj.product.price
    total_price.short_description = 'Total Price'

    # Display product with full name, size and color
    def product_display(self, obj):
        size = obj.selected_size.size if obj.selected_size else "N/A"
        color = obj.selected_color.color if obj.selected_color else "N/A"
        return f"{obj.product.name} - Size: {size}, Color: {color}"
    product_display.short_description = 'Product'


# -------------------------------
# Order Admin
# -------------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'guest_email', 'is_guest_order', 'paid', 'created_at', 'total_amount_display')
    readonly_fields = (
        'user', 'guest_email', 'guest_name', 'is_guest_order',
        'billing_address_display', 'shipping_address_display',
        'stripe_payment_intent', 'paid', 'created_at'
    )
    inlines = [OrderItemInline]
    search_fields = ('user__email', 'guest_email')
    list_filter = ('paid', 'is_guest_order', 'created_at')

    # Display billing address as text
    def billing_address_display(self, obj):
        if obj.billing_address:
            a = obj.billing_address
            return f"{a.full_name}\n{a.line1}\n{a.line2 or ''}\n{a.city}, {a.state} {a.postal_code}\n{a.country}\nPhone: {a.phone_number or '-'}"
        return "-"
    billing_address_display.short_description = 'Billing Address'

    # Display shipping address as text
    def shipping_address_display(self, obj):
        if obj.shipping_address:
            a = obj.shipping_address
            return f"{a.full_name}\n{a.line1}\n{a.line2 or ''}\n{a.city}, {a.state} {a.postal_code}\n{a.country}\nPhone: {a.phone_number or '-'}"
        return "-"
    shipping_address_display.short_description = 'Shipping Address'

    # Display total order amount
    def total_amount_display(self, obj):
        return sum(item.quantity * item.product.price for item in obj.items.all())
    total_amount_display.short_description = 'Order Total'


# -------------------------------
# OrderItem Admin (Optional)
# -------------------------------
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'selected_size', 'selected_color', 'total_price')
    readonly_fields = ('order', 'product', 'quantity', 'selected_size', 'selected_color')

    def total_price(self, obj):
        return obj.quantity * obj.product.price
    total_price.short_description = 'Total Price'

admin.site.register(OrderItem, OrderItemAdmin)


# -------------------------------
# Address Admin
# -------------------------------
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'line1', 'line2', 'city', 'state', 'postal_code', 'country', 'phone_number')
    readonly_fields = ('full_name', 'line1', 'line2', 'city', 'state', 'postal_code', 'country', 'phone_number')
