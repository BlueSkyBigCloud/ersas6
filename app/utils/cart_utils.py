def get_cart(request):
    """Retrieve the cart from the session."""
    return request.session.get('cart', {})

def save_cart(request, cart):
    """Save the cart back to the session."""
    request.session['cart'] = cart
    request.session.modified = True

def add_to_cart(request, product_id, quantity=1, size_id=None, color_id=None):
    """Add an item to the session-based cart."""
    cart = get_cart(request)
    key = f"{product_id}-{size_id or 'none'}-{color_id or 'none'}"

    if key in cart:
        cart[key]['quantity'] += int(quantity)
    else:
        cart[key] = {
            'product_id': product_id,
            'quantity': int(quantity),
            'size_id': size_id,
            'color_id': color_id,
        }

    save_cart(request, cart)

def remove_from_cart(request, key):
    """Remove an item from the cart."""
    cart = get_cart(request)
    if key in cart:
        del cart[key]
        save_cart(request, cart)

from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0