import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from modules.party.service import list_customers
from modules.order.service import list_orders
from modules.billing.service import list_invoices
from modules.crm.service import list_retention_cases

st.title("👥 CRM")

tab1, tab2, tab3 = st.tabs(["Customers", "Orders & Invoices", "Retention Cases (from Churn AI)"])

with tab1:
    st.dataframe(list_customers(limit=500), use_container_width=True)

with tab2:
    st.write("Orders")
    st.dataframe(list_orders(limit=500), use_container_width=True)
    st.write("Invoices")
    st.dataframe(list_invoices(), use_container_width=True)

with tab3:
    st.caption("Auto-created when the Churn Prediction model flags a customer above threshold.")
    st.dataframe(list_retention_cases(), use_container_width=True)
