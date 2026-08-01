from django.db import models


class Product(models.Model):
    PRODUCT_TYPES = [
        ("PREPAID_SIM", "Mobile Prepaid SIM"),
        ("FIBER", "Home Fiber Broadband"),
    ]

    name = models.CharField(max_length=100)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PricePlan(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="plans")
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # Prepaid SIM specific
    validity_days = models.IntegerField(null=True, blank=True, help_text="Prepaid: pack validity")
    data_per_day_gb = models.FloatField(null=True, blank=True, help_text="Prepaid: daily data allowance")
    voice_minutes = models.IntegerField(null=True, blank=True, help_text="Prepaid: voice minutes included")

    # Fiber specific
    speed_mbps = models.IntegerField(null=True, blank=True, help_text="Fiber: download speed")
    monthly_data_cap_gb = models.IntegerField(null=True, blank=True, help_text="Fiber: FUP data cap, blank=unlimited")

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.name} — {self.name} (₹{self.price})"
