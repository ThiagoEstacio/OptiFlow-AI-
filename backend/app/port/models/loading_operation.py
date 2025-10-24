"""
Loading Operation model - Individual loading operations for vessels
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class LoadingStatus(str, enum.Enum):
    """Loading operation status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class LoadingOperation(Base):
    """
    Loading Operation model - represents individual loading operations
    """
    __tablename__ = "loading_operations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # References
    vessel_id = Column(UUID(as_uuid=True), ForeignKey("vessels.id", ondelete="CASCADE"), nullable=False, index=True)
    berth_id = Column(UUID(as_uuid=True), ForeignKey("berths.id", ondelete="SET NULL"), nullable=True, index=True)
    commodity_id = Column(UUID(as_uuid=True), ForeignKey("commodities.id", ondelete="SET NULL"), nullable=True)
    route_id = Column(UUID(as_uuid=True), ForeignKey("loading_routes.id", ondelete="SET NULL"), nullable=True)

    # Basic info
    operation_number = Column(String(100), nullable=False, unique=True, index=True)
    status = Column(SQLEnum(LoadingStatus), default=LoadingStatus.PLANNED, nullable=False, index=True)

    # Planned quantities
    target_quantity = Column(Float, nullable=False)  # tons
    target_loading_rate = Column(Float, nullable=True)  # tons/hour
    estimated_duration_hours = Column(Float, nullable=True)

    # Actual quantities
    actual_quantity = Column(Float, default=0.0, nullable=False)  # tons
    actual_loading_rate = Column(Float, nullable=True)  # tons/hour
    actual_duration_minutes = Column(Integer, nullable=True)

    # Timing
    planned_start = Column(DateTime(timezone=True), nullable=True)
    planned_end = Column(DateTime(timezone=True), nullable=True)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)

    # Progress tracking
    progress_percentage = Column(Float, default=0.0, nullable=False)
    current_hold_number = Column(Integer, nullable=True)  # Current ship hold being loaded
    total_holds = Column(Integer, nullable=True)

    # Equipment used
    shiploader_ids = Column(ARRAY(String), default=list, nullable=False)
    conveyor_ids = Column(ARRAY(String), default=list, nullable=False)
    stacker_reclaimer_ids = Column(ARRAY(String), default=list, nullable=False)

    # Quality metrics
    cargo_quality_parameters = Column(JSONB, default=dict, nullable=False)
    # Example: {"moisture_content": 8.5, "iron_content": 62.3, "silica": 4.2}

    # Downtime tracking
    total_downtime_minutes = Column(Integer, default=0, nullable=False)
    weather_delay_minutes = Column(Integer, default=0, nullable=False)
    equipment_failure_minutes = Column(Integer, default=0, nullable=False)
    operational_delay_minutes = Column(Integer, default=0, nullable=False)
    other_delay_minutes = Column(Integer, default=0, nullable=False)

    # Efficiency metrics
    efficiency_percentage = Column(Float, nullable=True)  # Actual vs target
    productivity_tons_per_hour = Column(Float, nullable=True)
    equipment_utilization = Column(Float, nullable=True)  # percentage

    # Energy consumption (from OptiFlow devices)
    total_energy_kwh = Column(Float, nullable=True)
    energy_per_ton = Column(Float, nullable=True)  # kWh/ton

    # Additional info
    notes = Column(Text, nullable=True)
    metadata_json = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    site = relationship("Site", back_populates="loading_operations")
    vessel = relationship("Vessel", back_populates="loading_operations")
    berth = relationship("Berth", back_populates="loading_operations")
    commodity = relationship("Commodity", back_populates="loading_operations")
    route = relationship("LoadingRoute", back_populates="loading_operations")
    downtime_events = relationship("DowntimeEvent", back_populates="loading_operation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LoadingOperation {self.operation_number} - {self.status.value}>"
