"""
Single call site for all LLM usage in the platform.

MULTI-USER KEY ISOLATION:
API keys are passed in EXPLICITLY per call (gemini_key / grok_key
parameters) rather than read from a shared global/environment variable.
This matters because this app can be used by multiple people at once:
os.environ and a shared .env file are process-wide, so if one person's
key were stored there, every other user of the same running app would
silently be able to use it too. Each Streamlit session resolves its own
key from st.session_state (see dashboard/pages/0_Settings.py) and passes
it into these functions explicitly - nothing here reads a shared key by
default. core.config.get_api_key() is used only as an OPT-IN server-wide
fallback (see core/config.py) for single-user/local deployments.

generate(prompt) tries providers in order: Gemini -> Grok -> Ollama.
- Gemini and Grok are cloud APIs with token/rate limits - if either
  raises a rate-limit, quota, auth, timeout, or connection error, it
  falls through to the next provider.
- Ollama is the guaranteed local last resort (no token limit, no cost,
  fully offline, no key needed) - it always runs if the two cloud
  providers are unavailable, exhausted, or no key was supplied for them.
"""
import logging
import requests
from core.config import get_api_key, OLLAMA_HOST, OLLAMA_MODEL, GEMINI_MODEL, GROK_MODEL

log = logging.getLogger("llm_client")

PROVIDER_ORDER = ["gemini", "grok", "ollama"]


class ProviderError(Exception):
    pass


def _call_gemini(prompt: str, api_key: str | None = None) -> str:
    api_key = api_key or get_api_key("gemini")
    if not api_key:
        raise ProviderError("No Gemini API key available. Enter your own key in the Settings page.")
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt)
    if not getattr(response, "text", None):
        raise ProviderError("Gemini returned an empty response")
    return response.text


def _call_grok(prompt: str, api_key: str | None = None) -> str:
    api_key = api_key or get_api_key("grok")
    if not api_key:
        raise ProviderError("No Grok API key available. Enter your own key in the Settings page.")
    # Grok (xAI) exposes an OpenAI-compatible chat completions endpoint
    resp = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": GROK_MODEL,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    if resp.status_code == 429:
        raise ProviderError("Grok rate/token limit reached")
    if resp.status_code >= 400:
        # Surface the actual response body - xAI returns a helpful error
        # message (e.g. "model not found") in the body on 400s, which a
        # bare raise_for_status() would otherwise swallow.
        raise ProviderError(f"Grok {resp.status_code} error: {resp.text[:300]}")
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _call_ollama(prompt: str, api_key: str | None = None) -> str:
    # Ollama is local and needs no key; api_key is accepted (and ignored)
    # only so every caller in _CALLERS shares the same signature.
    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=300,   # local model generation can be slow on a laptop CPU
        )
    except requests.exceptions.ConnectionError:
        raise ProviderError(
            f"Could not connect to Ollama at {OLLAMA_HOST}. Is Ollama running? "
            f"Start it with 'ollama serve' (or just open the Ollama app)."
        )
    except requests.exceptions.ReadTimeout:
        raise ProviderError(
            f"Ollama did not respond within 300s for model '{OLLAMA_MODEL}'. "
            f"First run after 'ollama pull' can be slow while the model loads into "
            f"memory - try again, or use a smaller model (e.g. 'phi3' or 'llama3.2:1b')."
        )
    if resp.status_code == 404:
        raise ProviderError(
            f"Ollama model '{OLLAMA_MODEL}' not found locally. Run: ollama pull {OLLAMA_MODEL}"
        )
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "")


_CALLERS = {"gemini": _call_gemini, "grok": _call_grok, "ollama": _call_ollama}


def generate(prompt: str, providers: list[str] | None = None,
             gemini_key: str | None = None, grok_key: str | None = None) -> dict:
    """
    Returns {"text": ..., "provider_used": ...}.
    Tries each provider in PROVIDER_ORDER (or a custom order) until one
    succeeds; raises RuntimeError only if all configured/available
    providers fail (Ollama should virtually always succeed if installed).

    gemini_key / grok_key: pass the CALLING USER'S OWN key here (e.g.
    from st.session_state in a Streamlit page). If omitted, falls back
    to any server-wide default configured via core.config - which is
    intentionally opt-in and shared, so leave these None-safe defaults
    alone for multi-user deployments and always pass explicit keys.
    """
    order = providers or PROVIDER_ORDER
    key_map = {"gemini": gemini_key, "grok": grok_key, "ollama": None}
    last_error = None
    for provider in order:
        try:
            text = _CALLERS[provider](prompt, key_map.get(provider))
            return {"text": text, "provider_used": provider}
        except Exception as e:
            log.warning("Provider '%s' failed: %s — falling back", provider, e)
            last_error = e
            continue
    raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")