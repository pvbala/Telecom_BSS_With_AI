from django.db import models
from customers.models import Customer
from orders.models import Order


class Service(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("ACTIVE", "Active"),
        ("SUSPENDED", "Suspended"),
        ("TERMINATED", "Terminated"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="services")
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="service")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    activated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Service for {self.customer.name} — {self.order.price_plan.product.name} [{self.status}]"
