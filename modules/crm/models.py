from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from datetime import datetime, timezone
from core.db import Base


class RetentionCase(Base):
    """Created automatically when the Churn Prediction AI flags a customer (Section 6)."""
    __tablename__ = "crm_retention_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("party_customers.id"))
    churn_score = Column(Float)
    reason = Column(String(300))
    status = Column(String(20), default="open")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
