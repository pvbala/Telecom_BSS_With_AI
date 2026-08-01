from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Product, PricePlan


class PricePlanInline(admin.TabularInline):
    model = PricePlan
    extra = 1


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    list_display = ("name", "product_type", "is_active")
    list_filter = ("product_type", "is_active")
    search_fields = ("name",)
    inlines = [PricePlanInline]


@admin.register(PricePlan)
class PricePlanAdmin(ImportExportModelAdmin):
    list_display = ("product", "name", "price", "is_active")
    list_filter = ("product__product_type", "is_active")
    search_fields = ("name", "product__name")
