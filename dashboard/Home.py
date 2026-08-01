import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.db import init_db
from modules.catalog.service import seed_default_catalog_if_empty

st.set_page_config(page_title="Telecom BSS/OSS Platform", layout="wide")

init_db()
seed_default_catalog_if_empty()

st.title("📡 Telecom BSS/OSS Platform")
st.markdown("""
Welcome. Use the pages in the left sidebar:

- **Settings** — enter your Gemini / Grok API keys (Ollama is used automatically as the local fallback)
- **Test Data Generator** — describe a business process in plain English (or YAML) and run it against the real platform
- **AI Insights** — view/run churn prediction, anomaly detection, and revenue leakage
- **CRM** — retention cases raised by the churn model
- **NOC / Assurance** — alarms and trouble tickets

All test data generation is **additive** — it always adds new customers/orders/records on top of whatever already exists; nothing is ever wiped.
""")

from modules.party.service import list_customers
from modules.order.service import list_orders
from modules.billing.service import list_invoices

col1, col2, col3 = st.columns(3)
col1.metric("Customers", len(list_customers(limit=100000)))
col2.metric("Orders", len(list_orders(limit=100000)))
col3.metric("Invoices", len(list_invoices()))
