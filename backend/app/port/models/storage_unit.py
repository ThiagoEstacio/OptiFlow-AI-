"""
Storage Unit model - Storage areas/yards for commodities
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Float, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class StorageUnit(Base):
    """
    Storage Unit model - represents storage yards/silos for commodities
    """
    __tablename__ = "storage_units"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    storage_type = Column(String(50), nullable=False)  # e.g., "yard", "silo", "warehouse", "dome"
    is_active = Column(Boolean, default=True, nullable=False)

    # Commodity
    commodity_id = Column(UUID(as_uuid=True), ForeignKey("commodities.id", ondelete="SET NULL"), nullable=True)

    # Capacity
    max_capacity = Column(Float, nullable=False)  # tons
    current_inventory = Column(Float, default=0.0, nullable=False)  # tons
    available_capacity = Column(Float, nullable=True)  # tons (calculated)
    utilization_percentage = Column(Float, nullable=True)

    # Physical dimensions
    length = Column(Float, nullable=True)  # meters
    width = Column(Float, nullable=True)  # meters
    height = Column(Float, nullable=True)  # meters
    area = Column(Float, nullable=True)  # square meters
    volume = Column(Float, nullable=True)  # cubic meters

    # Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    zone = Column(String(100), nullable=True)  # Storage zone/area
    location_metadata = Column(JSONB, default=dict, nullable=False)

    # Equipment
    has_stacker_reclaimer = Column(Boolean, default=False, nullable=False)
    stacker_reclaimer_capacity = Column(Float, nullable=True)  # tons/hour
    connected_conveyor_ids = Column(JSONB, default=list, nullable=False)

    # Inventory tracking
    total_received = Column(Float, default=0.0, nullable=False)  # tons (lifetime)
    total_dispatched = Column(Float, default=0.0, nullable=False)  # tons (lifetime)
    last_receipt_date = Column(DateTime(timezone=True), nullable=True)
    last_dispatch_date = Column(DateTime(timezone=True), nullable=True)

    # Quality management
    quality_parameters = Column(JSONB, default=dict, nullable=False)
    # Example: {"moisture_content": 8.5, "iron_content": 62.3}

    # Environmental monitoring
    dust_suppression_enabled = Column(Boolean, default=False, nullable=False)
    temperature_monitoring = Column(Boolean, default=False, nullable=False)
    environmental_sensors = Column(JSONB, default=list, nullable=False)

    # Additional info
    metadata_json = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    site = relationship("Site", back_populates="storage_units")
    commodity = relationship("Commodity", back_populates="storage_units")
    outbound_routes = relationship("LoadingRoute", foreign_keys="LoadingRoute.source_storage_id", back_populates="source_storage")

    def __repr__(self):
        return f"<StorageUnit {self.name} ({self.code}) - {self.current_inventory}/{self.max_capacity} tons>"
