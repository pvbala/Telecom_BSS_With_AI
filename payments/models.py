from django.db import models
from customers.models import Customer
from orders.models import Order
from billing.models import Invoice


class Payment(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]
    METHOD_CHOICES = [
        ("CARD", "Card"),
        ("UPI", "UPI"),
        ("NETBANKING", "Net banking"),
        ("WALLET", "Wallet"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="payments")
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="UPI")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} — ₹{self.amount} [{self.status}]"
