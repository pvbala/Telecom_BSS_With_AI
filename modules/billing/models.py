from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from datetime import datetime, timezone
from core.db import Base


class Invoice(Base):
    __tablename__ = "billing_invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, index=True)
    account_id = Column(Integer, ForeignKey("party_accounts.id"))
    amount = Column(Float, default=0.0)
    currency = Column(String(8), default="INR")
    status = Column(String(20), default="ISSUED")   # ISSUED | PAID | OVERDUE | DISPUTED
    issued_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    due_at = Column(DateTime)
