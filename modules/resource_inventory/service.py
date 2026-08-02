"""
Resource Inventory: a finite pool of network resources (MSISDNs, circuit
IDs, IMSIs) that provisioning allocates from - this is what makes
"how many resources are available for further use" a real, answerable
question, rather than provisioning just generating a random identifier
out of thin air every time (which is what modules/provisioning/service.py
did before this module existed).
"""
import random
from sqlalchemy import func
from core.db import get_session
from core.event_bus import publish
from modules.resource_inventory.models import ResourceItem

RESOURCE_GENERATORS = {
    "MSISDN": lambda: f"91{random.randint(7000000000, 9999999999)}",
    "CIRCUIT_ID": lambda: f"CKT-{random.randint(100000, 999999)}",
    "IMSI": lambda: f"IMSI-{random.randint(100000000, 999999999)}",
}


def seed_resource_pool_if_empty(pool_size: int = 200):
    """
    Additive seed: only inserts a starting pool of resources if the table
    is currently empty (fresh DB). Never touches/removes anything that
    already exists - same additive pattern as the product catalog seed.
    """
    with get_session() as session:
        if session.query(ResourceItem).count() > 0:
            return

    for resource_type, generator in RESOURCE_GENERATORS.items():
        values = set()
        while len(values) < pool_size:
            values.add(generator())
        with get_session() as session:
            for value in values:
                session.add(ResourceItem(resource_type=resource_type, value=value, status="available"))


def allocate_resource(resource_type: str) -> dict | None:
    """
    Picks one AVAILABLE resource of the given type and marks it assigned.
    Returns None if the pool for that type is exhausted (caller decides
    the fallback - see modules/provisioning/service.py).
    """
    with get_session() as session:
        item = (session.query(ResourceItem)
                .filter(ResourceItem.resource_type == resource_type, ResourceItem.status == "available")
                .first())
        if not item:
            return None
        item.status = "assigned"
        session.flush()
        result = {"resource_id": item.id, "resource_type": resource_type, "value": item.value}
    publish("resource_allocated", **result)
    return result


def link_resource_to_service(resource_id: int, service_instance_id: int):
    """Called once the ServiceInstance exists, to record which service a resource is assigned to."""
    with get_session() as session:
        item = session.query(ResourceItem).get(resource_id)
        if item:
            item.assigned_service_instance_id = service_instance_id
            session.flush()


def release_resource(resource_id: int) -> dict:
    """Returns a resource to the available pool (e.g. when a service is terminated)."""
    with get_session() as session:
        item = session.query(ResourceItem).get(resource_id)
        if not item:
            raise ValueError(f"Resource {resource_id} not found")
        item.status = "available"
        item.assigned_service_instance_id = None
        session.flush()
        result = {"resource_id": resource_id, "status": "available"}
    publish("resource_released", **result)
    return result


def summary() -> list[dict]:
    """Available/assigned/total counts per resource type - the core 'how many left' answer."""
    with get_session() as session:
        rows = (session.query(ResourceItem.resource_type, ResourceItem.status, func.count(ResourceItem.id))
                .group_by(ResourceItem.resource_type, ResourceItem.status).all())
    counts: dict[str, dict[str, int]] = {}
    for resource_type, status, count in rows:
        counts.setdefault(resource_type, {"available": 0, "assigned": 0})
        counts[resource_type][status] = count
    return [
        {"resource_type": rt, "available": c["available"], "assigned": c["assigned"],
         "total": c["available"] + c["assigned"]}
        for rt, c in counts.items()
    ]


def total_available() -> int:
    with get_session() as session:
        return session.query(ResourceItem).filter(ResourceItem.status == "available").count()


def add_more_resources(resource_type: str, count: int = 100) -> dict:
    """Manually top up the pool for a given resource type (e.g. from Manage Entities)."""
    if resource_type not in RESOURCE_GENERATORS:
        raise ValueError(f"Unknown resource_type: {resource_type}")
    generator = RESOURCE_GENERATORS[resource_type]
    values = set()
    while len(values) < count:
        values.add(generator())
    with get_session() as session:
        for value in values:
            session.add(ResourceItem(resource_type=resource_type, value=value, status="available"))
    return {"resource_type": resource_type, "added": count}