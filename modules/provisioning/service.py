"""
Simulated provisioning/activation (Section 4/7 - OSS layer).
On a laptop there's no real network element manager to call, so this
module stands in as the adapter: it generates a plausible network
identifier (MSISDN/circuit ID/IMSI-like value) and marks the product
instance + a new service instance active. In production this is where
NETCONF/SNMP/TR-069 adapters to real network elements would plug in,
behind the exact same function signature.
"""
import random
from core.event_bus import publish
from modules.inventory import service as inventory_service


def _generate_network_identifier(service_type: str) -> str:
    if service_type == "mobile_line":
        return f"91{random.randint(7000000000, 9999999999)}"
    if service_type == "broadband_line":
        return f"CKT-{random.randint(100000, 999999)}"
    if service_type == "iot_connection":
        return f"IMSI-{random.randint(100000000, 999999999)}"
    return f"ID-{random.randint(10000, 99999)}"


def provision_order_item(product_instance_id: int, offering_category: str) -> dict:
    service_type_map = {
        "Mobile": "mobile_line",
        "Broadband": "broadband_line",
        "IoT": "iot_connection",
    }
    service_type = service_type_map.get(offering_category, "generic_service")
    network_id = _generate_network_identifier(service_type)

    si = inventory_service.create_service_instance(
        product_instance_id=product_instance_id,
        service_type=service_type,
        network_identifier=network_id,
    )
    inventory_service.activate_product_instance(product_instance_id)

    result = {"product_instance_id": product_instance_id, **si}
    publish("service_provisioned", **result)
    return result
