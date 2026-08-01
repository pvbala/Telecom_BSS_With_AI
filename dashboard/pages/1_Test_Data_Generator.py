import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import yaml

from test_data_engine.nl_spec_translator import translate
from test_data_engine.spec_parser import parse_spec, summarize_plan, SpecValidationError
from test_data_engine.orchestrator import run_scenario

st.title("🧪 Test Data Generator")
st.caption("Data is always ADDED to what already exists — nothing is ever overwritten.")

mode = st.radio("Input mode", ["Plain English", "YAML / Structured"], horizontal=True)

if "draft_yaml" not in st.session_state:
    st.session_state.draft_yaml = ""

if mode == "Plain English":
    nl_text = st.text_area(
        "Describe the business process test case",
        placeholder="Create 5 Customers, Put 2 Orders for each of these 5 customers, "
                    "provision the service, raise the invoice.",
        height=100,
    )
    if st.button("Translate to spec"):
        with st.spinner("Asking the LLM to draft a spec..."):
            result = translate(nl_text)
        if "error" in result:
            st.error(result["error"])
            st.code(result.get("raw_yaml", ""), language="yaml")
        else:
            st.session_state.draft_yaml = result["yaml"]
            st.success(f"Draft generated using provider: {result['provider_used']}")

st.subheader("Review / edit the spec before running")
st.session_state.draft_yaml = st.text_area(
    "YAML spec", value=st.session_state.draft_yaml, height=300,
)

col1, col2 = st.columns(2)

with col1:
    if st.button("Validate"):
        try:
            spec = parse_spec(st.session_state.draft_yaml, is_path=False)
            st.success("Spec is valid.")
            st.text(summarize_plan(spec))
        except SpecValidationError as e:
            st.error(str(e))

with col2:
    if st.button("▶ Run scenario", type="primary"):
        try:
            with st.spinner("Running business process against the live platform..."):
                result = run_scenario(spec_text=st.session_state.draft_yaml)
            st.success(f"Scenario '{result['scenario']}' completed.")
            for line in result["log"]:
                st.write("✅", line)
            with st.expander("Run manifest (entity IDs created)"):
                st.json(result)
        except Exception as e:
            st.error(f"Run failed: {e}")

st.divider()
st.subheader("Saved scenarios (scenario_library/)")
lib_dir = Path(__file__).resolve().parent.parent.parent / "test_data_engine" / "scenario_library"
for f in sorted(lib_dir.glob("*.yaml")):
    with st.expander(f.name):
        content = f.read_text()
        st.code(content, language="yaml")
        if st.button(f"Load '{f.name}' into editor", key=f"load_{f.name}"):
            st.session_state.draft_yaml = content
            st.rerun()

if st.session_state.draft_yaml:
    new_name = st.text_input("Save current spec as (filename, no extension)")
    if st.button("💾 Save to scenario library") and new_name:
        out_path = lib_dir / f"{new_name}.yaml"
        out_path.write_text(st.session_state.draft_yaml)
        st.success(f"Saved to {out_path}")
