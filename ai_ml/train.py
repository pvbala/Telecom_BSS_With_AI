"""
Generic training entrypoint. Usage:
    python -m ai_ml.train churn_prediction
    python -m ai_ml.train anomaly_detection

Reads the use_case_specs/<id>.yaml, extracts features, trains the model
type declared in the spec, and registers the resulting artifact in the
ai_model_registry table (via ai_ml.model_registry).
"""
import sys
import joblib
import yaml
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, IsolationForest

from ai_ml import features as feat
from ai_ml.model_registry import register_model

SPECS_DIR = Path(__file__).resolve().parent / "use_case_specs"
MODELS_DIR = Path(__file__).resolve().parent / "models"
MODELS_DIR.mkdir(exist_ok=True)


def _load_spec(use_case_id: str) -> dict:
    path = SPECS_DIR / f"{use_case_id}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def train_churn_prediction():
    df = feat.build_churn_features()
    if df.empty or len(df) < 3:
        print("Not enough customer data to train churn model yet. Generate test data first.")
        return None

    feature_cols = ["tenure_days", "invoice_count", "overdue_invoice_count",
                     "ticket_count", "active_product_count"]
    X = df[feature_cols].values

    # No real churn labels exist yet in freshly generated test data, so we
    # bootstrap a proxy risk label from a transparent weighted rule, and
    # train a regressor against it. As real churn outcomes are observed in
    # production, this proxy label is replaced by the real outcome column
    # (the standard MLOps feedback loop described in Section 6).
    proxy_label = (
        0.4 * (df["overdue_invoice_count"] > 0).astype(float)
        + 0.4 * (df["ticket_count"] >= 2).astype(float)
        + 0.2 * (df["active_product_count"] <= 1).astype(float)
    )

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, proxy_label)

    file_path = MODELS_DIR / "churn_prediction.joblib"
    joblib.dump({"model": model, "feature_cols": feature_cols}, file_path)

    metrics = {"training_rows": len(df), "note": "proxy-label bootstrap model"}
    record = register_model("churn_prediction", str(file_path), metrics)
    print(f"Trained churn_prediction model: {record}")
    return record


def train_anomaly_detection():
    df = feat.build_alarm_features()
    if df.empty or len(df) < 5:
        print("Not enough alarm data to train anomaly model yet. Generate test data first.")
        return None

    feature_cols = ["severity_weight", "alarms_last_hour_same_type"]
    X = df[feature_cols].values

    model = IsolationForest(contamination=0.15, random_state=42)
    model.fit(X)

    file_path = MODELS_DIR / "anomaly_detection.joblib"
    joblib.dump({"model": model, "feature_cols": feature_cols}, file_path)

    metrics = {"training_rows": len(df)}
    record = register_model("anomaly_detection", str(file_path), metrics)
    print(f"Trained anomaly_detection model: {record}")
    return record


TRAINERS = {
    "churn_prediction": train_churn_prediction,
    "anomaly_detection": train_anomaly_detection,
}


def train(use_case_id: str):
    if use_case_id not in TRAINERS:
        print(f"No trainer implemented for '{use_case_id}' "
              f"(revenue_leakage is rule-based, no training needed)")
        return None
    return TRAINERS[use_case_id]()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m ai_ml.train <use_case_id>")
        sys.exit(1)
    train(sys.argv[1])
