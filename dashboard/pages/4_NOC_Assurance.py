import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from modules.assurance.service import list_alarms, list_tickets, raise_alarm
from ai_ml.serve import score_anomaly_detection
from llm.troubleshoot_narrator import narrate_anomaly
from llm.nl_query import ask as nl_ask

st.title("📶 NOC / Assurance")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Raise a test alarm")
    alarm_type = st.selectbox("Alarm type", ["link_down", "high_latency", "packet_loss", "hardware_fault"])
    severity = st.selectbox("Severity", ["minor", "major", "critical", "warning"])
    if st.button("Raise alarm"):
        result = raise_alarm(alarm_type=alarm_type, severity=severity,
                              description="Manually raised from NOC dashboard")
        st.success(f"Alarm {result['code']} raised — anomaly detector will react automatically.")

with col2:
    st.subheader("Recent alarms")
    st.dataframe(list_alarms(), use_container_width=True)

st.divider()
st.subheader("Anomaly Detection results")
if st.button("Run anomaly detection now"):
    results = score_anomaly_detection()
    st.dataframe(results, use_container_width=True)
    anomalies = [r for r in results if r["is_anomaly"]]
    if anomalies:
        top = anomalies[0]
        with st.spinner("Asking LLM for a root-cause narrative..."):
            narrative = narrate_anomaly(top, [r for r in results if r["alarm_type"] == top["alarm_type"]])
        st.info(narrative)

st.divider()
st.subheader("Trouble Tickets")
st.dataframe(list_tickets(), use_container_width=True)

st.divider()
st.subheader("Ask a question about your data (natural language → SQL)")
question = st.text_input("e.g. 'How many critical alarms were raised?'")
if st.button("Ask") and question:
    with st.spinner("Thinking..."):
        result = nl_ask(question)
    st.code(result.get("sql", ""), language="sql")
    if "error" in result:
        st.error(result["error"])
    else:
        st.dataframe(result["rows"], use_container_width=True)
