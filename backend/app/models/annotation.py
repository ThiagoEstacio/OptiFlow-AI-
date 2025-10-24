"""
Annotation Model

Allows users to add comments, notes, and markers to time-series data for documentation
and collaboration purposes.

Use cases:
- Document equipment failures or maintenance activities
- Mark significant events on trends
- Add context to anomalies
- Collaborative troubleshooting
- Audit trail of operator actions
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.models.base import Base


class AnnotationType(str, enum.Enum):
    """Types of annotations"""
    COMMENT = "comment"  # General comment
    EVENT = "event"  # Significant event marker
    ALARM = "alarm"  # Alarm/alert related
    MAINTENANCE = "maintenance"  # Maintenance activity
    QUALITY = "quality"  # Quality issue
    NOTE = "note"  # General note
    BOOKMARK = "bookmark"  # Bookmark for easy reference


class AnnotationSeverity(str, enum.Enum):
    """Severity levels for annotations"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Annotation(Base):
    """
    Annotation model for time-series data.

    Annotations can be attached to:
    - A specific tag at a specific time
    - A time range on a tag
    - Multiple tags (for cross-tag events)
    - A specific device or site
    """
    __tablename__ = "annotations"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Type and classification
    annotation_type = Column(SQLEnum(AnnotationType), nullable=False, default=AnnotationType.COMMENT)
    severity = Column(SQLEnum(AnnotationSeverity), nullable=False, default=AnnotationSeverity.INFO)

    # Content
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)  # Markdown supported

    # Time information
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True, index=True)  # For range annotations

    # Tag association (optional - can be device/site level)
    tag_id = Column(UUID, ForeignKey("tags.id", ondelete="CASCADE"), nullable=True, index=True)
    tag = relationship("Tag", back_populates="annotations")

    # Device/Site association (for broader annotations)
    device_id = Column(UUID, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True, index=True)
    device = relationship("Device")

    site_id = Column(UUID, ForeignKey("sites.id", ondelete="CASCADE"), nullable=True, index=True)
    site = relationship("Site")

    # User information
    created_by = Column(String(255), nullable=False)  # Username or user ID
    created_by_name = Column(String(255), nullable=True)  # Display name

    # Additional metadata
    metadata = Column(JSONB, default=dict, nullable=False)  # Custom fields, attachments, etc.

    # Color for visual representation
    color = Column(String(7), nullable=True)  # Hex color code (e.g., "#FF5733")

    # Visibility and permissions
    is_public = Column(Boolean, default=True, nullable=False)  # Public or private
    pinned = Column(Boolean, default=False, nullable=False)  # Pinned to top

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)

    def __repr__(self):
        return f"<Annotation {self.id} type={self.annotation_type} title='{self.title}'>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "annotation_type": self.annotation_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "content": self.content,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "tag_id": str(self.tag_id) if self.tag_id else None,
            "device_id": str(self.device_id) if self.device_id else None,
            "site_id": str(self.site_id) if self.site_id else None,
            "created_by": self.created_by,
            "created_by_name": self.created_by_name,
            "metadata": self.metadata,
            "color": self.color,
            "is_public": self.is_public,
            "pinned": self.pinned,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_deleted": self.is_deleted
        }

    @property
    def duration_seconds(self):
        """Calculate duration for range annotations"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

    @property
    def is_range(self):
        """Check if this is a range annotation"""
        return self.end_time is not None and self.end_time > self.start_time
