from django.db import models
from users.models import CustomUser
from django.utils.timezone import now

class IPWhiteList(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="whitelisted_ips", null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.ip_address}"
        return f"Global whitelist - {self.ip_address}"  



class AccessLog(models.Model):
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='logs'
    )
    ip_address = models.GenericIPAddressField()
    accessed_at = models.DateTimeField(auto_now_add=True)
    page_viewed = models.CharField(max_length=255, null=True, blank=True)  # New field
    user_agent = models.TextField(null=True, blank=True)  # Fix: Add user agent field


    @property
    def user_name(self):
        return self.user.name if self.user else "Guest"

    def __str__(self):
        return f"{self.ip_address} - {self.page_viewed} - {self.accessed_at}"
    


class Blocked_IPAddress(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)  # Store the IP address
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the block was added
    reason = models.CharField(max_length=255, blank=True, null=True)  # Optional reason for blocking

    def __str__(self):
        return f"Blocked IP: {self.ip_address}"