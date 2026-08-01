from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from datetime import datetime, timezone
from core.db import Base


class ProductInstance(Base):
    """What a customer actually owns - the Product Inventory (Section 3)."""
    __tablename__ = "inventory_product_instances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("party_customers.id"))
    order_id = Column(Integer, ForeignKey("order_orders.id"))
    offering_id = Column(Integer, ForeignKey("catalog_product_offerings.id"))
    attributes = Column(JSON, default=dict)
    status = Column(String(20), default="pending")   # pending | active | suspended | terminated
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ServiceInstance(Base):
    """The OSS-side realization of a product instance (Section 3)."""
    __tablename__ = "inventory_service_instances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, index=True)
    product_instance_id = Column(Integer, ForeignKey("inventory_product_instances.id"))
    service_type = Column(String(50))         # e.g. mobile_line, broadband_line, iot_connection
    network_identifier = Column(String(50))   # e.g. MSISDN, circuit ID, IMSI
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
