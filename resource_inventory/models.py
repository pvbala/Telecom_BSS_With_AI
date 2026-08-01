from django.db import models


class NetworkResource(models.Model):
    """Logical/network resources — MSISDN pool for SIMs, port pool for fiber."""

    RESOURCE_TYPES = [
        ("MSISDN", "Mobile number (MSISDN)"),
        ("FIBER_PORT", "Fiber ONT port"),
    ]
    STATUS_CHOICES = [
        ("FREE", "Free"),
        ("RESERVED", "Reserved"),
        ("ASSIGNED", "Assigned"),
        ("FAULTY", "Faulty"),
    ]

    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    identifier = models.CharField(max_length=50, unique=True, help_text="MSISDN number or port ID, e.g. ONT-0234")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="FREE")
    assigned_to_order = models.ForeignKey(
        "orders.Order", null=True, blank=True, on_delete=models.SET_NULL, related_name="resources"
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.identifier} [{self.status}]"

    class Meta:
        ordering = ["resource_type", "identifier"]
