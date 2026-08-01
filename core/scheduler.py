"""
Wraps APScheduler as an in-process background scheduler, started inside
the FastAPI process (main.py). ai_ml/scheduler_jobs.py registers each AI
use case whose spec declares a `scheduled_*` trigger.
"""
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()


def start():
    if not scheduler.running:
        scheduler.start()


def add_daily_job(func, job_id: str, hour: int = 2, minute: int = 0):
    scheduler.add_job(func, "cron", hour=hour, minute=minute, id=job_id, replace_existing=True)


def add_interval_job(func, job_id: str, minutes: int = 60):
    scheduler.add_job(func, "interval", minutes=minutes, id=job_id, replace_existing=True)


def run_now(job_id: str):
    job = scheduler.get_job(job_id)
    if job:
        job.func()
