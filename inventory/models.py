from django.db import models

from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True, help_text="Stock Keeping Unit")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reorder_level = models.PositiveIntegerField(default=0, help_text="Minimum quantity before restock")

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def in_stock(self):
        return self.quantity > 0


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("IN", "Stock In"),
        ("OUT", "Stock Out"),
        ("ADJ", "Adjustment"),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # If it's a new transaction (not updating an old one)
        if not self.pk:
            if self.transaction_type == "IN":
                self.item.quantity += self.quantity
            elif self.transaction_type == "OUT":
                self.item.quantity -= self.quantity
            elif self.transaction_type == "ADJ":
                self.item.quantity = self.quantity  # overwrite stock count

            self.item.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.item.name} ({self.quantity})"