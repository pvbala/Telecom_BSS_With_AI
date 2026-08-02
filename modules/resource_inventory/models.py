from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime, timezone
from core.db import Base


class ResourceItem(Base):
    """
    A single allocatable network resource (Section 3/4 - Resource Inventory,
    the OSS layer beneath Service Inventory). Each row is one MSISDN, one
    circuit ID, or one IMSI - either sitting 'available' in the pool for
    future provisioning, or already 'assigned' to a live service instance.
    """
    __tablename__ = "resource_inventory_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_type = Column(String(30), index=True)   # MSISDN | CIRCUIT_ID | IMSI
    value = Column(String(50), unique=True)
    status = Column(String(20), default="available")  # available | assigned
    assigned_service_instance_id = Column(Integer, ForeignKey("inventory_service_instances.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))