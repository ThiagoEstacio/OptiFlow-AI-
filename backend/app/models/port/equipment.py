"""
Port Equipment model - Port equipment (shiploaders, conveyors, cranes, etc.)
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Float, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class EquipmentType(str, enum.Enum):
    """Types of port equipment"""
    SHIPLOADER = "shiploader"  # Ship loading equipment
    CONVEYOR = "conveyor"  # Belt conveyor
    ELEVATOR = "elevator"  # Bucket elevator
    CRANE = "crane"  # Gantry/mobile crane
    STACKER = "stacker"  # Stacker for stockyard
    RECLAIMER = "reclaimer"  # Reclaimer for stockyard
    WEIGHING_SCALE = "weighing_scale"  # Weighing equipment
    DUST_SUPPRESSION = "dust_suppression"  # Dust control system
    HOPPER = "hopper"  # Receiving/discharge hopper
    OTHER = "other"


class EquipmentStatus(str, enum.Enum):
    """Equipment operational status"""
    OPERATING = "operating"  # Currently operating
    IDLE = "idle"  # Ready but not in use
    MAINTENANCE = "maintenance"  # Under maintenance
    FAULT = "fault"  # Faulty/error state
    OFFLINE = "offline"  # Offline/unavailable


class MaintenanceType(str, enum.Enum):
    """Type of maintenance"""
    PREVENTIVE = "preventive"  # Scheduled preventive maintenance
    PREDICTIVE = "predictive"  # AI-predicted maintenance
    CORRECTIVE = "corrective"  # Repair after failure
    INSPECTION = "inspection"  # Routine inspection


class PortEquipment(Base):
    """
    Port Equipment model - represents port handling equipment
    """
    __tablename__ = "port_equipment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)
    berth_id = Column(UUID(as_uuid=True), ForeignKey("berths.id", ondelete="SET NULL"), nullable=True, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True)
    # device_id links to the Device model for sensor data collection

    # Equipment identification
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)  # Unique equipment code (e.g., "TC4515", "SL01")
    equipment_type = Column(SQLEnum(EquipmentType), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Equipment specifications
    manufacturer = Column(String(255), nullable=True)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    year_manufactured = Column(Integer, nullable=True)
    year_installed = Column(Integer, nullable=True)

    # Performance specifications
    rated_capacity = Column(Float, nullable=True)  # Rated capacity (tons/hour or tons)
    max_capacity = Column(Float, nullable=True)  # Maximum capacity
    design_speed = Column(Float, nullable=True)  # Design speed (m/s for conveyors, cycles/hour for cranes)
    power_rating = Column(Float, nullable=True)  # Power rating (kW)

    # Current status
    status = Column(SQLEnum(EquipmentStatus), default=EquipmentStatus.IDLE, nullable=False, index=True)
    health_score = Column(Float, nullable=True)  # AI-predicted health score (0-100)
    failure_probability = Column(Float, nullable=True)  # AI-predicted failure probability (0-100)
    remaining_useful_life = Column(Integer, nullable=True)  # Predicted RUL (hours)

    # Operational metrics
    total_operating_hours = Column(Float, default=0.0, nullable=False)
    total_downtime_hours = Column(Float, default=0.0, nullable=False)
    total_throughput = Column(Float, default=0.0, nullable=False)  # Total material handled (tons)
    current_throughput = Column(Float, nullable=True)  # Current throughput (tons/hour)

    # Maintenance tracking
    last_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    next_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    maintenance_interval_hours = Column(Float, nullable=True)  # Maintenance interval (hours)

    # Alarm thresholds (for monitoring)
    alarm_thresholds = Column(JSONB, default=dict, nullable=False)
    # Example: {
    #   "temperature_high": 80,
    #   "vibration_high": 5.0,
    #   "current_high": 450,
    #   "efficiency_low": 75
    # }

    # Location
    location = Column(String(255), nullable=True)  # Physical location description
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)

    # Additional information
    notes = Column(Text, nullable=True)
    criticality = Column(String(20), nullable=True)  # "critical", "high", "medium", "low"

    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    site = relationship("Site", back_populates="port_equipment")
    berth = relationship("Berth", back_populates="equipment")
    device = relationship("Device")  # Sensor device for data collection
    maintenance_records = relationship("MaintenanceRecord", back_populates="equipment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PortEquipment {self.code} - {self.equipment_type.value}>"


class MaintenanceRecord(Base):
    """
    Maintenance Record model - tracks maintenance history
    """
    __tablename__ = "maintenance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(UUID(as_uuid=True), ForeignKey("port_equipment.id", ondelete="CASCADE"), nullable=False, index=True)

    # Maintenance details
    maintenance_type = Column(SQLEnum(MaintenanceType), nullable=False, index=True)
    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    actual_date = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_hours = Column(Float, nullable=True)

    # Work performed
    work_description = Column(Text, nullable=False)
    parts_replaced = Column(JSONB, default=list, nullable=False)
    # Example: [{"part": "Belt", "quantity": 1, "cost": 5000}]

    # Costs
    labor_cost = Column(Float, nullable=True)
    parts_cost = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)

    # Personnel
    technician_name = Column(String(255), nullable=True)
    supervisor_name = Column(String(255), nullable=True)

    # Findings & recommendations
    findings = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    next_maintenance_date = Column(DateTime(timezone=True), nullable=True)

    # Additional information
    notes = Column(Text, nullable=True)
    attachments = Column(JSONB, default=list, nullable=False)
    # Example: [{"filename": "report.pdf", "url": "s3://..."}]

    # Metadata
    settings = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    equipment = relationship("PortEquipment", back_populates="maintenance_records")

    def __repr__(self):
        return f"<MaintenanceRecord {self.maintenance_type.value} - {self.actual_date}>"
