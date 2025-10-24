"""
Vessel model - Ship/Vessel for port operations
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class VesselType(str, enum.Enum):
    """Vessel types"""
    BULK_CARRIER = "bulk_carrier"
    CONTAINER_SHIP = "container_ship"
    TANKER = "tanker"
    RO_RO = "ro_ro"
    GENERAL_CARGO = "general_cargo"
    OTHER = "other"


class VesselStatus(str, enum.Enum):
    """Vessel operational status"""
    APPROACHING = "approaching"
    BERTHED = "berthed"
    LOADING = "loading"
    UNLOADING = "unloading"
    LOADING_COMPLETE = "loading_complete"
    DEPARTED = "departed"
    CANCELLED = "cancelled"


class Vessel(Base):
    """
    Vessel model - represents ships/vessels in port operations
    """
    __tablename__ = "vessels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    imo_number = Column(String(20), unique=True, nullable=True, index=True)  # International Maritime Organization number
    mmsi_number = Column(String(20), nullable=True)  # Maritime Mobile Service Identity
    call_sign = Column(String(20), nullable=True)
    flag_country = Column(String(100), nullable=True)

    # Vessel specifications
    vessel_type = Column(SQLEnum(VesselType), nullable=False, index=True)
    length_overall = Column(Float, nullable=True)  # meters
    beam = Column(Float, nullable=True)  # meters
    draft = Column(Float, nullable=True)  # meters
    deadweight_tonnage = Column(Integer, nullable=True)  # DWT in tons
    gross_tonnage = Column(Integer, nullable=True)  # GT

    # Operation info
    status = Column(SQLEnum(VesselStatus), default=VesselStatus.APPROACHING, nullable=False, index=True)
    current_berth_id = Column(UUID(as_uuid=True), ForeignKey("berths.id", ondelete="SET NULL"), nullable=True)

    # Cargo info
    cargo_type = Column(String(100), nullable=True)
    cargo_quantity_planned = Column(Float, nullable=True)  # tons
    cargo_quantity_actual = Column(Float, nullable=True)  # tons

    # Scheduling
    eta = Column(DateTime(timezone=True), nullable=True)  # Estimated Time of Arrival
    ata = Column(DateTime(timezone=True), nullable=True)  # Actual Time of Arrival
    etd = Column(DateTime(timezone=True), nullable=True)  # Estimated Time of Departure
    atd = Column(DateTime(timezone=True), nullable=True)  # Actual Time of Departure
    berthing_time = Column(DateTime(timezone=True), nullable=True)
    unberthing_time = Column(DateTime(timezone=True), nullable=True)

    # Loading times
    loading_start_time = Column(DateTime(timezone=True), nullable=True)
    loading_end_time = Column(DateTime(timezone=True), nullable=True)
    loading_duration_minutes = Column(Integer, nullable=True)

    # Performance metrics
    average_loading_rate = Column(Float, nullable=True)  # tons/hour
    peak_loading_rate = Column(Float, nullable=True)  # tons/hour
    demurrage_hours = Column(Float, default=0.0, nullable=False)  # Hours beyond allowed time
    weather_delay_hours = Column(Float, default=0.0, nullable=False)
    equipment_delay_hours = Column(Float, default=0.0, nullable=False)
    other_delay_hours = Column(Float, default=0.0, nullable=False)

    # Additional info
    agent_company = Column(String(200), nullable=True)
    shipper_company = Column(String(200), nullable=True)
    receiver_company = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)

    # Metadata
    metadata_json = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    site = relationship("Site", back_populates="vessels")
    current_berth = relationship("Berth", foreign_keys=[current_berth_id], back_populates="current_vessels")
    loading_operations = relationship("LoadingOperation", back_populates="vessel", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Vessel {self.name} ({self.imo_number}) - {self.status.value}>"
