"""
Tag model - Process variables (temperature, pressure, flow, etc.)
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Float, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class TagDataType(str, enum.Enum):
    """Tag data types"""
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    DOUBLE = "double"


class TagCategory(str, enum.Enum):
    """Tag categories"""
    PROCESS = "process"
    ENERGY = "energy"
    QUALITY = "quality"
    PRODUCTION = "production"
    MAINTENANCE = "maintenance"
    ALARM = "alarm"
    SETPOINT = "setpoint"
    STATUS = "status"


class Tag(Base):
    """
    Tag model - represents a process variable
    """
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Protocol-specific address
    # For OPC UA: node_id (e.g., "ns=2;s=Temperature.Motor1")
    # For Modbus: register_address (e.g., "holding:1000")
    # For MQTT: topic (e.g., "sensors/temperature/motor1")
    address = Column(String(500), nullable=False)

    # Data type and unit
    data_type = Column(SQLEnum(TagDataType), nullable=False)
    unit = Column(String(50), nullable=True)  # °C, bar, m³/h, kW, etc.
    category = Column(SQLEnum(TagCategory), default=TagCategory.PROCESS, nullable=False, index=True)

    # Engineering limits
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    engineering_min = Column(Float, nullable=True)
    engineering_max = Column(Float, nullable=True)

    # Scaling (raw_value * scale + offset = engineering_value)
    scale = Column(Float, default=1.0, nullable=False)
    offset = Column(Float, default=0.0, nullable=False)

    # Sampling configuration
    scan_rate_ms = Column(Integer, default=1000, nullable=False)  # milliseconds
    deadband = Column(Float, nullable=True)  # Only log if change > deadband

    # Quality flags
    enable_quality_check = Column(Boolean, default=True, nullable=False)

    # Latest value (cached for quick access)
    last_value = Column(String(100), nullable=True)
    last_quality = Column(String(20), nullable=True)
    last_timestamp = Column(DateTime(timezone=True), nullable=True)

    # Statistics (updated periodically)
    data_points_count = Column(Integer, default=0, nullable=False)

    # Additional settings
    settings = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    device = relationship("Device", back_populates="tags")
    alarm_definitions = relationship("AlarmDefinition", back_populates="tag", cascade="all, delete-orphan")
    annotations = relationship("Annotation", back_populates="tag", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tag {self.name} ({self.unit})>"
