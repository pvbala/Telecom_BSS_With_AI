from core.db import get_session, next_sequence_number
from core.event_bus import publish
from modules.inventory.models import ProductInstance, ServiceInstance


def create_product_instance(customer_id: int, order_id: int, offering_id: int, attributes: dict) -> dict:
    with get_session() as session:
        seq = next_sequence_number(session, ProductInstance, "code")
        pi = ProductInstance(code=f"PI-{seq:04d}", customer_id=customer_id, order_id=order_id,
                              offering_id=offering_id, attributes=attributes, status="pending")
        session.add(pi)
        session.flush()
        result = {"product_instance_id": pi.id, "code": pi.code}
    publish("product_instance_created", **result, customer_id=customer_id)
    return result


def activate_product_instance(product_instance_id: int) -> dict:
    with get_session() as session:
        pi = session.query(ProductInstance).get(product_instance_id)
        pi.status = "active"
        session.flush()
        result = {"product_instance_id": pi.id, "status": pi.status}
    publish("product_instance_activated", **result)
    return result


def create_service_instance(product_instance_id: int, service_type: str, network_identifier: str) -> dict:
    with get_session() as session:
        seq = next_sequence_number(session, ServiceInstance, "code")
        si = ServiceInstance(code=f"SVC-{seq:04d}", product_instance_id=product_instance_id,
                              service_type=service_type, network_identifier=network_identifier,
                              status="active")
        session.add(si)
        session.flush()
        result = {"service_instance_id": si.id, "code": si.code, "network_identifier": network_identifier}
    publish("service_instance_created", **result)
    return result


def list_product_instances(customer_id: int | None = None) -> list[dict]:
    with get_session() as session:
        q = session.query(ProductInstance)
        if customer_id:
            q = q.filter(ProductInstance.customer_id == customer_id)
        rows = q.all()
        return [{"id": p.id, "code": p.code, "status": p.status, "customer_id": p.customer_id,
                  "offering_id": p.offering_id, "attributes": p.attributes} for p in rows]
