from django.contrib import admin
from .models import ProvisioningJob


@admin.register(ProvisioningJob)
class ProvisioningJobAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "resource_identifier", "created_at")
    list_filter = ("status",)
