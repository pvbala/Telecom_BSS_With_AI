"""
Executes a parsed Business Process Test Case spec by calling the REAL
module service functions (party, catalog, order, provisioning, inventory,
mediation_rating, billing) - exactly as a human/operator would drive the
platform. This guarantees:
  1. Data is consistent across every subsystem (an invoice always ties
     back to a real order and real usage).
  2. Every run is ADDITIVE: it only ever creates new rows on top of
     whatever already exists (see core/db.py next_sequence_number and
     init_db - nothing here deletes or truncates existing data).
"""
import random
from test_data_engine.spec_parser import parse_spec
from test_data_engine import data_factory
from modules.party import service as party_service
from modules.catalog import service as catalog_service
from modules.order import service as order_service
from modules.inventory import service as inventory_service
from modules.provisioning import service as provisioning_service
from modules.mediation_rating import service as mediation_service
from modules.billing import service as billing_service
from modules.assurance import service as assurance_service


class RunManifest:
    """Captures every entity created in this run for traceability/results display."""
    def __init__(self):
        self.customers = []          # [{customer_id, account_id, ...}]
        self.orders = []             # [{order_id, customer_id, account_id, ...}]
        self.product_instances = []  # [{product_instance_id, customer_id, offering_category}]
        self.invoices = []           # [{invoice_id, account_id, customer_id, amount, status}]
        self.tickets = []            # [{ticket_id, customer_id, ...}]
        self.log = []

    def note(self, message: str):
        self.log.append(message)

    def as_dict(self):
        return {
            "customers_created": len(self.customers),
            "orders_created": len(self.orders),
            "product_instances_created": len(self.product_instances),
            "invoices_created": len(self.invoices),
            "tickets_created": len(self.tickets),
            "log": self.log,
            "customers": self.customers,
            "orders": self.orders,
            "product_instances": self.product_instances,
            "invoices": self.invoices,
            "tickets": self.tickets,
        }


def _step_create_customer(step: dict, manifest: RunManifest):
    count = step.get("count", 1)
    template = step.get("template", "individual_prepaid_customer")
    for _ in range(count):
        payload = data_factory.generate_customer_payload(template)
        result = party_service.create_customer(**payload)
        account = party_service.get_account_for_customer(result["customer_id"])
        entry = {**result, "account_id": account["id"]}
        manifest.customers.append(entry)
    manifest.note(f"Created {count} customer(s)")


def _resolve_offering(product: dict) -> dict:
    if "offering_name" in product:
        offering = catalog_service.get_offering_by_name(product["offering_name"])
        if not offering:
            raise ValueError(f"Unknown offering: {product['offering_name']}")
        return offering
    raise ValueError("Order product entry must specify 'offering_name'")


def _step_place_order(step: dict, manifest: RunManifest):
    count = step.get("count", 1)
    order_spec = step["order"]
    channel = order_spec.get("channel", "online")

    for customer in manifest.customers:
        for _ in range(count):
            items = []
            for product in order_spec["products"]:
                offering = _resolve_offering(product)
                items.append({
                    "offering_id": offering["id"],
                    "attributes": product.get("attributes", {}),
                })
            result = order_service.place_order(
                customer_id=customer["customer_id"],
                account_id=customer["account_id"],
                items=items,
                channel=channel,
            )
            manifest.orders.append({
                **result,
                "customer_id": customer["customer_id"],
                "account_id": customer["account_id"],
            })
    manifest.note(f"Placed {count} order(s) per customer for {len(manifest.customers)} customer(s)")


def _step_provision_service(step: dict, manifest: RunManifest):
    for order_entry in manifest.orders:
        order = order_service.get_order(order_entry["order_id"])
        for item in order["items"]:
            offering = catalog_service.list_offerings()
            off = next((o for o in offering if o["id"] == item["offering_id"]), None)
            spec_id = off["spec_id"] if off else None
            category = "Mobile"
            if spec_id is not None:
                from modules.catalog.models import ProductSpecification
                from core.db import get_session
                with get_session() as session:
                    spec = session.query(ProductSpecification).get(spec_id)
                    category = spec.category if spec else "Mobile"

            pi = inventory_service.create_product_instance(
                customer_id=order["customer_id"],
                order_id=order["id"],
                offering_id=item["offering_id"],
                attributes=item["attributes"],
            )
            provisioning_service.provision_order_item(
                product_instance_id=pi["product_instance_id"],
                offering_category=category,
            )
            manifest.product_instances.append({
                **pi, "customer_id": order["customer_id"], "offering_category": category,
            })
        order_service.update_order_status(order["id"], "ACTIVE")
    manifest.note(f"Provisioned {len(manifest.product_instances)} product instance(s)")


def _step_generate_usage(step: dict, manifest: RunManifest):
    profile = step.get("profile", "moderate_data_user")
    duration_days = step.get("duration_days", 30)
    for pi in manifest.product_instances:
        mediation_service.generate_usage(
            product_instance_id=pi["product_instance_id"],
            profile=profile,
            duration_days=duration_days,
        )
    manifest.note(f"Generated {duration_days}-day '{profile}' usage for "
                  f"{len(manifest.product_instances)} product instance(s)")


def _step_raise_invoice(step: dict, manifest: RunManifest):
    account_ids = {o["account_id"] for o in manifest.orders}
    for account_id in account_ids:
        customer_id = next(o["customer_id"] for o in manifest.orders if o["account_id"] == account_id)
        pi_ids = [pi["product_instance_id"] for pi in manifest.product_instances
                  if pi["customer_id"] == customer_id]
        total = sum(mediation_service.get_total_charges(pid) for pid in pi_ids)
        inv = billing_service.raise_invoice(account_id=account_id, amount=round(total, 2))
        manifest.invoices.append({**inv, "account_id": account_id, "customer_id": customer_id})
    manifest.note(f"Raised invoices for {len(account_ids)} account(s)")


def _step_raise_alarm(step: dict, manifest: RunManifest):
    count = step.get("count", 1)
    severities = step.get("severities", ["minor", "major", "critical"])
    alarm_types = step.get("alarm_types", ["link_down", "high_latency", "packet_loss"])
    for _ in range(count):
        assurance_service.raise_alarm(
            alarm_type=random.choice(alarm_types),
            severity=random.choice(severities),
            description="Synthetic alarm generated by test data engine",
        )
    manifest.note(f"Raised {count} alarm(s)")


def _step_create_ticket(step: dict, manifest: RunManifest):
    """
    Creates support tickets against customers created earlier in THIS run.
    This is what gives the Churn Prediction model's 'ticket_count' feature
    real variety to learn from - without this, every customer has 0 tickets.
    count = number of tickets PER customer (mirrors place_order's pattern).
    """
    count = step.get("count", 1)
    subjects = step.get("subjects", [
        "Billing query", "Slow internet speed", "Unable to make calls",
        "Data allowance exhausted early", "SIM activation issue",
    ])
    for customer in manifest.customers:
        for _ in range(count):
            subject = random.choice(subjects)
            ticket = assurance_service.create_ticket(
                subject=subject,
                description=f"Auto-generated test ticket: {subject}",
                customer_id=customer["customer_id"],
            )
            manifest.tickets.append({**ticket, "customer_id": customer["customer_id"]})
    manifest.note(f"Created {count} ticket(s) per customer for {len(manifest.customers)} customer(s)")


def _step_mark_invoice_overdue(step: dict, manifest: RunManifest):
    """
    Marks a fraction of the invoices raised earlier in THIS run as OVERDUE.
    This is what gives the Churn Prediction model's 'overdue_invoice_count'
    feature real variety to learn from - without this, every invoice stays
    ISSUED and that feature is always 0 for every customer.
    fraction: 0.0-1.0, portion of this run's invoices to mark overdue (default 1.0 = all)
    """
    fraction = step.get("fraction", 1.0)
    eligible = manifest.invoices
    num_to_mark = max(1, int(len(eligible) * fraction)) if eligible else 0
    chosen = random.sample(eligible, min(num_to_mark, len(eligible))) if eligible else []
    for inv in chosen:
        billing_service.update_invoice_status(inv["invoice_id"], "OVERDUE")
    manifest.note(f"Marked {len(chosen)} of {len(eligible)} invoice(s) from this run as OVERDUE")


STEP_HANDLERS = {
    "create_customer": _step_create_customer,
    "place_order": _step_place_order,
    "provision_service": _step_provision_service,
    "generate_usage": _step_generate_usage,
    "raise_invoice": _step_raise_invoice,
    "raise_alarm": _step_raise_alarm,
    "create_ticket": _step_create_ticket,
    "mark_invoice_overdue": _step_mark_invoice_overdue,
}


def run_scenario(spec_path: str = None, spec_text: str = None) -> dict:
    """Entry point used by the CLI, the FastAPI endpoint, and the Streamlit page."""
    if spec_path:
        spec = parse_spec(spec_path, is_path=True)
    elif spec_text:
        spec = parse_spec(spec_text, is_path=False)
    else:
        raise ValueError("Provide either spec_path or spec_text")

    manifest = RunManifest()
    for step in spec["steps"]:
        handler = STEP_HANDLERS[step["action"]]
        handler(step, manifest)

    return {"scenario": spec.get("scenario", "Unnamed scenario"), **manifest.as_dict()}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m test_data_engine.orchestrator <scenario.yaml>")
        sys.exit(1)
    result = run_scenario(spec_path=sys.argv[1])
    print(f"Scenario '{result['scenario']}' complete:")
    for line in result["log"]:
        print(" -", line)