from django.contrib import admin
from .models import Fault


@admin.register(Fault)
class FaultAdmin(admin.ModelAdmin):
    list_display = ("resource", "severity", "status", "description", "detected_at")
    list_filter = ("severity", "status")
