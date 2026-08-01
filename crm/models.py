from django.db import models
from customers.models import Customer


class Interaction(models.Model):
    CHANNEL_CHOICES = [
        ("CALL", "Call"),
        ("EMAIL", "Email"),
        ("CHAT", "Chat"),
        ("STORE_VISIT", "Store visit"),
        ("SYSTEM", "System-generated"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="interactions")
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default="CALL")
    summary = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.channel} with {self.customer.name}: {self.summary}"
