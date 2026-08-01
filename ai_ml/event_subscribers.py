"""
Reads each ai_ml/use_case_specs/*.yaml; any spec with `trigger: event_driven`
subscribes to its declared `event_name` on the core event bus, so it fires
the instant the relevant module publishes that event (e.g. an alarm being
raised) - no polling, no dashboard click required.
"""
import yaml
from pathlib import Path
from core.event_bus import subscribe
from ai_ml import serve

SPECS_DIR = Path(__file__).resolve().parent / "use_case_specs"


def register_event_subscribers():
    for path in SPECS_DIR.glob("*.yaml"):
        with open(path) as f:
            spec = yaml.safe_load(f)

        if spec.get("trigger") == "event_driven":
            use_case_id = spec["use_case_id"]
            event_name = spec["event_name"]

            def handler(sender, uc_id=use_case_id, **kwargs):
                print(f"[event_subscriber] {uc_id} triggered by event")
                serve.score(uc_id)

            subscribe(event_name, handler)
            print(f"Subscribed AI use case '{use_case_id}' to event '{event_name}'")
