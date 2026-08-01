"""
Central configuration for the Telecom BSS/OSS platform.

API keys are NEVER hard-coded. They are taken as input from the user at
runtime, in this order of precedence:
  1. Already set in the OS environment (os.environ)
  2. Present in a local .env file (loaded via python-dotenv)
  3. Entered by the user through the Streamlit "Settings" page, which
     writes them into .env for future runs.

If none of the above are available when an LLM call is made, the LLM
client will raise a clear error asking the user to enter a key via the
Settings page, rather than silently failing.
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
    """Read an API key for a given provider ('gemini' or 'grok') from env."""
    key_name = {"gemini": "GEMINI_API_KEY", "grok": "GROK_API_KEY"}.get(provider)
    if not key_name:
        return None
    return os.getenv(key_name)


def save_api_key(provider: str, value: str) -> None:
    """
    Persist an API key entered by the user (e.g. via the Streamlit Settings
    page) into the local .env file AND the current process environment,
    so it's usable immediately without a restart.
    """
    key_name = {"gemini": "GEMINI_API_KEY", "grok": "GROK_API_KEY"}.get(provider)
    if not key_name:
        raise ValueError(f"Unknown provider: {provider}")
    if not ENV_PATH.exists():
        ENV_PATH.touch()
    set_key(str(ENV_PATH), key_name, value)
    os.environ[key_name] = value


def configured_providers() -> dict:
    """Return which providers currently have a usable key/endpoint configured."""
    return {
        "gemini": bool(get_api_key("gemini")),
        "grok": bool(get_api_key("grok")),
        "ollama": True,  # local, no key required
    }