from django.contrib import admin
from .models import Order, OrderStatusHistory


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("status", "changed_at")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "price_plan", "status", "created_at")
    list_filter = ("status", "price_plan__product")
    search_fields = ("customer__name", "customer__phone")
    inlines = [OrderStatusHistoryInline]
    actions = ["advance_to_validated", "advance_to_provisioned", "advance_to_active"]

    @admin.action(description="Advance selected orders: -> VALIDATED")
    def advance_to_validated(self, request, queryset):
        for order in queryset:
            try:
                order.transition_to("VALIDATED")
            except ValueError:
                pass

    @admin.action(description="Advance selected orders: -> PROVISIONED (assigns resource)")
    def advance_to_provisioned(self, request, queryset):
        from provisioning.services import provision_order
        for order in queryset:
            try:
                provision_order(order)
            except ValueError:
                pass

    @admin.action(description="Advance selected orders: -> ACTIVE (activates service)")
    def advance_to_active(self, request, queryset):
        from activation.services import activate_order
        for order in queryset:
            try:
                activate_order(order)
            except ValueError:
                pass
