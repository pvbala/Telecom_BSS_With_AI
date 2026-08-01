# Telecom BSS/OSS Platform (Laptop / Minimal Profile)

A Python-first, modular-monolith implementation of a Telecom BSS/OSS platform:
flexible multi-product catalog, order-to-cash orchestration, a Business-Process-Test-Case-driven
synthetic data engine, and a spec-driven AI prediction framework (churn, anomaly detection,
revenue leakage) with an LLM cascade (Gemini → Grok → Ollama) for natural-language features.

## 1. Setup

```bash
cd telecom_platform
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in keys, OR use the Settings page in the UI
```

Optional (for the LLM fallback's final tier): install [Ollama](https://ollama.com), then:
```bash
ollama pull llama3.1
```
If you skip Ollama, the platform still works — Gemini/Grok are simply tried first, and if
neither is configured, LLM-powered features (NL→YAML spec translation, troubleshooting
narratives, NL→SQL) will show a clear error until you add a key or install Ollama.

## 2. Run

**Terminal 1 — the platform API (all BSS/OSS modules):**
```bash
uvicorn main:app --reload
```
API docs: http://localhost:8000/docs

**Terminal 2 — the dashboard:**
```bash
streamlit run dashboard/Home.py
```
Opens at http://localhost:8501 — includes:
- **Settings** — enter Gemini/Grok API keys
- **Test Data Generator** — plain-English or YAML business process specs
- **AI Insights** — churn / anomaly / leakage predictions, train & run on demand
- **CRM** — customers, orders, invoices, auto-generated retention cases
- **NOC / Assurance** — alarms, tickets, anomaly detection, NL→SQL queries

## 3. Generate test data (three ways)

**a) Via the dashboard (recommended):** open the Test Data Generator page, type e.g.
`Create 5 Customers, Put 2 Orders for each of these 5 customers, provision the service, raise the invoice.`
Review the generated YAML, click Validate, then Run.

**b) Via the CLI:**
```bash
python -m test_data_engine.orchestrator test_data_engine/scenario_library/five_customers_two_orders.yaml
```

**c) Via the API:**
```bash
curl -X POST http://localhost:8000/test-data/run-from-file \
  -H "Content-Type: application/json" \
  -d '{"spec_path": "test_data_engine/scenario_library/five_customers_two_orders.yaml"}'
```

Every run is **additive** — running the same scenario twice creates a second batch of
customers/orders/invoices on top of the first; nothing already in `telecom.db` is ever deleted
or overwritten.

## 4. Train and run AI predictions

```bash
python -m ai_ml.train churn_prediction
python -m ai_ml.train anomaly_detection
```
(revenue_leakage is rule-based reconciliation — no training needed)

Then use the AI Insights dashboard page, or:
```bash
curl "http://localhost:8000/ai/score/churn_prediction"
```

## 5. Project structure

```
telecom_platform/
├── main.py                 FastAPI app - all module routers + startup wiring
├── core/                   db, event_bus, scheduler, config (API keys)
├── modules/                party, catalog, order, inventory, provisioning,
│                            mediation_rating, billing, assurance, crm
├── test_data_engine/       spec_parser, orchestrator, data_factory, nl_spec_translator
├── ai_ml/                  use_case_specs (YAML), features, train, serve, scheduler_jobs,
│                            event_subscribers, model_registry
├── llm/                    client (Gemini→Grok→Ollama cascade), troubleshoot_narrator,
│                            ticket_assistant, nl_query
├── dashboard/               Streamlit multipage app
├── telecom.db               SQLite database (created on first run)
└── requirements.txt
```

## 6. Adding a new product (no code change)

Use the Catalog API/service to add a `ProductSpecification` (its attribute schema) and a
`ProductOffering` (price/name). Example:
```python
from modules.catalog.service import create_product_spec, create_offering
spec = create_product_spec(
    name="Enterprise WAN Link", category="Enterprise",
    characteristic_schema=[
        {"name": "BandwidthMbps", "type": "number", "required": True},
        {"name": "SLA", "type": "enum", "values": ["gold", "silver", "bronze"], "required": True},
    ],
)
create_offering(name="Enterprise WAN 1Gbps Gold", spec_id=spec["spec_id"], price=49999)
```
No other code needs to change — Order, Inventory, Billing all work generically off the schema.

## 7. Adding a new AI prediction (no new infrastructure)

Add a new YAML file under `ai_ml/use_case_specs/`, add a trainer function in `ai_ml/train.py`
and a scorer function in `ai_ml/serve.py`'s `SCORERS` dict. The scheduler/event-subscriber
wiring in `ai_ml/scheduler_jobs.py` and `ai_ml/event_subscribers.py` picks it up automatically
based on the spec's `trigger` field.
