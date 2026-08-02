import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from ai_ml.serve import score, revenue_leakage_diagnostics
from ai_ml.train import train
from ai_ml.model_registry import get_latest_model
from modules.party import service as party_service
from modules.assurance import service as assurance_service
from modules.billing import service as billing_service
from modules.crm import service as crm_service
from dashboard.session_keys import get_session_keys

st.set_page_config(page_title="AI Insights", layout="wide")
st.title("AI Predictions")

if "expanded" not in st.session_state:
    st.session_state.expanded = {}


def toggle(key: str):
    st.session_state.expanded[key] = not st.session_state.expanded.get(key, False)


# ---------------------------------------------------------------------
# Gather live scores once per page load
# ---------------------------------------------------------------------
churn_results = score("churn_prediction")
anomaly_results = score("anomaly_detection")
leakage_results = score("revenue_leakage")

high_risk_churn = sorted([r for r in churn_results if r["score"] >= 0.7],
                          key=lambda r: -r["score"])
critical_anomalies = sorted([r for r in anomaly_results if r["is_anomaly"]],
                             key=lambda r: -r["score"])
leakage_flags = sorted(leakage_results, key=lambda r: -r["discrepancy_amount"])

churn_model = get_latest_model("churn_prediction")
anomaly_model = get_latest_model("anomaly_detection")
last_trained_dates = [m["trained_at"] for m in [churn_model, anomaly_model] if m]
last_trained = max(last_trained_dates)[:10] if last_trained_dates else "Not trained yet"

# ---------------------------------------------------------------------
# KPI strip
# ---------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Customers at risk", len(high_risk_churn))
k2.metric("Critical anomalies", len(critical_anomalies))
k3.metric("Revenue leakage", f"Rs {sum(r['discrepancy_amount'] for r in leakage_flags):,.0f}")
k4.metric("Models last trained", last_trained)

st.divider()

# ---------------------------------------------------------------------
# Needs attention today - unified priority list across all 3 use cases
# ---------------------------------------------------------------------
st.subheader("Needs attention today")

attention_items = (
    [("churn", r) for r in high_risk_churn[:3]]
    + [("anomaly", r) for r in critical_anomalies[:3]]
    + [("leakage", r) for r in leakage_flags[:3]]
)

if not attention_items:
    st.success("Nothing urgent right now - no high-risk customers, critical anomalies, "
               "or revenue leakage detected.")

for kind, item in attention_items:
    with st.container(border=True):
        if kind == "churn":
            key = f"churn_{item['customer_id']}"
            c1, c2, c3 = st.columns([5, 1, 2])
            c1.markdown(f"**Customer {item['customer_id']}** (churn risk) - {item['reason']}")
            c2.markdown(f"`Churn {item['score']}`")
            b1, b2 = c3.columns(2)
            if b1.button("Details", key=f"btn_details_{key}"):
                toggle(key)
            if b2.button("Retain", key=f"btn_action_{key}", type="primary"):
                result = crm_service.create_retention_case(
                    customer_id=item["customer_id"], churn_score=item["score"], reason=item["reason"])
                st.success(f"Retention case {result['code']} created.")

            if st.session_state.expanded.get(key):
                customer = party_service.get_customer(item["customer_id"])
                account = party_service.get_account_for_customer(item["customer_id"])
                tickets = assurance_service.list_tickets(customer_id=item["customer_id"])
                invoices = billing_service.list_invoices(account["id"]) if account else []
                st.markdown(f"**{customer['name']}** ({customer['code']}) - {customer['email'] or 'no email'}")
                d1, d2 = st.columns(2)
                d1.write("Tickets")
                d1.dataframe(tickets, use_container_width=True)
                d2.write("Invoices")
                d2.dataframe(invoices, use_container_width=True)

        elif kind == "anomaly":
            key = f"anomaly_{item['alarm_id']}"
            c1, c2, c3 = st.columns([5, 1, 2])
            c1.markdown(f"**Alarm {item['alarm_id']}** (anomaly) - {item['alarm_type']}")
            c2.markdown(f"`Score {item['score']}`")
            b1, b2 = c3.columns(2)
            if b1.button("Details", key=f"btn_details_{key}"):
                toggle(key)
            if b2.button("Explain", key=f"btn_action_{key}", type="primary"):
                try:
                    from llm.troubleshoot_narrator import narrate_anomaly
                    gemini_key, grok_key = get_session_keys()
                    related = assurance_service.list_alarms(alarm_type=item["alarm_type"])
                    narrative = narrate_anomaly(item, related, gemini_key=gemini_key, grok_key=grok_key)
                    st.info(narrative)
                except Exception as e:
                    st.error(f"Could not generate explanation: {e}")

            if st.session_state.expanded.get(key):
                related = assurance_service.list_alarms(alarm_type=item["alarm_type"])
                st.write(f"Other alarms of type '{item['alarm_type']}':")
                st.dataframe(related, use_container_width=True)

        else:  # leakage
            key = f"leakage_{item['product_instance_id']}"
            c1, c2, c3 = st.columns([5, 1, 2])
            c1.markdown(f"**Product instance {item['product_instance_id']}** (leakage) - "
                        f"customer {item['customer_id']}, usage never invoiced")
            c2.markdown(f"`Rs {item['discrepancy_amount']:,.0f}`")
            b1, b2 = c3.columns(2)
            if b1.button("Details", key=f"btn_details_{key}"):
                toggle(key)
            if b2.button("Raise invoice", key=f"btn_action_{key}", type="primary"):
                account = party_service.get_account_for_customer(item["customer_id"])
                if account:
                    result = billing_service.raise_invoice_for_account(account["id"])
                    st.success(f"Invoice {result['invoice_code']} raised for Rs {result['amount']}.")

            if st.session_state.expanded.get(key):
                st.write(f"Rated usage: Rs {item['rated_total']:,.2f} - "
                         f"Invoiced so far: Rs {item['invoiced_total']:,.2f}")

st.divider()

# ---------------------------------------------------------------------
# All predictions - compact status rows, each expandable to the full list
# ---------------------------------------------------------------------
st.subheader("All predictions")

with st.container(border=True):
    c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
    c1.markdown("**Churn prediction & retention**")
    c2.caption(f"{len(churn_results)} customers scored")
    c3.markdown(f"{len(high_risk_churn)} high risk" if high_risk_churn else "none flagged")
    show_churn_table = c4.button("Expand", key="expand_churn")
    tcol1, tcol2 = st.columns([1, 3])
    if tcol1.button("Train model", key="train_churn"):
        with st.spinner("Training..."):
            result = train("churn_prediction")
        st.success(f"Trained v{result['version']}") if result else st.warning("Not enough data yet.")
    if show_churn_table:
        st.dataframe(churn_results, use_container_width=True)

with st.container(border=True):
    c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
    c1.markdown("**Anomaly detection & troubleshooting**")
    c2.caption(f"{len(anomaly_results)} alarms scored - live, event-driven")
    c3.markdown(f"{len(critical_anomalies)} critical" if critical_anomalies else "none flagged")
    show_anomaly_table = c4.button("Expand", key="expand_anomaly")
    if st.button("Train model", key="train_anomaly"):
        with st.spinner("Training..."):
            result = train("anomaly_detection")
        st.success(f"Trained v{result['version']}") if result else st.warning("Not enough data yet.")
    if show_anomaly_table:
        st.dataframe(anomaly_results, use_container_width=True)

with st.container(border=True):
    c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
    c1.markdown("**Revenue assurance / leakage detection**")
    c2.caption("Rule-based reconciliation - no training needed")
    if leakage_flags:
        c3.markdown(f"Rs {sum(r['discrepancy_amount'] for r in leakage_flags):,.0f} leaking")
    else:
        diag = revenue_leakage_diagnostics()
        c3.markdown("all invoiced" if diag["has_enough_data"] else "no data yet")
    show_leakage_table = c4.button("Expand", key="expand_leakage")
    if show_leakage_table:
        st.dataframe(leakage_results, use_container_width=True)

st.divider()
st.subheader("Look up a specific entity")
lookup_uc = st.selectbox("Use case", ["churn_prediction", "anomaly_detection", "revenue_leakage"])
entity_id = st.number_input("Entity ID (customer_id / alarm_id / product_instance_id)", min_value=1, step=1)
if st.button("Score this entity"):
    result = score(lookup_uc, entity_id=int(entity_id))
    st.json(result)