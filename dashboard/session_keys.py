"""
Every dashboard page that calls an LLM function should use get_session_keys()
to fetch THIS BROWSER SESSION's own keys (set on the Settings page) and pass
them explicitly into llm.client.generate() / translate() / narrate_anomaly()
/ ask(). This is what keeps one user's key from being usable by another user
of the same running app - see core/config.py and llm/client.py for the full
explanation.
"""
import streamlit as st


def get_session_keys() -> tuple[str | None, str | None]:
    """Returns (gemini_key, grok_key) for the CURRENT user's browser session only."""
    return st.session_state.get("gemini_api_key"), st.session_state.get("grok_api_key")


def has_session_key(provider: str) -> bool:
    return bool(st.session_state.get(f"{provider}_api_key"))