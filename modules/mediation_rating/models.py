from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from datetime import datetime, timezone
from core.db import Base


class UsageRecord(Base):
    """Raw usage event (a simplified CDR/xDR)."""
    __tablename__ = "mediation_usage_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_instance_id = Column(Integer, ForeignKey("inventory_product_instances.id"))
    usage_type = Column(String(30))          # data_mb | voice_min | sms
    quantity = Column(Float, default=0.0)
    event_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class RatedCharge(Base):
    """A usage record after rating (converted to money)."""
    __tablename__ = "mediation_rated_charges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usage_record_id = Column(Integer, ForeignKey("mediation_usage_records.id"))
    product_instance_id = Column(Integer, ForeignKey("inventory_product_instances.id"))
    amount = Column(Float, default=0.0)
    currency = Column(String(8), default="INR")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
