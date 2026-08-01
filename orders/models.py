from django.db import models
from django.utils import timezone
from customers.models import Customer
from catalog.models import PricePlan


class Order(models.Model):
    STATUS_CHOICES = [
        ("CREATED", "Created"),
        ("VALIDATED", "Validated"),
        ("PROVISIONED", "Provisioned"),
        ("ACTIVE", "Active"),
        ("FAILED", "Failed"),
        ("COMPLETED", "Completed"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders")
    price_plan = models.ForeignKey(PricePlan, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="CREATED")
    installation_address = models.TextField(blank=True, help_text="Used for fiber orders")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} — {self.customer.name} — {self.price_plan.name} [{self.status}]"

    class Meta:
        ordering = ["-created_at"]

    # --- simple state machine -------------------------------------------------
    ALLOWED_TRANSITIONS = {
        "CREATED": {"VALIDATED", "FAILED"},
        "VALIDATED": {"PROVISIONED", "FAILED"},
        "PROVISIONED": {"ACTIVE", "FAILED"},
        "ACTIVE": {"COMPLETED"},
        "FAILED": set(),
        "COMPLETED": set(),
    }

    def transition_to(self, new_status):
        if new_status not in self.ALLOWED_TRANSITIONS.get(self.status, set()):
            raise ValueError(f"Cannot move order from {self.status} to {new_status}")
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])
        OrderStatusHistory.objects.create(order=self, status=new_status, changed_at=timezone.now())
        return self


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="history")
    status = models.CharField(max_length=20)
    changed_at = models.DateTimeField()

    class Meta:
        ordering = ["changed_at"]

    def __str__(self):
        return f"Order #{self.order_id} -> {self.status} @ {self.changed_at}"
