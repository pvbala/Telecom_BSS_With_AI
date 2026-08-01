"""
Reads each ai_ml/use_case_specs/*.yaml at startup; any spec whose
`trigger` starts with `scheduled_` gets registered as a background job
with core/scheduler.py, running the SAME score() function the dashboard
'Run now' button and event subscribers use.
"""
import yaml
from pathlib import Path
from core import scheduler
from ai_ml import serve

SPECS_DIR = Path(__file__).resolve().parent / "use_case_specs"


def _load_all_specs() -> list[dict]:
    specs = []
    for path in SPECS_DIR.glob("*.yaml"):
        with open(path) as f:
            specs.append(yaml.safe_load(f))
    return specs


def register_scheduled_jobs():
    for spec in _load_all_specs():
        trigger = spec.get("trigger", "")
        use_case_id = spec["use_case_id"]
        if trigger.startswith("scheduled"):
            job_id = f"ai_job_{use_case_id}"

            def job(uc_id=use_case_id):
                print(f"[scheduler] running scheduled use case: {uc_id}")
                serve.score(uc_id)

            if trigger == "scheduled_daily":
                scheduler.add_daily_job(job, job_id=job_id, hour=2, minute=0)
            else:
                scheduler.add_interval_job(job, job_id=job_id, minutes=60)
            print(f"Registered scheduled AI job: {use_case_id} ({trigger})")
