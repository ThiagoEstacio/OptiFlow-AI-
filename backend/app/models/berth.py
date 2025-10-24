"""
SmartPort - Berth Model

Represents a berth (docking position) in the port.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base


class BerthType(str, enum.Enum):
    """Types of berths available in the port"""
    CONTAINER = "container"
    BULK = "bulk"
    GENERAL_CARGO = "general_cargo"
    RO_RO = "ro_ro"
    TANKER = "tanker"
    CRUISE = "cruise"


class BerthStatus(str, enum.Enum):
    """Current status of a berth"""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"
    UNAVAILABLE = "unavailable"


class Berth(Base):
    """Berth model for port docking positions"""
    __tablename__ = "berths"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Information
    name = Column(String(100), nullable=False, unique=True, index=True)
    code = Column(String(20), nullable=False, unique=True)
    berth_type = Column(SQLEnum(BerthType), nullable=False, index=True)
    status = Column(SQLEnum(BerthStatus), nullable=False, default=BerthStatus.AVAILABLE, index=True)

    # Physical Specifications
    max_loa = Column(Float, nullable=False)  # Maximum Length Overall (meters)
    max_beam = Column(Float, nullable=False)  # Maximum beam width (meters)
    max_draft = Column(Float, nullable=False)  # Maximum draft depth (meters)
    max_displacement = Column(Float, nullable=True)  # Maximum vessel displacement (tonnes)

    # Capabilities
    max_crane_capacity = Column(Float, nullable=True)  # Maximum crane capacity (tonnes)
    number_of_cranes = Column(Integer, default=0)
    has_shore_power = Column(Boolean, default=False)
    has_fresh_water = Column(Boolean, default=False)
    has_bunker_facility = Column(Boolean, default=False)

    # Location (GeoJSON coordinates)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Current Occupation
    current_vessel_id = Column(UUID(as_uuid=True), ForeignKey("vessels.id"), nullable=True)
    occupation_start = Column(DateTime(timezone=True), nullable=True)
    estimated_departure = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    current_vessel = relationship("Vessel", foreign_keys=[current_vessel_id], back_populates="current_berth")
    operations = relationship("PortOperation", back_populates="berth", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Berth {self.code} - {self.name} ({self.status.value})>"

    @property
    def is_available(self) -> bool:
        """Check if berth is available for new vessel"""
        return self.status == BerthStatus.AVAILABLE and self.current_vessel_id is None

    @property
    def occupancy_duration_hours(self) -> Optional[float]:
        """Calculate current occupancy duration in hours"""
        if self.occupation_start and self.status == BerthStatus.OCCUPIED:
            duration = datetime.utcnow() - self.occupation_start
            return duration.total_seconds() / 3600
        return None

    def can_accommodate_vessel(self, vessel_loa: float, vessel_beam: float, vessel_draft: float) -> bool:
        """Check if berth can accommodate a vessel with given dimensions"""
        return (
            self.is_available and
            vessel_loa <= self.max_loa and
            vessel_beam <= self.max_beam and
            vessel_draft <= self.max_draft
        )
