"""
Asset Health Alert models - Automated alerts based on asset health scores
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class HealthAlertSeverity(str, enum.Enum):
    """Health alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class HealthAlertState(str, enum.Enum):
    """Health alert states"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AssetHealthAlert(Base):
    """
    Asset Health Alert - Automated alerts generated from asset health monitoring

    Tracks health-based alerts for assets with low health scores,
    critical issues, or concerning warning patterns.
    """
    __tablename__ = "asset_health_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)

    # Alert information
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(SQLEnum(HealthAlertSeverity), nullable=False, index=True)
    state = Column(SQLEnum(HealthAlertState), default=HealthAlertState.ACTIVE, nullable=False, index=True)

    # Health metrics at time of alert
    health_score = Column(Float, nullable=False)
    health_status = Column(String(50), nullable=False)  # excellent, good, fair, poor, critical
    issues_count = Column(Float, default=0, nullable=False)
    warnings_count = Column(Float, default=0, nullable=False)

    # Problematic attributes
    problematic_attributes = Column(JSONB, default=list, nullable=False)  # List of attribute issues

    # Recommendations
    recommendations = Column(JSONB, default=list, nullable=False)  # List of recommended actions

    # Alert metadata
    alert_metadata = Column(JSONB, default=dict, nullable=False)  # Additional data

    # Acknowledgment
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    acknowledgment_comment = Column(Text, nullable=True)

    # Resolution
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_comment = Column(Text, nullable=True)
    resolved_health_score = Column(Float, nullable=True)

    # Notification settings
    notification_sent = Column(Boolean, default=False, nullable=False)
    notification_sent_at = Column(DateTime(timezone=True), nullable=True)

    # Auto-resolution
    auto_resolved = Column(Boolean, default=False, nullable=False)

    # Timestamps
    triggered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    asset = relationship("Asset", back_populates="health_alerts")

    def __repr__(self):
        return f"<AssetHealthAlert {self.title} ({self.severity.value} - {self.state.value})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "state": self.state.value,
            "health_score": self.health_score,
            "health_status": self.health_status,
            "issues_count": self.issues_count,
            "warnings_count": self.warnings_count,
            "problematic_attributes": self.problematic_attributes,
            "recommendations": self.recommendations,
            "alert_metadata": self.alert_metadata,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": str(self.acknowledged_by) if self.acknowledged_by else None,
            "acknowledgment_comment": self.acknowledgment_comment,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": str(self.resolved_by) if self.resolved_by else None,
            "resolution_comment": self.resolution_comment,
            "resolved_health_score": self.resolved_health_score,
            "notification_sent": self.notification_sent,
            "auto_resolved": self.auto_resolved,
            "triggered_at": self.triggered_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
