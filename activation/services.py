from django.db import transaction
from django.utils import timezone
from service_inventory.models import Service
from .models import ActivationLog


@transaction.atomic
def activate_order(order):
    """Flip the reserved resource + service to ACTIVE, move order to ACTIVE."""
    if order.status != "PROVISIONED":
        raise ValueError("Order must be PROVISIONED before it can be activated")

    resource = order.resources.filter(status="RESERVED").first()
    if not resource:
        ActivationLog.objects.create(order=order, status="FAILED", notes="No reserved resource found")
        order.transition_to("FAILED")
        raise ValueError("No reserved resource found for this order")

    resource.status = "ASSIGNED"
    resource.save(update_fields=["status", "updated_at"])

    service, _ = Service.objects.get_or_create(order=order, defaults={"customer": order.customer})
    service.status = "ACTIVE"
    service.activated_at = timezone.now()
    service.save(update_fields=["status", "activated_at"])

    ActivationLog.objects.create(order=order, status="SUCCESS")
    order.transition_to("ACTIVE")
    return service
