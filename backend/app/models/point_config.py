"""
Point Configuration Models

Extended configuration for Points (Tags) including:
- Compression settings
- Historian configuration
- Advanced validation
- Templates support
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Float, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class CompressionType(str, enum.Enum):
    """Compression algorithm types"""
    NONE = "none"
    SWINGING_DOOR = "swinging_door"
    BOXCAR = "boxcar"
    DEADBAND = "deadband"


class HistorianType(str, enum.Enum):
    """Historian storage types"""
    INFLUXDB = "influxdb"
    TIMESCALEDB = "timescaledb"
    POSTGRESQL = "postgresql"
    NONE = "none"


class PointTemplate(Base):
    """
    Point Template - Reusable configuration for points

    Templates allow quick configuration of multiple points with common settings.
    Example templates: "Standard Temperature", "Standard Pressure", "Motor Status"
    """
    __tablename__ = "point_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Category and data type defaults
    category = Column(String(50), nullable=True)  # Links to TagCategory
    data_type = Column(String(50), nullable=True)  # Links to TagDataType

    # Default engineering settings
    unit = Column(String(50), nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    engineering_min = Column(Float, nullable=True)
    engineering_max = Column(Float, nullable=True)
    scale = Column(Float, default=1.0, nullable=True)
    offset = Column(Float, default=0.0, nullable=True)

    # Default sampling configuration
    scan_rate_ms = Column(Integer, default=1000, nullable=True)
    deadband = Column(Float, nullable=True)

    # Compression settings
    compression_enabled = Column(Boolean, default=False, nullable=False)
    compression_type = Column(SQLEnum(CompressionType), default=CompressionType.NONE, nullable=False)
    compression_config = Column(JSONB, default=dict, nullable=False)
    # Example compression_config for SwingingDoor:
    # {
    #   "deviation": 2.0,  # Maximum deviation from trend line
    #   "time_deadband_ms": 1000  # Minimum time between samples
    # }
    # Example compression_config for BoxCar:
    # {
    #   "time_window_ms": 60000,  # Time window for averaging (1 minute)
    #   "change_threshold": 0.5  # Minimum change to trigger storage
    # }

    # Historian settings
    historian_enabled = Column(Boolean, default=True, nullable=False)
    historian_type = Column(SQLEnum(HistorianType), default=HistorianType.INFLUXDB, nullable=False)
    historian_config = Column(JSONB, default=dict, nullable=False)
    # Example historian_config:
    # {
    #   "retention_days": 365,
    #   "measurement": "process_data",
    #   "field_name": "value",
    #   "tags": {"source": "plc"}
    # }

    # Alarm settings defaults
    enable_alarms = Column(Boolean, default=False, nullable=False)
    alarm_config = Column(JSONB, default=dict, nullable=False)
    # Example alarm_config:
    # {
    #   "high_high": {"enabled": true, "limit": 100, "priority": "critical"},
    #   "high": {"enabled": true, "limit": 90, "priority": "high"},
    #   "low": {"enabled": true, "limit": 10, "priority": "high"},
    #   "low_low": {"enabled": true, "limit": 0, "priority": "critical"}
    # }

    # Additional settings
    settings = Column(JSONB, default=dict, nullable=False)

    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    organization = relationship("Organization", backref="point_templates")

    def __repr__(self):
        return f"<PointTemplate {self.name}>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "data_type": self.data_type,
            "unit": self.unit,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "engineering_min": self.engineering_min,
            "engineering_max": self.engineering_max,
            "scale": self.scale,
            "offset": self.offset,
            "scan_rate_ms": self.scan_rate_ms,
            "deadband": self.deadband,
            "compression_enabled": self.compression_enabled,
            "compression_type": self.compression_type.value if self.compression_type else None,
            "compression_config": self.compression_config,
            "historian_enabled": self.historian_enabled,
            "historian_type": self.historian_type.value if self.historian_type else None,
            "historian_config": self.historian_config,
            "enable_alarms": self.enable_alarms,
            "alarm_config": self.alarm_config,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PointConfiguration(Base):
    """
    Point Configuration - Extended configuration for Tags

    This extends the Tag model with advanced features:
    - Data compression
    - Historian configuration
    - Template linkage
    """
    __tablename__ = "point_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("point_templates.id", ondelete="SET NULL"), nullable=True, index=True)

    # Compression settings (overrides template if set)
    compression_enabled = Column(Boolean, default=False, nullable=False)
    compression_type = Column(SQLEnum(CompressionType), default=CompressionType.NONE, nullable=False)
    compression_config = Column(JSONB, default=dict, nullable=False)

    # Compression statistics
    total_samples_received = Column(Integer, default=0, nullable=False)
    total_samples_stored = Column(Integer, default=0, nullable=False)
    compression_ratio = Column(Float, default=1.0, nullable=False)  # samples_received / samples_stored
    last_compressed_value = Column(Float, nullable=True)
    last_compressed_timestamp = Column(DateTime(timezone=True), nullable=True)

    # Historian settings
    historian_enabled = Column(Boolean, default=True, nullable=False)
    historian_type = Column(SQLEnum(HistorianType), default=HistorianType.INFLUXDB, nullable=False)
    historian_config = Column(JSONB, default=dict, nullable=False)

    # Historian statistics
    total_writes = Column(Integer, default=0, nullable=False)
    last_write_timestamp = Column(DateTime(timezone=True), nullable=True)
    write_errors = Column(Integer, default=0, nullable=False)
    last_write_error = Column(Text, nullable=True)

    # Advanced validation rules
    validation_rules = Column(JSONB, default=dict, nullable=False)
    # Example validation_rules:
    # {
    #   "rate_of_change": {"enabled": true, "max_per_second": 10.0},
    #   "range_check": {"enabled": true, "action": "reject"},  # reject or clamp
    #   "stuck_value": {"enabled": true, "max_same_count": 10}
    # }

    # Performance metrics
    avg_processing_time_ms = Column(Float, default=0.0, nullable=False)
    last_processing_time_ms = Column(Float, default=0.0, nullable=False)

    # Additional settings
    settings = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tag = relationship("Tag", backref="point_configuration", uselist=False)
    template = relationship("PointTemplate", backref="point_configurations")

    def __repr__(self):
        return f"<PointConfiguration tag_id={self.tag_id}>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "tag_id": str(self.tag_id),
            "template_id": str(self.template_id) if self.template_id else None,
            "compression_enabled": self.compression_enabled,
            "compression_type": self.compression_type.value if self.compression_type else None,
            "compression_config": self.compression_config,
            "compression_ratio": self.compression_ratio,
            "total_samples_received": self.total_samples_received,
            "total_samples_stored": self.total_samples_stored,
            "historian_enabled": self.historian_enabled,
            "historian_type": self.historian_type.value if self.historian_type else None,
            "historian_config": self.historian_config,
            "total_writes": self.total_writes,
            "write_errors": self.write_errors,
            "validation_rules": self.validation_rules,
            "avg_processing_time_ms": self.avg_processing_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_compression_ratio_percent(self) -> float:
        """Get compression ratio as percentage"""
        if self.total_samples_received == 0:
            return 0.0
        return (1.0 - (self.total_samples_stored / self.total_samples_received)) * 100.0

    def get_write_success_rate(self) -> float:
        """Get write success rate as percentage"""
        if self.total_writes == 0:
            return 100.0
        return ((self.total_writes - self.write_errors) / self.total_writes) * 100.0
