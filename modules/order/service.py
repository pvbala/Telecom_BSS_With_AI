from core.db import get_session, next_sequence_number
from core.event_bus import publish
from modules.order.models import Order, OrderItem
from modules.catalog import service as catalog_service


def place_order(customer_id: int, account_id: int, items: list[dict], channel: str = "online") -> dict:
    """
    items: [{"offering_id": int, "attributes": {...}}, ...]
    Validates each item's attributes against its ProductSpecification schema
    (Section 2 flexible product model) before accepting the order.
    """
    validated_items = []
    for item in items:
        offering = catalog_service.get_offering_by_name(item["offering_name"]) \
            if "offering_name" in item else None
        offering_id = item.get("offering_id") or (offering["id"] if offering else None)
        if offering_id is None:
            raise ValueError("Order item must reference offering_id or offering_name")

        with get_session() as session:
            from modules.catalog.models import ProductOffering
            off = session.query(ProductOffering).get(offering_id)
            spec_id = off.spec_id
            price = off.price

        attrs = item.get("attributes", {})
        catalog_service.validate_attributes(spec_id, attrs)
        validated_items.append({"offering_id": offering_id, "attributes": attrs, "price": price})

    with get_session() as session:
        seq = next_sequence_number(session, Order, "code")
        order = Order(code=f"ORD-{seq:04d}", customer_id=customer_id, account_id=account_id,
                       channel=channel, status="CREATED")
        session.add(order)
        session.flush()

        for it in validated_items:
            oi = OrderItem(order_id=order.id, offering_id=it["offering_id"],
                            attributes=it["attributes"], price=it["price"])
            session.add(oi)
        session.flush()

        result = {"order_id": order.id, "order_code": order.code, "status": order.status,
                  "item_count": len(validated_items)}

    publish("order_placed", **result, customer_id=customer_id, account_id=account_id)
    return result


def update_order_status(order_id: int, status: str):
    with get_session() as session:
        order = session.query(Order).get(order_id)
        order.status = status
        session.flush()
    publish("order_status_changed", order_id=order_id, status=status)


def get_order(order_id: int) -> dict | None:
    with get_session() as session:
        order = session.query(Order).get(order_id)
        if not order:
            return None
        items = session.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        return {
            "id": order.id, "code": order.code, "status": order.status,
            "customer_id": order.customer_id, "account_id": order.account_id,
            "items": [{"offering_id": i.offering_id, "attributes": i.attributes, "price": i.price}
                      for i in items],
        }


def list_orders(limit: int = 100) -> list[dict]:
    with get_session() as session:
        rows = session.query(Order).order_by(Order.id.desc()).limit(limit).all()
        return [{"id": o.id, "code": o.code, "status": o.status, "customer_id": o.customer_id,
                  "account_id": o.account_id} for o in rows]


def provision_order(order_id: int) -> dict:
    """
    Drives an order through OSS activation: creates a Product Instance and
    Service Instance for each order item, then marks the order ACTIVE.
    This is the single shared implementation used both by the Test Data
    Engine's 'provision_service' step AND the manual 'Provision Order'
    screen, so there is exactly one code path for this business process
    regardless of who/what triggers it.
    """
    from modules.catalog import service as catalog_service
    from modules.catalog.models import ProductSpecification
    from modules.inventory import service as inventory_service
    from modules.provisioning import service as provisioning_service
    from core.db import get_session as _get_session

    order = get_order(order_id)
    if not order:
        raise ValueError(f"Order {order_id} not found")
    if order["status"] == "ACTIVE":
        raise ValueError(f"Order {order_id} is already provisioned/active")

    created_instances = []
    for item in order["items"]:
        offerings = catalog_service.list_offerings()
        off = next((o for o in offerings if o["id"] == item["offering_id"]), None)
        spec_id = off["spec_id"] if off else None
        category = "Mobile"
        if spec_id is not None:
            with _get_session() as session:
                spec = session.query(ProductSpecification).get(spec_id)
                category = spec.category if spec else "Mobile"

        pi = inventory_service.create_product_instance(
            customer_id=order["customer_id"], order_id=order["id"],
            offering_id=item["offering_id"], attributes=item["attributes"],
        )
        provisioning_service.provision_order_item(
            product_instance_id=pi["product_instance_id"], offering_category=category,
        )
        created_instances.append({
            **pi, "customer_id": order["customer_id"], "offering_category": category,
        })

    update_order_status(order_id, "ACTIVE")
    return {"order_id": order_id, "product_instances": created_instances}