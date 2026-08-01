from django.contrib import admin
from .models import UsageRecord


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ("service", "usage_type", "data_mb", "duration_seconds", "charge_amount", "recorded_at")
    list_filter = ("usage_type",)
