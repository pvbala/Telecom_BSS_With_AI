from django.contrib import admin
from .models import Payment
from .services import process_payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "order", "invoice", "amount", "method", "status", "created_at")
    list_filter = ("status", "method")
    search_fields = ("customer__name",)
    actions = ["mark_success", "mark_failed"]

    @admin.action(description="Simulate gateway: mark SUCCESS")
    def mark_success(self, request, queryset):
        for payment in queryset:
            process_payment(payment, simulate_failure=False)

    @admin.action(description="Simulate gateway: mark FAILED")
    def mark_failed(self, request, queryset):
        for payment in queryset:
            process_payment(payment, simulate_failure=True)
