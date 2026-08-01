from sqlalchemy import Column, Integer, String, DateTime, Float, JSON
from datetime import datetime, timezone
from core.db import Base, get_session


class ModelRecord(Base):
    """Metadata for a trained model artifact (replaces an MLflow server for laptop scale)."""
    __tablename__ = "ai_model_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    use_case_id = Column(String(100), index=True)
    version = Column(Integer, default=1)
    file_path = Column(String(300))
    metrics = Column(JSON, default=dict)
    trained_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def register_model(use_case_id: str, file_path: str, metrics: dict) -> dict:
    with get_session() as session:
        existing = session.query(ModelRecord).filter(
            ModelRecord.use_case_id == use_case_id).count()
        record = ModelRecord(use_case_id=use_case_id, version=existing + 1,
                              file_path=file_path, metrics=metrics)
        session.add(record)
        session.flush()
        return {"id": record.id, "use_case_id": use_case_id, "version": record.version,
                "file_path": file_path, "metrics": metrics}


def get_latest_model(use_case_id: str) -> dict | None:
    with get_session() as session:
        rec = (session.query(ModelRecord)
               .filter(ModelRecord.use_case_id == use_case_id)
               .order_by(ModelRecord.version.desc())
               .first())
        if not rec:
            return None
        return {"file_path": rec.file_path, "version": rec.version, "metrics": rec.metrics,
                 "trained_at": rec.trained_at.isoformat() if rec.trained_at else None}