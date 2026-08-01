from django.db import models
from service_inventory.models import Service


class UsageRecord(models.Model):
    """Synthetic CDR-like usage record. For prepaid: deducts balance. For fiber: just logged."""

    USAGE_TYPES = [
        ("VOICE", "Voice call"),
        ("DATA", "Data session"),
        ("SMS", "SMS"),
    ]

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="usage_records")
    usage_type = models.CharField(max_length=20, choices=USAGE_TYPES, default="DATA")
    data_mb = models.FloatField(default=0)
    duration_seconds = models.IntegerField(default=0)
    charge_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"{self.usage_type} usage for service #{self.service_id} at {self.recorded_at}"
