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

st.title("Telecom BSS/OSS Platform")
st.markdown("""
Welcome. Use the pages in the left sidebar:

- **Settings** — enter your Gemini / Grok API keys (Ollama is used automatically as the local fallback)
- **Test Data Generator** — describe a business process in plain English (or YAML) and run it against the real platform
- **AI Insights** — view/run churn prediction, anomaly detection, and revenue leakage
- **CRM** — retention cases raised by the churn model
- **NOC / Assurance** — alarms and trouble tickets
- **Manage Entities** — create/manage records directly, including Resource Inventory

All test data generation is **additive** — it always adds new customers/orders/records on top of whatever already exists; nothing is ever wiped.
""")

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

st.subheader("Overview")
row1 = st.columns(3)
row1[0].metric("Customers", len(customers))
row1[1].metric("Orders", len(orders))
row1[2].metric("Invoices", len(invoices))

row2 = st.columns(4)
row2[0].metric("Active Products", active_products)
row2[1].metric("Open Invoices (pending payment)", open_invoices)
row2[2].metric("Open Orders", open_orders)
row2[3].metric("Closed Orders (fulfilled)", closed_orders)

row3 = st.columns(1)
row3[0].metric("Resource Inventory Available", resources_available)
st.caption("Total unallocated MSISDNs, circuit IDs, and IMSIs across all pools — "
           "see the 'Resource Inventory' tab in Manage Entities for the breakdown by type.")