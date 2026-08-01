from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from core.db import Base


class ProductSpecification(Base):
    """
    Defines the SCHEMA of a product family (e.g. 'Postpaid Mobile Plan').
    characteristic_schema is a JSON list of attribute definitions, e.g.:
    [{"name": "DataAllowanceGB", "type": "number", "required": true},
     {"name": "SIMType", "type": "enum", "values": ["physical","eSIM"], "required": true}]
    This is what lets new products with DIFFERENT attributes be added
    purely as data, with no code change.
    """
    __tablename__ = "catalog_product_specs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100))                 # Mobile, Broadband, IoT, Enterprise WAN...
    characteristic_schema = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    offerings = relationship("ProductOffering", back_populates="spec")


class ProductOffering(Base):
    """The commercial/sellable wrapper around a ProductSpecification: price + validity."""
    __tablename__ = "catalog_product_offerings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, index=True)
    name = Column(String(200), nullable=False)
    spec_id = Column(Integer, ForeignKey("catalog_product_specs.id"))
    price = Column(Float, default=0.0)
    currency = Column(String(8), default="INR")
    billing_frequency = Column(String(20), default="monthly")   # monthly | one_time | usage_based
    is_active = Column(String(10), default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    spec = relationship("ProductSpecification", back_populates="offerings")
