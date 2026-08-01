from django.db import models
from resource_inventory.models import NetworkResource


class Fault(models.Model):
    SEVERITY_CHOICES = [
        ("MINOR", "Minor"),
        ("MAJOR", "Major"),
        ("CRITICAL", "Critical"),
    ]
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("ACKNOWLEDGED", "Acknowledged"),
        ("RESOLVED", "Resolved"),
    ]

    resource = models.ForeignKey(NetworkResource, on_delete=models.CASCADE, related_name="faults")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="MINOR")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="OPEN")
    description = models.CharField(max_length=255)
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-detected_at"]

    def __str__(self):
        return f"Fault on {self.resource.identifier} [{self.severity}/{self.status}]"
