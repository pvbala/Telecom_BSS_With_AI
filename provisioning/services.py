from django.db import transaction
from resource_inventory.models import NetworkResource
from .models import ProvisioningJob


RESOURCE_TYPE_BY_PRODUCT = {
    "PREPAID_SIM": "MSISDN",
    "FIBER": "FIBER_PORT",
}


@transaction.atomic
def provision_order(order):
    """Reserve a free network resource for this order and move it to PROVISIONED."""
    if order.status != "VALIDATED":
        order.transition_to("VALIDATED") if order.status == "CREATED" else None

    resource_type = RESOURCE_TYPE_BY_PRODUCT[order.price_plan.product.product_type]
    resource = NetworkResource.objects.select_for_update().filter(
        resource_type=resource_type, status="FREE"
    ).first()

    if not resource:
        ProvisioningJob.objects.create(order=order, status="FAILED", notes="No free resource available")
        order.transition_to("FAILED")
        raise ValueError("No free resource available to provision this order")

    resource.status = "RESERVED"
    resource.assigned_to_order = order
    resource.save(update_fields=["status", "assigned_to_order", "updated_at"])

    ProvisioningJob.objects.create(
        order=order, status="SUCCESS", resource_identifier=resource.identifier
    )
    order.transition_to("PROVISIONED")
    return resource
