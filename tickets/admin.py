from django.contrib import admin
from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "subject", "priority", "status", "created_at")
    list_filter = ("status", "priority")
    search_fields = ("customer__name", "subject")
