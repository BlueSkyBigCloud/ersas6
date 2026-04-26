from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import IPWhiteList
from django.shortcuts import render
from .models import AccessLog, Blocked_IPAddress, IPWhiteList
from django.contrib.admin.views.decorators import staff_member_required
from users.models import *
from django.core.paginator import Paginator
from .utils import get_client_ip
from django.utils import timezone
from datetime import timedelta


@staff_member_required
def list_logged_ips(request):
    client_ip = get_client_ip(request)

    # Check if this IP is whitelisted for the current user
    is_whitelisted = IPWhiteList.objects.filter(
        user=request.user,
        ip_address=client_ip
    ).exists()

    # Evaluate abuse (only if not whitelisted AND not already blocked)
    if not is_whitelisted and not Blocked_IPAddress.objects.filter(ip_address=client_ip).exists():
        one_minute_ago = timezone.now() - timedelta(minutes=1)
        request_count = AccessLog.objects.filter(
            ip_address=client_ip,
            accessed_at__gte=one_minute_ago
        ).count()

        if request_count > 20:
            # Automatically block the IP address
            Blocked_IPAddress.objects.get_or_create(
                ip_address=client_ip,
                defaults={"reason": "Exceeded 20 requests in 1 minute"}
            )

    # Fetch logs for display
    logs = AccessLog.objects.order_by('-accessed_at')

    # Build sets of whitelisted and blocked IPs
    whitelisted_ips = set(
        IPWhiteList.objects.filter(user=request.user).values_list('ip_address', flat=True)
    )
    blocked_ips = set(Blocked_IPAddress.objects.values_list('ip_address', flat=True))

    # Paginate logs
    paginator = Paginator(logs, 250)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Mark logs as whitelisted
    for log in page_obj:
        log.is_whitelisted = log.ip_address in whitelisted_ips

    context = {
        'logs': page_obj,
        'blocked_ips': blocked_ips,  # <-- add blocked_ips for template
    }
    return render(request, 'logged_ips.html', context)



def ipwhitelist_redflag_view(request):
    return render(request, 'ipwhitelist_redflag.html')