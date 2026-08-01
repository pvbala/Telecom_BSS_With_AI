"""
Single entrypoint for the whole modular monolith.
Run with:  uvicorn main:app --reload
"""
import logging
from fastapi import FastAPI
from pydantic import BaseModel

from core.db import init_db
from core import scheduler as core_scheduler

from modules.party.api import router as party_router
from modules.catalog.api import router as catalog_router
from modules.order.api import router as order_router
from modules.inventory.api import router as inventory_router
from modules.billing.api import router as billing_router
from modules.assurance.api import router as assurance_router
from modules.crm.api import router as crm_router

from modules.catalog.service import seed_default_catalog_if_empty
from modules.crm.service import register_event_subscribers as register_crm_subscribers
from ai_ml.event_subscribers import register_event_subscribers as register_ai_event_subscribers
from ai_ml.scheduler_jobs import register_scheduled_jobs

from test_data_engine.orchestrator import run_scenario
from test_data_engine.nl_spec_translator import translate as translate_nl_spec
from ai_ml.serve import score as ai_score
from llm.nl_query import ask as nl_ask

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Telecom BSS/OSS Platform", version="1.0")

app.include_router(party_router)
app.include_router(catalog_router)
app.include_router(order_router)
app.include_router(inventory_router)
app.include_router(billing_router)
app.include_router(assurance_router)
app.include_router(crm_router)


@app.on_event("startup")
def on_startup():
    init_db()                              # additive: only creates missing tables
    seed_default_catalog_if_empty()        # additive: only seeds if catalog is empty
    register_crm_subscribers()             # CRM listens for churn_score_ready
    register_ai_event_subscribers()        # anomaly_detection listens for alarm_raised
    register_scheduled_jobs()              # churn_prediction / revenue_leakage on schedule
    core_scheduler.start()
    logging.info("Telecom BSS/OSS platform started.")


@app.get("/")
def root():
    return {"status": "ok", "message": "Telecom BSS/OSS platform is running"}


# ---- Test Data Generation endpoints ----

class RunScenarioPathRequest(BaseModel):
    spec_path: str


class RunScenarioYamlRequest(BaseModel):
    yaml_text: str


class TranslateNLRequest(BaseModel):
    text: str


@app.post("/test-data/run-from-file")
def run_from_file(req: RunScenarioPathRequest):
    return run_scenario(spec_path=req.spec_path)


@app.post("/test-data/run-from-yaml")
def run_from_yaml(req: RunScenarioYamlRequest):
    return run_scenario(spec_text=req.yaml_text)


@app.post("/test-data/translate")
def translate_nl(req: TranslateNLRequest):
    return translate_nl_spec(req.text)


# ---- AI Insights endpoints ----

@app.get("/ai/score/{use_case_id}")
def score_use_case(use_case_id: str, entity_id: int | None = None):
    return ai_score(use_case_id, entity_id=entity_id)


class NLQueryRequest(BaseModel):
    question: str


@app.post("/ai/nl-query")
def nl_query(req: NLQueryRequest):
    return nl_ask(req.question)
