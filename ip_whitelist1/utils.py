from .models import AccessLog

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_user_ip(request):
        if request.user.is_authenticated:
            ip_address = get_client_ip(request)
            if not AccessLog.objects.filter(user=request.user, ip_address=ip_address).exists():
                AccessLog.objects.create(user=request.user, ip_address=ip_address)
