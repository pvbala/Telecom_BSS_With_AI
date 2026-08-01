from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from core.db import Base


class Customer(Base):
    __tablename__ = "party_customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, index=True)      # e.g. CUST-0001, continues additively
    customer_type = Column(String(20), default="individual")  # individual | organization
    name = Column(String(200), nullable=False)
    email = Column(String(200))
    phone = Column(String(30))
    address = Column(String(300))
    segment = Column(String(50), default="consumer")         # consumer | sme | enterprise
    credit_profile = Column(JSON, default=dict)               # flexible extra attributes
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    accounts = relationship("Account", back_populates="customer")


class Account(Base):
    __tablename__ = "party_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, index=True)       # e.g. ACC-0001
    customer_id = Column(Integer, ForeignKey("party_customers.id"))
    billing_cycle_day = Column(Integer, default=1)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer", back_populates="accounts")
