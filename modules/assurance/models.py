from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from datetime import datetime, timezone
from core.db import Base


class Alarm(Base):
    __tablename__ = "assurance_alarms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, index=True)
    service_instance_id = Column(Integer, ForeignKey("inventory_service_instances.id"), nullable=True)
    severity = Column(String(20), default="minor")   # critical | major | minor | warning
    alarm_type = Column(String(50))
    description = Column(String(300))
    raised_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default="open")


class TroubleTicket(Base):
    __tablename__ = "assurance_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("party_customers.id"), nullable=True)
    alarm_id = Column(Integer, ForeignKey("assurance_alarms.id"), nullable=True)
    subject = Column(String(200))
    description = Column(String(1000))
    status = Column(String(20), default="open")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
