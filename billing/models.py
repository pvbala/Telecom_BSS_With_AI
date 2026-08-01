from django.db import models
from customers.models import Customer
from orders.models import Order


class Balance(models.Model):
    """Prepaid wallet balance per customer+order (one SIM = one wallet)."""

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="balance")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="balances")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    data_remaining_gb = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Balance for order #{self.order_id}: ₹{self.amount}, {self.data_remaining_gb:.2f}GB left"


class LedgerEntry(models.Model):
    ENTRY_TYPES = [
        ("TOPUP", "Top-up / recharge"),
        ("USAGE_DEDUCTION", "Usage deduction"),
        ("REFUND", "Refund"),
    ]

    balance = models.ForeignKey(Balance, on_delete=models.CASCADE, related_name="entries")
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.entry_type} ₹{self.amount} on balance #{self.balance_id}"


class Invoice(models.Model):
    """Monthly invoice — used for fiber broadband."""

    STATUS_CHOICES = [
        ("DUE", "Due"),
        ("PAID", "Paid"),
        ("OVERDUE", "Overdue"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="invoices")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="invoices")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DUE")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice #{self.id} — {self.customer.name} — ₹{self.amount} [{self.status}]"
