import uuid
from django.db import models
from django.conf import settings



class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_transactions'
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='received_transactions', 
        null=True, 
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    description2 = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=10)

    def __str__(self):
        return f"Transaction {self.id} - {self.amount} {self.currency}"
    

class FinAccount(models.Model):
    ACCOUNT_TYPES = [
        ('SAVINGS', 'Savings'),
        ('CHECKING', 'Checking'),
        ('CREDIT', 'Credit'),
        ('INVESTMENT', 'Investment'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='fin_account'
    )
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    transactions = models.ManyToManyField(Transaction, related_name='accounts', blank=True)

    def __str__(self):
        return f"{self.user}'s {self.type} Account"

    @property
    def calculate_total(self):
        return sum(txn.amount for txn in self.transactions.all())

    def save(self, *args, **kwargs):
        self.total = self.calculate_total
        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return self.name