"""
Loading Operation model - Cargo loading/unloading operations
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class OperationType(str, enum.Enum):
    """Type of operation"""
    LOADING = "loading"  # Loading cargo onto vessel
    UNLOADING = "unloading"  # Unloading cargo from vessel
    TRANSSHIPMENT = "transshipment"  # Transfer between vessels


class OperationStatus(str, enum.Enum):
    """Status of loading operation"""
    PLANNED = "planned"  # Operation planned
    READY = "ready"  # Ready to start (vessel berthed, equipment ready)
    IN_PROGRESS = "in_progress"  # Operation in progress
    PAUSED = "paused"  # Temporarily paused
    DELAYED = "delayed"  # Delayed from schedule
    COMPLETED = "completed"  # Successfully completed
    CANCELLED = "cancelled"  # Cancelled


class CommodityType(str, enum.Enum):
    """Types of commodities"""
    SOYBEAN = "soybean"
    CORN = "corn"
    WHEAT = "wheat"
    SUGAR = "sugar"
    SOYBEAN_MEAL = "soybean_meal"
    FERTILIZER = "fertilizer"
    IRON_ORE = "iron_ore"
    COAL = "coal"
    PETROLEUM = "petroleum"
    CHEMICALS = "chemicals"
    CONTAINER = "container"
    GENERAL_CARGO = "general_cargo"
    OTHER = "other"


class Cargo(Base):
    """
    Cargo model - represents cargo to be loaded/unloaded
    """
    __tablename__ = "cargos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loading_operation_id = Column(UUID(as_uuid=True), ForeignKey("loading_operations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Cargo details
    commodity = Column(SQLEnum(CommodityType), nullable=False, index=True)
    commodity_grade = Column(String(100), nullable=True)  # Grade/quality (e.g., "Grade A", "Premium")
    description = Column(Text, nullable=True)

    # Quantity
    planned_quantity = Column(Float, nullable=False)  # Planned quantity (tons)
    actual_quantity = Column(Float, nullable=True)  # Actual loaded/unloaded (tons)
    unit = Column(String(20), default="tons", nullable=False)

    # Origin & destination
    origin = Column(String(255), nullable=True)  # Origin location
    destination = Column(String(255), nullable=True)  # Destination location
    shipper = Column(String(255), nullable=True)  # Shipper/exporter
    consignee = Column(String(255), nullable=True)  # Consignee/importer

    # Quality & specifications
    specifications = Column(JSONB, default=dict, nullable=False)
    # Example: {"moisture": 14.5, "protein": 35.2, "impurities": 1.2}

    # Additional information
    bl_number = Column(String(100), nullable=True)  # Bill of lading number
    customs_reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # Metadata
    settings = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    loading_operation = relationship("LoadingOperation", back_populates="cargos")

    def __repr__(self):
        return f"<Cargo {self.commodity.value} - {self.planned_quantity}{self.unit}>"


class LoadingOperation(Base):
    """
    Loading Operation model - represents a loading/unloading operation
    """
    __tablename__ = "loading_operations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)
    vessel_id = Column(UUID(as_uuid=True), ForeignKey("vessels.id", ondelete="CASCADE"), nullable=False, index=True)
    berth_id = Column(UUID(as_uuid=True), ForeignKey("berths.id", ondelete="CASCADE"), nullable=False, index=True)

    # Operation details
    operation_type = Column(SQLEnum(OperationType), nullable=False, index=True)
    operation_number = Column(String(100), nullable=False, unique=True, index=True)  # Unique operation ID
    status = Column(SQLEnum(OperationStatus), default=OperationStatus.PLANNED, nullable=False, index=True)

    # Schedule
    planned_start = Column(DateTime(timezone=True), nullable=False)
    planned_end = Column(DateTime(timezone=True), nullable=False)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)

    # Performance metrics
    planned_rate = Column(Float, nullable=True)  # Planned loading rate (tons/hour)
    actual_rate = Column(Float, nullable=True)  # Actual average rate (tons/hour)
    current_rate = Column(Float, nullable=True)  # Current instantaneous rate (tons/hour)

    total_planned_quantity = Column(Float, nullable=False)  # Total planned (tons)
    total_actual_quantity = Column(Float, default=0.0, nullable=False)  # Total loaded/unloaded (tons)

    efficiency = Column(Float, nullable=True)  # Operational efficiency (%)
    downtime_hours = Column(Float, default=0.0, nullable=False)  # Total downtime (hours)
    working_hours = Column(Float, default=0.0, nullable=False)  # Actual working hours

    # Delay tracking
    is_delayed = Column(Boolean, default=False, nullable=False)
    delay_reason = Column(Text, nullable=True)
    delay_minutes = Column(Float, default=0.0, nullable=False)

    # Equipment used
    equipment_used = Column(JSONB, default=list, nullable=False)
    # Example: ["TC4515", "EL4511", "SL01"]

    # Additional information
    notes = Column(Text, nullable=True)
    weather_conditions = Column(String(255), nullable=True)
    shift_supervisor = Column(String(255), nullable=True)

    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    site = relationship("Site", back_populates="loading_operations")
    vessel = relationship("Vessel", back_populates="loading_operations")
    berth = relationship("Berth", back_populates="loading_operations")
    cargos = relationship("Cargo", back_populates="loading_operation", cascade="all, delete-orphan")
    events = relationship("OperationEvent", back_populates="loading_operation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LoadingOperation {self.operation_number} - {self.status.value}>"


class OperationEvent(Base):
    """
    Operation Event model - tracks events during loading operations
    """
    __tablename__ = "operation_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loading_operation_id = Column(UUID(as_uuid=True), ForeignKey("loading_operations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    # Examples: "start", "pause", "resume", "delay", "equipment_change", "weather_delay", "complete"

    event_time = Column(DateTime(timezone=True), nullable=False, index=True)
    description = Column(Text, nullable=False)

    # Event data
    event_data = Column(JSONB, default=dict, nullable=False)
    # Example: {"reason": "Equipment maintenance", "equipment_id": "TC4515", "duration_minutes": 45}

    # User who recorded the event
    user_id = Column(UUID(as_uuid=True), nullable=True)
    user_name = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    loading_operation = relationship("LoadingOperation", back_populates="events")

    def __repr__(self):
        return f"<OperationEvent {self.event_type} at {self.event_time}>"
