import uuid
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings
id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class UserPayment(models.Model):
    app_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    company = models.ForeignKey(
        'app.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='payments'
    )
    payment_bool = models.BooleanField(default=False)
    stripe_checkout_id = models.CharField(max_length=500, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=500, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=500, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Set company to user's company if not already set
        if not self.company and hasattr(self.app_user, "company"):
            self.company = self.app_user.company

        if self.stripe_checkout_id:
                self.payment_bool = True

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.app_user} - Paid: {self.payment_bool}"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_payment(sender, instance, created, **kwargs):
    if created:
        company = getattr(instance, 'company', None)
        UserPayment.objects.create(
            app_user=instance,
            company=company,
            payment_bool=company.is_company_subscription_active if company else False
        )