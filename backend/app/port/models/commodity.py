"""
Commodity model - Types of cargo/commodities handled in port
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class Commodity(Base):
    """
    Commodity model - represents types of cargo handled
    """
    __tablename__ = "commodities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # e.g., "iron_ore", "coal", "grain", "fertilizer"
    is_active = Column(Boolean, default=True, nullable=False)

    # Physical properties
    density = Column(Float, nullable=True)  # kg/m³
    angle_of_repose = Column(Float, nullable=True)  # degrees
    moisture_content_max = Column(Float, nullable=True)  # percentage
    particle_size_avg = Column(Float, nullable=True)  # mm

    # Handling requirements
    requires_special_handling = Column(Boolean, default=False, nullable=False)
    handling_instructions = Column(Text, nullable=True)
    environmental_restrictions = Column(Text, nullable=True)

    # Performance metrics
    standard_loading_rate = Column(Float, nullable=True)  # tons/hour
    optimal_loading_rate = Column(Float, nullable=True)  # tons/hour
    total_volume_handled = Column(Float, default=0.0, nullable=False)  # tons

    # Pricing (optional)
    unit_price = Column(Float, nullable=True)  # per ton
    currency = Column(String(10), default="USD", nullable=False)

    # Additional info
    metadata_json = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    site = relationship("Site", back_populates="commodities")
    storage_units = relationship("StorageUnit", back_populates="commodity")
    loading_operations = relationship("LoadingOperation", back_populates="commodity")

    def __repr__(self):
        return f"<Commodity {self.name} ({self.code})>"
