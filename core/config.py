"""
Central configuration for the Telecom BSS/OSS platform.

*** MULTI-USER KEY ISOLATION - READ THIS FIRST ***
This app can be used by multiple people connecting to the same running
instance at once. os.environ and the .env file below are PROCESS-WIDE:
anything stored there is visible to and usable by every user of this
deployment, not just the person who entered it.

For that reason, get_api_key()/save_api_key() in this file represent an
explicit, OPT-IN "server-wide default" key only - e.g. something a
solo developer sets once for their own local single-user use, or an
admin deliberately provisions as a shared fallback for a whole team.

Each individual user's OWN personal key should instead be kept in that
user's Streamlit session only (st.session_state, set on the Settings
page - see dashboard/pages/0_Settings.py) and passed explicitly into
llm.client.generate(gemini_key=..., grok_key=...) on every call. Nothing
in this file, and nothing in llm/client.py, reads a personal key from
shared process state - keys only flow in as explicit function arguments.
"""
import os
from pathlib import Path
from dotenv import load_dotenv, set_key

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

# Load whatever is already in .env into the process environment.
# This never deletes/overwrites existing data - it only loads config.
load_dotenv(dotenv_path=ENV_PATH, override=False)

DB_PATH = BASE_DIR / "telecom.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Order in which LLM providers are tried: Gemini -> Grok -> Ollama (local, no token limit)
LLM_PROVIDER_ORDER = ["gemini", "grok", "ollama"]

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

# Model names for cloud providers - these change/get deprecated often, so they
# are overridable via .env without touching code. Defaults below are current
# as of July 2026; if you get a 404/model-not-found error, check the
# provider's docs for their latest model name and set it in .env.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4.5")


def get_api_key(provider: str) -> str | None:
    """
    Reads the SERVER-WIDE DEFAULT key (process env / .env) for a provider.
    This is a shared fallback only - see the module docstring. Personal,
    per-user keys must NOT go through this function; pass them explicitly
    into llm.client.generate() instead.
    """
    key_name = {"gemini": "GEMINI_API_KEY", "grok": "GROK_API_KEY"}.get(provider)
    if not key_name:
        return None
    return os.getenv(key_name)


def save_api_key(provider: str, value: str) -> None:
    """
    Persists a SERVER-WIDE DEFAULT key into the local .env file AND the
    current process environment. This key becomes usable by EVERY user
    of this running app, not just whoever calls this function - only use
    it for a genuinely shared/admin-provisioned key or solo local use,
    never to store an individual user's personal key.
    """
    key_name = {"gemini": "GEMINI_API_KEY", "grok": "GROK_API_KEY"}.get(provider)
    if not key_name:
        raise ValueError(f"Unknown provider: {provider}")
    if not ENV_PATH.exists():
        ENV_PATH.touch()
    set_key(str(ENV_PATH), key_name, value)
    os.environ[key_name] = value


def configured_providers() -> dict:
    """Return which providers currently have a server-wide default key/endpoint configured."""
    return {
        "gemini": bool(get_api_key("gemini")),
        "grok": bool(get_api_key("grok")),
        "ollama": True,  # local, no key required
    }