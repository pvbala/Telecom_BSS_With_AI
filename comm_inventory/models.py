from django.db import models
from catalog.models import Product


class StockItem(models.Model):
    """Physical/commercial stock — SIM card batches, ONT device stock, etc."""

    ITEM_TYPES = [
        ("SIM_CARD", "SIM card"),
        ("ONT_DEVICE", "ONT / fiber device"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_items")
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    batch_reference = models.CharField(max_length=50, blank=True)
    quantity_on_hand = models.IntegerField(default=0)
    quantity_reserved = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_item_type_display()} — {self.product.name} ({self.quantity_on_hand} in stock)"

    @property
    def quantity_available(self):
        return self.quantity_on_hand - self.quantity_reserved
