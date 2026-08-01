import re
import pandas as pd
from core.db import engine
from llm.client import generate

SCHEMA_SUMMARY = """
Tables:
party_customers(id, code, customer_type, name, email, phone, segment, created_at)
party_accounts(id, code, customer_id, status)
catalog_product_offerings(id, code, name, spec_id, price, currency)
order_orders(id, code, customer_id, account_id, status, created_at)
inventory_product_instances(id, code, customer_id, order_id, offering_id, status)
billing_invoices(id, code, account_id, amount, status, issued_at)
assurance_alarms(id, code, severity, alarm_type, description, status, raised_at)
assurance_tickets(id, code, customer_id, subject, status, created_at)
crm_retention_cases(id, code, customer_id, churn_score, reason, status)
"""

_UNSAFE_PATTERN = re.compile(r"\b(drop|delete|update|insert|alter|truncate)\b", re.IGNORECASE)


def ask(question: str) -> dict:
    """Natural-language question -> SQL (via LLM) -> executed against SQLite -> results."""
    prompt = f"""Given this SQLite schema:
{SCHEMA_SUMMARY}

Write ONE read-only SQLite SELECT query (no explanation, just the SQL)
that answers this question: "{question}"
"""
    sql_response = generate(prompt)["text"].strip()
    sql = sql_response.strip("`").replace("sql\n", "").strip()

    if _UNSAFE_PATTERN.search(sql) or not sql.lower().startswith("select"):
        return {"sql": sql, "error": "Generated query was not a safe read-only SELECT; refused to run."}

    try:
        df = pd.read_sql(sql, engine)
        return {"sql": sql, "rows": df.to_dict(orient="records")}
    except Exception as e:
        return {"sql": sql, "error": str(e)}
