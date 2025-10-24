"""
SmartPort Models - Port-specific domain models
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class VesselType(str, enum.Enum):
    """Types of vessels"""
    CONTAINER = "container"
    BULK_CARRIER = "bulk_carrier"
    TANKER = "tanker"
    RO_RO = "ro_ro"
    GENERAL_CARGO = "general_cargo"
    CRUISE = "cruise"


class BerthStatus(str, enum.Enum):
    """Berth availability status"""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"


class Berth(Base):
    """
    Port Berth - Docking location for vessels
    """
    __tablename__ = "smartport_berths"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    name = Column(String(100), nullable=False, index=True)
    berth_number = Column(String(50), nullable=False)
    status = Column(SQLEnum(BerthStatus), default=BerthStatus.AVAILABLE, nullable=False, index=True)

    # Specifications
    max_vessel_length_m = Column(Float, nullable=True)
    max_vessel_width_m = Column(Float, nullable=True)
    max_draft_m = Column(Float, nullable=True)
    max_tonnage = Column(Integer, nullable=True)

    # Equipment
    has_crane = Column(Boolean, default=False)
    crane_capacity_tons = Column(Float, nullable=True)
    number_of_cranes = Column(Integer, default=0)

    # Utilities
    has_power_supply = Column(Boolean, default=True)
    has_water_supply = Column(Boolean, default=True)
    has_fuel_supply = Column(Boolean, default=False)

    # Additional data
    settings = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    site = relationship("Site")
    vessel_visits = relationship("VesselVisit", back_populates="berth")

    def __repr__(self):
        return f"<Berth {self.name} ({self.status.value})>"


class VesselVisit(Base):
    """
    Vessel Visit - Record of vessel docking at port
    """
    __tablename__ = "smartport_vessel_visits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)
    berth_id = Column(UUID(as_uuid=True), ForeignKey("smartport_berths.id", ondelete="SET NULL"), nullable=True, index=True)

    # Vessel information
    vessel_name = Column(String(255), nullable=False, index=True)
    vessel_type = Column(SQLEnum(VesselType), nullable=False, index=True)
    imo_number = Column(String(20), nullable=True, index=True)
    flag = Column(String(100), nullable=True)
    gross_tonnage = Column(Integer, nullable=True)
    length_m = Column(Float, nullable=True)
    width_m = Column(Float, nullable=True)
    draft_m = Column(Float, nullable=True)

    # Visit details
    arrival_time = Column(DateTime(timezone=True), nullable=False, index=True)
    departure_time = Column(DateTime(timezone=True), nullable=True, index=True)
    estimated_departure = Column(DateTime(timezone=True), nullable=True)

    # Cargo information
    cargo_type = Column(String(100), nullable=True)
    cargo_weight_tons = Column(Float, nullable=True)
    containers_loaded = Column(Integer, default=0)
    containers_unloaded = Column(Integer, default=0)

    # Operations
    is_loading = Column(Boolean, default=False)
    is_unloading = Column(Boolean, default=False)
    is_bunkering = Column(Boolean, default=False)

    # Performance metrics
    turnaround_time_hours = Column(Float, nullable=True)  # Time from arrival to departure
    berthing_time_hours = Column(Float, nullable=True)  # Time from mooring to unmooring
    cargo_handling_time_hours = Column(Float, nullable=True)

    # Additional data
    notes = Column(Text, nullable=True)
    visit_metadata = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    site = relationship("Site")
    berth = relationship("Berth", back_populates="vessel_visits")

    def __repr__(self):
        return f"<VesselVisit {self.vessel_name} @ {self.berth_id}>"


class PortKPI(Base):
    """
    Port KPI Metrics - Key Performance Indicators for port operations
    """
    __tablename__ = "smartport_kpis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # hourly, daily, weekly, monthly

    # Vessel metrics
    total_vessel_visits = Column(Integer, default=0)
    average_turnaround_time_hours = Column(Float, nullable=True)
    average_waiting_time_hours = Column(Float, nullable=True)
    berth_occupancy_rate = Column(Float, nullable=True)  # Percentage

    # Cargo metrics
    total_cargo_handled_tons = Column(Float, default=0)
    total_containers_handled = Column(Integer, default=0)
    average_cargo_handling_rate_tons_per_hour = Column(Float, nullable=True)

    # Operational metrics
    crane_utilization_rate = Column(Float, nullable=True)  # Percentage
    equipment_availability = Column(Float, nullable=True)  # Percentage
    labor_productivity = Column(Float, nullable=True)

    # Financial metrics
    revenue = Column(Float, nullable=True)
    cost = Column(Float, nullable=True)

    # Environmental metrics
    energy_consumption_kwh = Column(Float, nullable=True)
    carbon_emissions_tons = Column(Float, nullable=True)

    # Additional metrics
    custom_metrics = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    site = relationship("Site")

    def __repr__(self):
        return f"<PortKPI {self.period_start} to {self.period_end}>"
