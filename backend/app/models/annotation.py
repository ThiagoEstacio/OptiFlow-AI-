"""
Annotation model for team collaboration
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

from app.db.base import Base


class AnnotationType(str, enum.Enum):
    """Annotation types"""
    COMMENT = "comment"
    EVENT = "event"
    ALARM = "alarm"
    MAINTENANCE = "maintenance"
    OBSERVATION = "observation"
    ISSUE = "issue"


class AnnotationPriority(str, enum.Enum):
    """Annotation priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Annotation(Base):
    """
    Annotation model for team collaboration and event tracking

    Annotations can be attached to:
    - Devices
    - Tags
    - Time series data points
    - Dashboards
    - Sites
    """
    __tablename__ = "annotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Annotation metadata
    type = Column(SQLEnum(AnnotationType), nullable=False, default=AnnotationType.COMMENT)
    priority = Column(SQLEnum(AnnotationPriority), nullable=True, default=AnnotationPriority.MEDIUM)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Temporal information
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)

    # Relationships - what this annotation is attached to
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), nullable=True)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=True)

    # User information
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Additional metadata
    tags = Column(JSON, nullable=True, default=list)  # Custom tags for categorization
    metadata = Column(JSON, nullable=True, default=dict)  # Additional metadata

    # Status and visibility
    is_public = Column(Boolean, default=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by], backref="annotations_created")
    resolver = relationship("User", foreign_keys=[resolved_by], backref="annotations_resolved")

    def __repr__(self):
        return f"<Annotation(id={self.id}, type={self.type}, title={self.title})>"


class AnnotationComment(Base):
    """
    Comments on annotations for threaded discussions
    """
    __tablename__ = "annotation_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    annotation_id = Column(UUID(as_uuid=True), ForeignKey("annotations.id", ondelete="CASCADE"), nullable=False)

    # Comment content
    comment = Column(Text, nullable=False)

    # User information
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Reply threading
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("annotation_comments.id", ondelete="CASCADE"), nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    is_edited = Column(Boolean, default=False)

    # Relationships
    annotation = relationship("Annotation", backref="comments")
    creator = relationship("User", backref="annotation_comments")
    replies = relationship("AnnotationComment", backref="parent", remote_side=[id])

    def __repr__(self):
        return f"<AnnotationComment(id={self.id}, annotation_id={self.annotation_id})>"
