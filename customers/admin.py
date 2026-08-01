from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(ImportExportModelAdmin):
    list_display = ("name", "phone", "email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "phone", "email")
