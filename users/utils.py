import string
import random

def generate_coupon_code(length=10):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")