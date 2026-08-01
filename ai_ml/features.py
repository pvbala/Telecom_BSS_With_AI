"""
Feature computation for AI use cases. In the laptop profile, the
'feature store' is simply: compute on demand from the DB with pandas,
and optionally cache to a Parquet file under ai_ml/features/ for reuse.
"""
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from core.db import engine

FEATURES_DIR = Path(__file__).resolve().parent / "features"
FEATURES_DIR.mkdir(exist_ok=True)


def build_churn_features() -> pd.DataFrame:
    customers = pd.read_sql("SELECT id as customer_id, created_at FROM party_customers", engine)
    if customers.empty:
        return pd.DataFrame()

    invoices = pd.read_sql(
        "SELECT account_id, status FROM billing_invoices", engine)
    accounts = pd.read_sql(
        "SELECT id as account_id, customer_id FROM party_accounts", engine)
    tickets = pd.read_sql(
        "SELECT customer_id FROM assurance_tickets", engine)
    products = pd.read_sql(
        "SELECT customer_id, status FROM inventory_product_instances", engine)

    inv = invoices.merge(accounts, on="account_id", how="left")
    invoice_count = inv.groupby("customer_id").size().rename("invoice_count")
    overdue_count = (inv[inv["status"] == "OVERDUE"]
                      .groupby("customer_id").size().rename("overdue_invoice_count"))
    ticket_count = tickets.groupby("customer_id").size().rename("ticket_count")
    active_products = (products[products["status"] == "active"]
                        .groupby("customer_id").size().rename("active_product_count"))

    customers["created_at"] = pd.to_datetime(customers["created_at"])
    now = pd.Timestamp.now(tz=customers["created_at"].dt.tz)
    customers["tenure_days"] = (now - customers["created_at"]).dt.days

    df = customers.set_index("customer_id")
    df = df.join([invoice_count, overdue_count, ticket_count, active_products])
    df = df.fillna(0)
    return df.reset_index()


def build_alarm_features() -> pd.DataFrame:
    alarms = pd.read_sql("SELECT * FROM assurance_alarms", engine)
    if alarms.empty:
        return pd.DataFrame()
    severity_weight = {"critical": 3, "major": 2, "minor": 1, "warning": 0.5}
    alarms["severity_weight"] = alarms["severity"].map(severity_weight).fillna(1)
    alarms["raised_at"] = pd.to_datetime(alarms["raised_at"])
    alarms = alarms.sort_values("raised_at")
    alarms["alarms_last_hour_same_type"] = (
        alarms.groupby("alarm_type").cumcount()
    )
    return alarms
