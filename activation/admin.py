from django.contrib import admin
from .models import ActivationLog


@admin.register(ActivationLog)
class ActivationLogAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "created_at")
    list_filter = ("status",)
