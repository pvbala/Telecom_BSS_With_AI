from django.contrib import admin
from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("customer", "order", "status", "activated_at")
    list_filter = ("status",)
    search_fields = ("customer__name",)
