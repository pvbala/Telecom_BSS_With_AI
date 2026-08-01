from django.contrib import admin
from .models import NetworkResource


@admin.register(NetworkResource)
class NetworkResourceAdmin(admin.ModelAdmin):
    list_display = ("identifier", "resource_type", "status", "assigned_to_order", "updated_at")
    list_filter = ("resource_type", "status")
    search_fields = ("identifier",)
