from django.db import models
from orders.models import Order


class ProvisioningJob(models.Model):
    """Log of provisioning attempts — simulates a network provisioning system's job queue."""

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="provisioning_jobs")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    resource_identifier = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Provisioning job for order #{self.order_id} [{self.status}]"
