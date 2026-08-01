"""Simulated fault generation — occasionally raises a fault on an assigned resource,
and auto-opens a trouble ticket for the affected customer.
"""
import random
from resource_inventory.models import NetworkResource
from tickets.models import Ticket
from .models import Fault

FAULT_DESCRIPTIONS = {
    "MSISDN": ["Network registration failure", "Signal degradation", "SIM authentication error"],
    "FIBER_PORT": ["ONT link down", "High packet loss", "Port power fluctuation"],
}


def maybe_raise_random_fault(probability: float = 0.3):
    """Called periodically; with given probability, raises one fault on a random assigned resource."""
    if random.random() > probability:
        return None

    resource = NetworkResource.objects.filter(status="ASSIGNED").order_by("?").first()
    if not resource:
        return None

    severity = random.choices(["MINOR", "MAJOR", "CRITICAL"], weights=[0.6, 0.3, 0.1])[0]
    description = random.choice(FAULT_DESCRIPTIONS.get(resource.resource_type, ["Unknown fault"]))

    fault = Fault.objects.create(resource=resource, severity=severity, description=description)

    order = resource.assigned_to_order
    if order and severity in ("MAJOR", "CRITICAL"):
        Ticket.objects.create(
            customer=order.customer,
            service=getattr(order, "service", None),
            subject=f"Auto-detected fault: {description}",
            description=f"System detected a {severity} fault on {resource.identifier}.",
            priority="HIGH" if severity == "MAJOR" else "CRITICAL",
            status="OPEN",
        )
    return fault
