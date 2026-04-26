import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import timedelta
from django.utils.timezone import now
from .models import IPWhiteList, AccessLog
import os
from users.models import *
from .utils import *

logger = logging.getLogger(__name__)

class LogAllIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("Middleware invoked")
        response = self.get_response(request)

        ip_address = self.get_client_ip(request)

        if request.user.is_authenticated:
            logger.debug(f"Authenticated user: {request.user}")
            self.log_ip_address(request, ip_address)
        else:
            self.log_visitor(request, ip_address)

        return response

    def log_ip_address(self, request, ip_address):
        """Logs IP for authenticated users and sends alert if needed."""
        try:
            user = request.user
            page_viewed = request.path

            # Fetch user's whitelisted IPs
            whitelisted_ips = set(IPWhiteList.objects.filter(user=user).values_list('ip_address', flat=True))
            is_whitelisted = ip_address in whitelisted_ips

            # Log the access
            AccessLog.objects.create(ip_address=ip_address, user=user, page_viewed=page_viewed)

            logger.info(f"User {user} accessed {page_viewed} from IP {ip_address} (Whitelisted: {is_whitelisted})")

            # If not whitelisted, send alert
            if not is_whitelisted:
                recent_email_sent = AccessLog.objects.filter(
                    user=user, ip_address=ip_address, accessed_at__gte=now() - timedelta(minutes=15)
                ).exists()

                if not recent_email_sent:
                    logger.debug(f"Sending alert email to {user.email} for unauthorized IP {ip_address}")
                    self.notify_user(user, ip_address, page_viewed)

        except Exception as e:
            logger.error(f"Error logging IP for user {request.user.id}: {e}")

    def log_visitor(self, request, ip_address):
        """Logs visitors who are not authenticated."""
        try:
            page_viewed = request.path
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')

            # Check if the IP is whitelisted globally
            is_whitelisted = IPWhiteList.objects.filter(ip_address=ip_address).exists()

            AccessLog.objects.create(ip_address=ip_address, user=None, page_viewed=page_viewed, user_agent=user_agent)

            logger.info(f"Visitor logged: IP {ip_address}, Page: {page_viewed}, User Agent: {user_agent}, Whitelisted: {is_whitelisted}")

        except Exception as e:
            logger.error(f"Error logging visitor: {e}")

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip.strip()

    @staticmethod
    def notify_user(user, ip_address, page_viewed):
        """Sends email alert for unauthorized access."""
        try:
            sender_email = 'contact@tradesec.us'
            sender_password = os.environ.get('EMAIL_HOST_PASSWORD')
            recipient_email = user.email
            subject = "Unauthorized Access Detected"
            body = (
                f"Your account was accessed from an unrecognized IP address: {ip_address}.\n"
                f"Page Viewed: {page_viewed}\n"
                f"If this wasn't you, please secure your account immediately."
            )

            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = recipient_email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain"))

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, message.as_string())

            logger.info(f"Notification email sent to {user.email} for IP {ip_address} on {page_viewed}")

        except Exception as e:
            logger.error(f"Error sending email to {user.email}: {e}")


from django.http import HttpResponseForbidden
from .models import Blocked_IPAddress

class BlockSpecificIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR')
        
        # Check if the IP is in the Blocked_IPAddress model
        if Blocked_IPAddress.objects.filter(ip_address=ip).exists():
            return HttpResponseForbidden("Your IP is blocked.")
        
        return self.get_response(request)
    
class AutoBlockIPMiddleware:
    REQUEST_LIMIT = 30  # requests per minute

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = get_client_ip(request)

        user = getattr(request, "user", None)

        # ✅ Check if IP is in whitelist (user-specific or global)
        is_whitelisted = IPWhiteList.objects.filter(ip_address=ip).exists()

        # Allow whitelisted IPs to bypass block and logging
        if is_whitelisted:
            return self.get_response(request)

        # Block immediately if in Blocked_IPAddress
        if Blocked_IPAddress.objects.filter(ip_address=ip).exists():
            logger.warning(f"Blocked request from IP {ip}")
            return HttpResponseForbidden(
                "Your IP has been blocked due to suspicious activity. "
                "Please email contact@tradesec.us to request being removed from our block list."
            )

        # Log the request
        page_viewed = request.path
        user_obj = user if user and user.is_authenticated else None

        AccessLog.objects.create(
            ip_address=ip,
            user=user_obj,
            page_viewed=page_viewed,
            user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown')
        )

        # Detect abuse
        one_minute_ago = timezone.now() - timedelta(minutes=1)
        request_count = AccessLog.objects.filter(
            ip_address=ip,
            accessed_at__gte=one_minute_ago
        ).count()

        if request_count > self.REQUEST_LIMIT:
            Blocked_IPAddress.objects.get_or_create(
                ip_address=ip,
                defaults={"reason": f"Exceeded {self.REQUEST_LIMIT} requests per minute"}
            )
            logger.warning(f"IP {ip} blocked automatically for exceeding {self.REQUEST_LIMIT} req/min")
            return HttpResponseForbidden(
                "Your IP has been blocked due to excessive requests. "
                "Please email contact@tradesec.us to request being removed from our block list."
            )

        # Continue processing
        return self.get_response(request)