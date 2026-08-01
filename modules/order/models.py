from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from core.db import Base


class Order(Base):
    __tablename__ = "order_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("party_customers.id"))
    account_id = Column(Integer, ForeignKey("party_accounts.id"))
    channel = Column(String(30), default="online")
    status = Column(String(30), default="CREATED")
    # CREATED -> VALIDATED -> PROVISIONING -> ACTIVE -> BILLED (or FAILED at any step)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("order_orders.id"))
    offering_id = Column(Integer, ForeignKey("catalog_product_offerings.id"))
    attributes = Column(JSON, default=dict)     # characteristic values chosen for this order line
    action = Column(String(20), default="add")  # add | modify | cease
    price = Column(Float, default=0.0)

    order = relationship("Order", back_populates="items")
