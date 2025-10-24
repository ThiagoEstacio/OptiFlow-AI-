"""
Vessel model - Ships and vessels for port operations
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class VesselType(str, enum.Enum):
    """Types of vessels"""
    BULK_CARRIER = "bulk_carrier"
    CONTAINER = "container"
    TANKER = "tanker"
    GENERAL_CARGO = "general_cargo"
    RORO = "roro"  # Roll-on/Roll-off
    BREAKBULK = "breakbulk"
    OTHER = "other"


class VesselStatus(str, enum.Enum):
    """Vessel operational status"""
    SCHEDULED = "scheduled"  # Scheduled to arrive
    APPROACHING = "approaching"  # En route to port
    ANCHORED = "anchored"  # Waiting at anchorage
    BERTHING = "berthing"  # Moving to berth
    BERTHED = "berthed"  # At berth, ready for operation
    LOADING = "loading"  # Loading cargo
    UNLOADING = "unloading"  # Unloading cargo
    COMPLETED = "completed"  # Operation completed
    DEPARTING = "departing"  # Leaving berth
    DEPARTED = "departed"  # Left port
    CANCELLED = "cancelled"  # Visit cancelled


class Vessel(Base):
    """
    Vessel model - represents ships/vessels visiting the port
    """
    __tablename__ = "vessels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # Vessel identification
    name = Column(String(255), nullable=False, index=True)
    imo_number = Column(String(20), nullable=False, unique=True, index=True)  # IMO ship identification number
    call_sign = Column(String(20), nullable=True, index=True)
    mmsi = Column(String(20), nullable=True)  # Maritime Mobile Service Identity

    # Vessel information
    vessel_type = Column(SQLEnum(VesselType), nullable=False, index=True)
    flag = Column(String(100), nullable=True)  # Country of registration
    classification = Column(String(100), nullable=True)  # Classification society

    # Vessel specifications
    dwt = Column(Float, nullable=True)  # Deadweight tonnage (tons)
    grt = Column(Float, nullable=True)  # Gross registered tonnage
    nrt = Column(Float, nullable=True)  # Net registered tonnage
    length = Column(Float, nullable=True)  # Length overall (meters)
    beam = Column(Float, nullable=True)  # Beam/width (meters)
    draft = Column(Float, nullable=True)  # Draft (meters)
    capacity = Column(Float, nullable=True)  # Cargo capacity (depends on vessel type)

    # Ownership & operation
    owner = Column(String(255), nullable=True)
    operator = Column(String(255), nullable=True)
    agent = Column(String(255), nullable=True)  # Port agent

    # Current status
    status = Column(SQLEnum(VesselStatus), default=VesselStatus.SCHEDULED, nullable=False, index=True)
    current_berth_id = Column(UUID(as_uuid=True), ForeignKey("berths.id", ondelete="SET NULL"), nullable=True, index=True)

    # Schedule
    eta = Column(DateTime(timezone=True), nullable=True)  # Estimated time of arrival
    ata = Column(DateTime(timezone=True), nullable=True)  # Actual time of arrival
    etb = Column(DateTime(timezone=True), nullable=True)  # Estimated time of berthing
    atb = Column(DateTime(timezone=True), nullable=True)  # Actual time of berthing
    etc = Column(DateTime(timezone=True), nullable=True)  # Estimated time of completion
    atc = Column(DateTime(timezone=True), nullable=True)  # Actual time of completion
    etd = Column(DateTime(timezone=True), nullable=True)  # Estimated time of departure
    atd = Column(DateTime(timezone=True), nullable=True)  # Actual time of departure

    # Additional information
    voyage_number = Column(String(50), nullable=True)
    previous_port = Column(String(100), nullable=True)
    next_port = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    site = relationship("Site", back_populates="vessels")
    current_berth = relationship("Berth", foreign_keys=[current_berth_id], back_populates="current_vessels")
    loading_operations = relationship("LoadingOperation", back_populates="vessel", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Vessel {self.name} (IMO: {self.imo_number})>"
