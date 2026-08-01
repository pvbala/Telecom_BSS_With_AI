from django.contrib import admin
from .models import Balance, LedgerEntry, Invoice


class LedgerEntryInline(admin.TabularInline):
    model = LedgerEntry
    extra = 0
    readonly_fields = ("entry_type", "amount", "description", "created_at")
    can_delete = False


@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ("order", "customer", "amount", "data_remaining_gb", "updated_at")
    search_fields = ("customer__name",)
    inlines = [LedgerEntryInline]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "order", "amount", "status", "billing_period_start", "billing_period_end")
    list_filter = ("status",)
    search_fields = ("customer__name",)
