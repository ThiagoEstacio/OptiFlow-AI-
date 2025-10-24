"""
Berth model - Berth/Dock position in port
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class BerthStatus(str, enum.Enum):
    """Berth operational status"""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"
    OUT_OF_SERVICE = "out_of_service"


class Berth(Base):
    """
    Berth model - represents berth/dock positions in port
    """
    __tablename__ = "berths"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Physical specifications
    length = Column(Float, nullable=False)  # meters
    depth = Column(Float, nullable=False)  # meters (water depth)
    max_vessel_length = Column(Float, nullable=True)  # meters
    max_vessel_draft = Column(Float, nullable=True)  # meters

    # Operational info
    status = Column(SQLEnum(BerthStatus), default=BerthStatus.AVAILABLE, nullable=False, index=True)
    vessel_types_allowed = Column(JSONB, default=list, nullable=False)  # List of allowed vessel types

    # Equipment
    has_shiploader = Column(Boolean, default=False, nullable=False)
    shiploader_capacity = Column(Float, nullable=True)  # tons/hour
    number_of_cranes = Column(Integer, default=0, nullable=False)
    conveyor_systems = Column(JSONB, default=list, nullable=False)  # List of connected conveyor IDs

    # Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_metadata = Column(JSONB, default=dict, nullable=False)

    # Performance metrics (calculated)
    total_vessels_handled = Column(Integer, default=0, nullable=False)
    total_cargo_handled = Column(Float, default=0.0, nullable=False)  # tons
    average_berth_time_hours = Column(Float, nullable=True)
    utilization_percentage = Column(Float, nullable=True)

    # Maintenance
    last_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    next_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    maintenance_notes = Column(Text, nullable=True)

    # Additional info
    metadata_json = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    site = relationship("Site", back_populates="berths")
    current_vessels = relationship("Vessel", foreign_keys="Vessel.current_berth_id", back_populates="current_berth")
    loading_operations = relationship("LoadingOperation", back_populates="berth", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Berth {self.name} ({self.code}) - {self.status.value}>"
