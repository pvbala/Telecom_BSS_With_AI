from django.db import models


class Customer(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("SUSPENDED", "Suspended"),
        ("CLOSED", "Closed"),
    ]

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    id_proof_type = models.CharField(max_length=50, blank=True, help_text="e.g. Aadhaar, Passport")
    id_proof_number = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"

    class Meta:
        ordering = ["-created_at"]
