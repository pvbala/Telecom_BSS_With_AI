import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from core.config import get_api_key, save_api_key, configured_providers

st.title("⚙️ Settings — LLM Providers")

st.markdown("""
Keys are **taken as input from you** and saved locally to a `.env` file
in the project folder — never hard-coded in the code. The platform tries
providers in this order: **Gemini → Grok → Ollama (local, always
available, no token limit)**.
""")

status = configured_providers()

st.subheader("Gemini API Key")
gemini_key = st.text_input(
    "Gemini API key", value=get_api_key("gemini") or "", type="password",
    help="Get one from https://aistudio.google.com/apikey",
)
if st.button("Save Gemini Key"):
    save_api_key("gemini", gemini_key)
    st.success("Gemini key saved.")

st.subheader("Grok (xAI) API Key")
grok_key = st.text_input(
    "Grok API key", value=get_api_key("grok") or "", type="password",
    help="Get one from https://console.x.ai",
)
if st.button("Save Grok Key"):
    save_api_key("grok", grok_key)
    st.success("Grok key saved.")

st.subheader("Ollama (local fallback)")
st.info(
    "No key needed. Install Ollama (https://ollama.com), run `ollama pull llama3.1`, "
    "and it will be used automatically whenever Gemini and Grok are unavailable or "
    "rate/token-limited."
)

st.subheader("Current status")
st.json(configured_providers())
