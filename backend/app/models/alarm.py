"""
Alarm models - Definitions and Events
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class AlarmSeverity(str, enum.Enum):
    """Alarm severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlarmType(str, enum.Enum):
    """Alarm types"""
    HIGH_LIMIT = "high_limit"
    LOW_LIMIT = "low_limit"
    HIGH_HIGH_LIMIT = "high_high_limit"
    LOW_LOW_LIMIT = "low_low_limit"
    RATE_OF_CHANGE = "rate_of_change"
    DEVIATION = "deviation"
    PREDICTIVE = "predictive"
    CUSTOM = "custom"


class AlarmState(str, enum.Enum):
    """Alarm states"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    CLEARED = "cleared"


class AlarmDefinition(Base):
    """
    Alarm Definition - Configuration for alarms
    """
    __tablename__ = "alarm_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Alarm configuration
    alarm_type = Column(SQLEnum(AlarmType), nullable=False)
    severity = Column(SQLEnum(AlarmSeverity), nullable=False, index=True)

    # Thresholds
    high_limit = Column(Float, nullable=True)
    low_limit = Column(Float, nullable=True)
    high_high_limit = Column(Float, nullable=True)
    low_low_limit = Column(Float, nullable=True)
    setpoint = Column(Float, nullable=True)
    deviation_limit = Column(Float, nullable=True)
    deadband = Column(Float, nullable=True)

    # Timing
    delay_seconds = Column(Float, default=0, nullable=False)  # Delay before triggering

    # Notification settings
    enable_email = Column(Boolean, default=False, nullable=False)
    enable_sms = Column(Boolean, default=False, nullable=False)
    notification_recipients = Column(JSONB, default=list, nullable=False)  # List of emails/phones

    # Additional settings
    settings = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tag = relationship("Tag", back_populates="alarm_definitions")
    events = relationship("AlarmEvent", back_populates="definition", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AlarmDefinition {self.name} ({self.severity.value})>"


class AlarmEvent(Base):
    """
    Alarm Event - Instance of an alarm being triggered
    """
    __tablename__ = "alarm_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    definition_id = Column(UUID(as_uuid=True), ForeignKey("alarm_definitions.id", ondelete="CASCADE"), nullable=False, index=True)

    # State
    state = Column(SQLEnum(AlarmState), default=AlarmState.ACTIVE, nullable=False, index=True)

    # Values at trigger
    trigger_value = Column(Float, nullable=True)
    trigger_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Acknowledgment
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    acknowledgment_comment = Column(Text, nullable=True)

    # Clearing
    cleared_at = Column(DateTime(timezone=True), nullable=True)
    clear_value = Column(Float, nullable=True)

    # Duration
    duration_seconds = Column(Float, nullable=True)

    # Additional data
    event_metadata = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    definition = relationship("AlarmDefinition", back_populates="events")

    def __repr__(self):
        return f"<AlarmEvent {self.id} ({self.state.value})>"
