from django.db import models
from orders.models import Order


class ActivationLog(models.Model):
    STATUS_CHOICES = [
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="activation_logs")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="SUCCESS")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Activation for order #{self.order_id} [{self.status}]"
