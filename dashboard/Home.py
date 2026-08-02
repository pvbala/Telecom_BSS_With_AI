import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.db import init_db
from modules.catalog.service import seed_default_catalog_if_empty
from modules.resource_inventory.service import seed_resource_pool_if_empty

st.set_page_config(page_title="Telecom BSS/OSS Platform", layout="wide")

init_db()
seed_default_catalog_if_empty()
seed_resource_pool_if_empty()

from modules.party.service import list_customers
from modules.order.service import list_orders
from modules.billing.service import list_invoices
from modules.inventory.service import list_product_instances
from modules.resource_inventory.service import total_available

customers = list_customers(limit=100000)
orders = list_orders(limit=100000)
invoices = list_invoices()
product_instances = list_product_instances()

active_products = len([p for p in product_instances if p["status"] == "active"])
open_invoices = len([i for i in invoices if i["status"] in ("ISSUED", "OVERDUE")])
open_orders = len([o for o in orders if o["status"] != "ACTIVE"])
closed_orders = len([o for o in orders if o["status"] == "ACTIVE"])
resources_available = total_available()

# tint: (background, text color) - amber only used when a number genuinely
# needs attention, green for a healthy resource pool, gray otherwise
TINTS = {
    "neutral": ("#F1EFE8", "#2C2C2A"),
    "warning": ("#FAEEDA", "#7A4F06"),
    "success": ("#EAF3DE", "#2F5A0F"),
}


def metric_card(icon: str, label: str, value, tint: str = "neutral"):
    bg, color = TINTS[tint]
    st.markdown(
        f"""<div style="background:{bg};border-radius:8px;padding:1rem;margin-bottom:0.5rem">
        <p style="font-size:13px;color:{color};margin:0 0 6px;opacity:0.85">{icon} {label}</p>
        <p style="font-size:24px;font-weight:600;margin:0;color:{color}">{value}</p>
        </div>""",
        unsafe_allow_html=True,
    )


st.title("Telecom BSS/OSS Platform")
st.caption("Live overview of customers, orders, billing, and network resources")

st.markdown("""
Use the pages in the left sidebar:

- **Settings** — enter your Gemini / Grok API keys (Ollama is used automatically as the local fallback)
- **Test Data Generator** — describe a business process in plain English (or YAML) and run it against the real platform
- **AI Insights** — view/run churn prediction, anomaly detection, and revenue leakage
- **CRM** — retention cases raised by the churn model
- **NOC / Assurance** — alarms and trouble tickets
- **Manage Entities** — create/manage records directly, including Resource Inventory and Invoice Payment

All test data generation is **additive** — it always adds new customers/orders/records on top of whatever already exists; nothing is ever wiped.
""")

st.divider()

st.subheader("Customers & orders")
c1, c2, c3 = st.columns(3)
with c1:
    metric_card("👥", "Customers", len(customers), "neutral")
with c2:
    metric_card("⏳", "Open orders", open_orders, "warning" if open_orders > 0 else "neutral")
with c3:
    metric_card("✅", "Closed orders", closed_orders, "neutral")

st.subheader("Billing")
b1, b2 = st.columns(2)
with b1:
    metric_card("🧾", "Invoices", len(invoices), "neutral")
with b2:
    metric_card("⚠️", "Pending payment", open_invoices, "warning" if open_invoices > 0 else "neutral")

st.subheader("Products & network")
p1, p2 = st.columns(2)
with p1:
    metric_card("📦", "Active products", active_products, "neutral")
with p2:
    metric_card("📡", "Resources available", resources_available,
                "warning" if resources_available < 20 else "success")