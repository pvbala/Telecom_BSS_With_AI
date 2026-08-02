import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from core.config import get_api_key, save_api_key, configured_providers

st.set_page_config(page_title="Settings", layout="wide")
st.title("Settings - LLM Providers")

st.markdown("""
This app can be used by **multiple people at once**. To keep your API key
private to you, keys entered below are stored **only in your own browser
session** - they are never written to a shared file and no other user of
this app can see or use them. Closing this browser tab clears your key;
you'll need to re-enter it next time.
""")

st.divider()
st.subheader("Your personal keys (private to this browser session)")

gemini_key = st.text_input(
    "Your Gemini API key", type="password",
    value=st.session_state.get("gemini_api_key", ""),
    help="Get one from https://aistudio.google.com/apikey",
)
if st.button("Use this Gemini key for my session"):
    st.session_state["gemini_api_key"] = gemini_key
    st.success("Saved to your session. Only you can use this key while this tab stays open.")

grok_key = st.text_input(
    "Your Grok (xAI) API key", type="password",
    value=st.session_state.get("grok_api_key", ""),
    help="Get one from https://console.x.ai",
)
if st.button("Use this Grok key for my session"):
    st.session_state["grok_api_key"] = grok_key
    st.success("Saved to your session. Only you can use this key while this tab stays open.")

if st.button("Clear my session keys"):
    st.session_state.pop("gemini_api_key", None)
    st.session_state.pop("grok_api_key", None)
    st.success("Your session keys have been cleared.")

st.subheader("Ollama (local fallback)")
st.info(
    "No key needed. Install Ollama (https://ollama.com), run `ollama pull llama3.1`, "
    "and it is used automatically whenever Gemini and Grok are unavailable, rate-limited, "
    "or no key has been entered for them."
)

st.subheader("Your session status")
st.json({
    "gemini_key_set_for_my_session": bool(st.session_state.get("gemini_api_key")),
    "grok_key_set_for_my_session": bool(st.session_state.get("grok_api_key")),
    "ollama": "always available (local, no key needed)",
})

st.divider()
with st.expander("Advanced: server-wide default key (admins / solo local use only)"):
    st.warning(
        "A server-wide default key is shared by EVERY user of this running app - "
        "not just you. Only set this if you are the sole user of this deployment, "
        "or you are deliberately provisioning a shared fallback key for your team. "
        "Most users should use the personal session keys above instead."
    )
    st.caption("Current server-wide defaults configured:")
    st.json(configured_providers())

    admin_gemini = st.text_input("Server-wide default Gemini key", type="password", key="admin_gemini")
    if st.button("Save as server-wide default Gemini key"):
        save_api_key("gemini", admin_gemini)
        st.success("Server-wide default Gemini key saved. This is now usable by ALL users of this app.")

    admin_grok = st.text_input("Server-wide default Grok key", type="password", key="admin_grok")
    if st.button("Save as server-wide default Grok key"):
        save_api_key("grok", admin_grok)
        st.success("Server-wide default Grok key saved. This is now usable by ALL users of this app.")