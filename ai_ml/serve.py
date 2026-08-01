"""
serve.score(use_case_id, entity_id=None) is the ONE function called by:
  - core/scheduler.py (scheduled_daily use cases, e.g. churn_prediction)
  - ai_ml/event_subscribers.py (event_driven use cases, e.g. anomaly_detection)
  - dashboard/pages/2_ai_insights.py ("Run now" button / on-demand lookup)

This keeps a single code path for "run a prediction" regardless of what
triggered it (Section 6.1 / the AI Insights UI design discussed earlier).
"""
import joblib
import pandas as pd
from pathlib import Path

from core.db import engine, get_session
from core.event_bus import publish
from ai_ml import features as feat
from ai_ml.model_registry import get_latest_model

MODELS_DIR = Path(__file__).resolve().parent / "models"


def _load_model(use_case_id: str):
    record = get_latest_model(use_case_id)
    if record and Path(record["file_path"]).exists():
        return joblib.load(record["file_path"])
    return None


def score_churn_prediction(entity_id: int | None = None) -> list[dict]:
    df = feat.build_churn_features()
    if df.empty:
        return []
    if entity_id:
        df = df[df["customer_id"] == entity_id]
        if df.empty:
            return []

    bundle = _load_model("churn_prediction")
    results = []
    for _, row in df.iterrows():
        if bundle:
            X = row[bundle["feature_cols"]].values.reshape(1, -1)
            score = float(bundle["model"].predict(X)[0])
        else:
            # Fallback rule-based score if no model trained yet
            score = (
                0.4 * (1 if row["overdue_invoice_count"] > 0 else 0)
                + 0.4 * (1 if row["ticket_count"] >= 2 else 0)
                + 0.2 * (1 if row["active_product_count"] <= 1 else 0)
            )
        score = round(min(max(score, 0), 1), 3)
        reason_parts = []
        if row["overdue_invoice_count"] > 0:
            reason_parts.append("overdue invoices")
        if row["ticket_count"] >= 2:
            reason_parts.append("multiple support tickets")
        if row["active_product_count"] <= 1:
            reason_parts.append("low product holding")
        reason = ", ".join(reason_parts) or "no strong risk signal"

        result = {"customer_id": int(row["customer_id"]), "score": score, "reason": reason}
        results.append(result)

        if score >= 0.7:
            publish("churn_score_ready", **result)

    return sorted(results, key=lambda r: -r["score"])


def score_anomaly_detection(alarm_id: int | None = None) -> list[dict]:
    df = feat.build_alarm_features()
    if df.empty:
        return []

    bundle = _load_model("anomaly_detection")
    results = []
    for _, row in df.iterrows():
        if bundle:
            X = row[bundle["feature_cols"]].values.reshape(1, -1)
            raw = bundle["model"].decision_function(X)[0]
            is_anomaly = bundle["model"].predict(X)[0] == -1
            score = round(float(1 - (raw + 0.5)), 3)  # rough normalize to ~0-1
        else:
            # Fallback rule: critical/major severity treated as anomalous
            is_anomaly = row["severity_weight"] >= 2
            score = float(row["severity_weight"]) / 3

        result = {"alarm_id": int(row["id"]), "alarm_type": row["alarm_type"],
                   "is_anomaly": bool(is_anomaly), "score": round(min(max(score, 0), 1), 3)}
        results.append(result)
        if is_anomaly:
            publish("anomaly_detected", **result)

    if alarm_id:
        results = [r for r in results if r["alarm_id"] == alarm_id]
    return sorted(results, key=lambda r: -r["score"])


def revenue_leakage_diagnostics() -> dict:
    """
    Distinguishes 'no data generated yet' from 'data exists but everything
    is correctly invoiced' (i.e. genuinely zero leakage) - the two look
    identical as an empty results list, but mean very different things.
    """
    product_count = pd.read_sql(
        "SELECT COUNT(*) as n FROM inventory_product_instances", engine).iloc[0]["n"]
    charge_count = pd.read_sql(
        "SELECT COUNT(*) as n FROM mediation_rated_charges", engine).iloc[0]["n"]
    invoice_count = pd.read_sql(
        "SELECT COUNT(*) as n FROM billing_invoices", engine).iloc[0]["n"]
    return {
        "product_instances": int(product_count),
        "rated_charges": int(charge_count),
        "invoices": int(invoice_count),
        "has_enough_data": product_count > 0 and charge_count > 0,
    }


def score_revenue_leakage(entity_id: int | None = None) -> list[dict]:
    """Rule-based reconciliation: usage rated but not reflected in any invoice amount."""
    products = pd.read_sql("SELECT id, customer_id FROM inventory_product_instances", engine)
    charges = pd.read_sql(
        "SELECT product_instance_id, SUM(amount) as rated_total "
        "FROM mediation_rated_charges GROUP BY product_instance_id", engine)
    if products.empty:
        return []

    df = products.merge(charges, left_on="id", right_on="product_instance_id", how="left")
    df["rated_total"] = df["rated_total"].fillna(0)

    accounts = pd.read_sql("SELECT id as account_id, customer_id FROM party_accounts", engine)
    invoices = pd.read_sql("SELECT account_id, SUM(amount) as invoiced_total "
                            "FROM billing_invoices GROUP BY account_id", engine)
    acc_inv = accounts.merge(invoices, on="account_id", how="left")
    acc_inv["invoiced_total"] = acc_inv["invoiced_total"].fillna(0)
    cust_invoiced = acc_inv.groupby("customer_id")["invoiced_total"].sum()

    results = []
    for _, row in df.iterrows():
        invoiced = float(cust_invoiced.get(row["customer_id"], 0))
        rated = float(row["rated_total"])
        # crude leakage signal: meaningful usage exists but customer has no invoice at all
        if rated > 0 and invoiced == 0:
            result = {"product_instance_id": int(row["id"]), "customer_id": int(row["customer_id"]),
                       "rated_total": rated, "invoiced_total": invoiced,
                       "discrepancy_amount": round(rated, 2)}
            results.append(result)
            publish("leakage_detected", **result)

    if entity_id:
        results = [r for r in results if r["product_instance_id"] == entity_id]
    return results


SCORERS = {
    "churn_prediction": score_churn_prediction,
    "anomaly_detection": score_anomaly_detection,
    "revenue_leakage": score_revenue_leakage,
}


def score(use_case_id: str, entity_id: int | None = None) -> list[dict]:
    """The single entrypoint every trigger (scheduler / event / UI button) calls."""
    if use_case_id not in SCORERS:
        raise ValueError(f"Unknown use_case_id: {use_case_id}")
    return SCORERS[use_case_id](entity_id)