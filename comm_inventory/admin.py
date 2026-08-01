from django.contrib import admin
from .models import StockItem


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ("product", "item_type", "batch_reference", "quantity_on_hand", "quantity_reserved", "quantity_available")
    list_filter = ("item_type", "product")
