"""
SmartPort - Vessel Model

Represents vessels/ships that dock at the port.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Float, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base


class VesselType(str, enum.Enum):
    """Types of vessels"""
    CONTAINER_SHIP = "container_ship"
    BULK_CARRIER = "bulk_carrier"
    TANKER = "tanker"
    GENERAL_CARGO = "general_cargo"
    RO_RO = "ro_ro"
    CRUISE_SHIP = "cruise_ship"
    FERRY = "ferry"
    TUGBOAT = "tugboat"
    OTHER = "other"


class VesselStatus(str, enum.Enum):
    """Current status of a vessel"""
    APPROACHING = "approaching"
    ANCHORED = "anchored"
    BERTHED = "berthed"
    LOADING = "loading"
    UNLOADING = "unloading"
    DEPARTING = "departing"
    DEPARTED = "departed"


class Vessel(Base):
    """Vessel model for ships visiting the port"""
    __tablename__ = "vessels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identification
    name = Column(String(200), nullable=False, index=True)
    imo = Column(String(20), nullable=False, unique=True, index=True)  # International Maritime Organization number
    mmsi = Column(String(20), nullable=True, unique=True)  # Maritime Mobile Service Identity
    call_sign = Column(String(20), nullable=True)
    flag = Column(String(100), nullable=True)  # Country of registration

    # Classification
    vessel_type = Column(SQLEnum(VesselType), nullable=False, index=True)
    status = Column(SQLEnum(VesselStatus), nullable=False, default=VesselStatus.APPROACHING, index=True)

    # Physical Specifications
    loa = Column(Float, nullable=False)  # Length Overall (meters)
    beam = Column(Float, nullable=False)  # Beam width (meters)
    draft = Column(Float, nullable=False)  # Current draft depth (meters)
    max_draft = Column(Float, nullable=True)  # Maximum draft depth (meters)
    gross_tonnage = Column(Float, nullable=True)  # Gross tonnage (GT)
    deadweight_tonnage = Column(Float, nullable=True)  # Deadweight tonnage (DWT)

    # Capacity
    capacity_teu = Column(Integer, nullable=True)  # Twenty-foot Equivalent Unit (for container ships)
    capacity_passengers = Column(Integer, nullable=True)  # Passenger capacity
    capacity_vehicles = Column(Integer, nullable=True)  # Vehicle capacity (for RoRo)
    capacity_cubic_meters = Column(Float, nullable=True)  # Cargo capacity in cubic meters

    # Scheduling
    eta = Column(DateTime(timezone=True), nullable=True, index=True)  # Estimated Time of Arrival
    ata = Column(DateTime(timezone=True), nullable=True)  # Actual Time of Arrival
    etd = Column(DateTime(timezone=True), nullable=True)  # Estimated Time of Departure
    atd = Column(DateTime(timezone=True), nullable=True)  # Actual Time of Departure

    # Location
    last_latitude = Column(Float, nullable=True)
    last_longitude = Column(Float, nullable=True)
    last_position_update = Column(DateTime(timezone=True), nullable=True)
    heading = Column(Float, nullable=True)  # Compass heading in degrees
    speed_knots = Column(Float, nullable=True)  # Current speed in knots

    # Voyage Information
    origin_port = Column(String(200), nullable=True)
    destination_port = Column(String(200), nullable=True)
    voyage_number = Column(String(50), nullable=True)

    # Operator Information
    owner = Column(String(200), nullable=True)
    operator = Column(String(200), nullable=True)
    agent = Column(String(200), nullable=True)

    # Metadata
    notes = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    current_berth = relationship("Berth", foreign_keys="Berth.current_vessel_id", back_populates="current_vessel")
    operations = relationship("PortOperation", back_populates="vessel", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Vessel {self.imo} - {self.name} ({self.vessel_type.value})>"

    @property
    def is_berthed(self) -> bool:
        """Check if vessel is currently berthed"""
        return self.status in [VesselStatus.BERTHED, VesselStatus.LOADING, VesselStatus.UNLOADING]

    @property
    def port_time_hours(self) -> Optional[float]:
        """Calculate time spent in port (hours)"""
        if self.ata and not self.atd:
            duration = datetime.utcnow() - self.ata
            return duration.total_seconds() / 3600
        elif self.ata and self.atd:
            duration = self.atd - self.ata
            return duration.total_seconds() / 3600
        return None

    @property
    def is_delayed(self) -> bool:
        """Check if vessel arrival/departure is delayed"""
        if self.eta and not self.ata:
            return datetime.utcnow() > self.eta
        if self.etd and not self.atd:
            return datetime.utcnow() > self.etd
        return False

    def update_position(self, latitude: float, longitude: float, heading: Optional[float] = None, speed: Optional[float] = None):
        """Update vessel position"""
        self.last_latitude = latitude
        self.last_longitude = longitude
        self.last_position_update = datetime.utcnow()
        if heading is not None:
            self.heading = heading
        if speed is not None:
            self.speed_knots = speed
