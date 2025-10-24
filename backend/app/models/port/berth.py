"""
Berth model - Port berths/terminals for vessel operations
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
    AVAILABLE = "available"  # Ready for vessel
    OCCUPIED = "occupied"  # Vessel at berth
    RESERVED = "reserved"  # Reserved for incoming vessel
    MAINTENANCE = "maintenance"  # Under maintenance
    UNAVAILABLE = "unavailable"  # Unavailable for operations


class BerthType(str, enum.Enum):
    """Type of berth/terminal"""
    BULK = "bulk"  # For bulk cargo (grains, coal, ore)
    CONTAINER = "container"  # For container vessels
    LIQUID = "liquid"  # For liquid bulk (oil, chemicals)
    GENERAL = "general"  # General cargo
    MULTIPURPOSE = "multipurpose"  # Multiple cargo types


class Berth(Base):
    """
    Berth model - represents a berth/wharf/pier where vessels dock
    """
    __tablename__ = "berths"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # Berth identification
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)  # Unique berth code (e.g., "B1", "TERM-A")
    description = Column(Text, nullable=True)
    berth_type = Column(SQLEnum(BerthType), nullable=False, index=True)

    # Physical specifications
    length = Column(Float, nullable=True)  # Berth length (meters)
    depth = Column(Float, nullable=True)  # Water depth (meters)
    max_draft = Column(Float, nullable=True)  # Maximum vessel draft allowed (meters)
    max_dwt = Column(Float, nullable=True)  # Maximum deadweight tonnage
    max_loa = Column(Float, nullable=True)  # Maximum length overall (meters)

    # Capacity & equipment
    loading_rate = Column(Float, nullable=True)  # Design loading rate (tons/hour)
    unloading_rate = Column(Float, nullable=True)  # Design unloading rate (tons/hour)
    storage_capacity = Column(Float, nullable=True)  # Associated storage capacity (tons)
    num_shiploaders = Column(Integer, default=0, nullable=False)
    num_conveyors = Column(Integer, default=0, nullable=False)
    num_cranes = Column(Integer, default=0, nullable=False)

    # Location
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)

    # Operational status
    status = Column(SQLEnum(BerthStatus), default=BerthStatus.AVAILABLE, nullable=False, index=True)
    current_vessel_id = Column(UUID(as_uuid=True), nullable=True)  # Currently berthed vessel

    # Availability schedule
    available_from = Column(DateTime(timezone=True), nullable=True)
    available_until = Column(DateTime(timezone=True), nullable=True)

    # Commodities handled
    commodities = Column(JSONB, default=list, nullable=False)
    # Example: ["soybean", "corn", "wheat", "sugar"]

    # Additional information
    notes = Column(Text, nullable=True)
    restrictions = Column(Text, nullable=True)  # Operational restrictions

    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    site = relationship("Site", back_populates="berths")
    current_vessels = relationship("Vessel", foreign_keys="Vessel.current_berth_id", back_populates="current_berth")
    loading_operations = relationship("LoadingOperation", back_populates="berth", cascade="all, delete-orphan")
    equipment = relationship("PortEquipment", back_populates="berth", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Berth {self.code} - {self.name}>"
