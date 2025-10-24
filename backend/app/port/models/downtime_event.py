"""
Downtime Event model - Tracking downtime/delays during loading operations
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class DowntimeCategory(str, enum.Enum):
    """Downtime categories"""
    WEATHER = "weather"
    EQUIPMENT_FAILURE = "equipment_failure"
    MAINTENANCE = "maintenance"
    OPERATIONAL = "operational"
    POWER_OUTAGE = "power_outage"
    WAITING_VESSEL = "waiting_vessel"
    WAITING_CARGO = "waiting_cargo"
    SAFETY_INCIDENT = "safety_incident"
    SHIFT_CHANGE = "shift_change"
    OTHER = "other"


class DowntimeSeverity(str, enum.Enum):
    """Downtime severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DowntimeEvent(Base):
    """
    Downtime Event model - represents downtime/delay events during operations
    """
    __tablename__ = "downtime_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # References
    loading_operation_id = Column(UUID(as_uuid=True), ForeignKey("loading_operations.id", ondelete="CASCADE"), nullable=True, index=True)
    device_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # OptiFlow device if applicable

    # Event info
    event_number = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(SQLEnum(DowntimeCategory), nullable=False, index=True)
    severity = Column(SQLEnum(DowntimeSeverity), default=DowntimeSeverity.MEDIUM, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Timing
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)  # Calculated when resolved

    # Impact
    cargo_loss_tons = Column(Float, default=0.0, nullable=False)
    cost_impact = Column(Float, nullable=True)  # In local currency
    productivity_impact_percentage = Column(Float, nullable=True)

    # Root cause analysis
    root_cause = Column(Text, nullable=True)
    contributing_factors = Column(JSONB, default=list, nullable=False)
    corrective_actions = Column(Text, nullable=True)
    preventive_actions = Column(Text, nullable=True)

    # Resolution
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_by = Column(String(200), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Equipment details (if equipment failure)
    equipment_name = Column(String(200), nullable=True)
    equipment_component = Column(String(200), nullable=True)
    failure_mode = Column(String(200), nullable=True)

    # Weather details (if weather-related)
    weather_conditions = Column(JSONB, default=dict, nullable=False)
    # Example: {"wind_speed": 45, "precipitation": true, "visibility": "poor"}

    # Additional info
    attachments = Column(JSONB, default=list, nullable=False)  # File paths/URLs
    metadata_json = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    site = relationship("Site", back_populates="downtime_events")
    loading_operation = relationship("LoadingOperation", back_populates="downtime_events")

    def __repr__(self):
        return f"<DowntimeEvent {self.event_number} - {self.category.value} ({self.duration_minutes}min)>"
