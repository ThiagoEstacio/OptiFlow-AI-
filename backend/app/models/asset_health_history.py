"""
Asset Health History - Time-series storage of health scores

Stores periodic snapshots of asset health for trend analysis,
pattern detection, and predictive maintenance.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class AssetHealthHistory(Base):
    """
    Asset Health History - Time-series health score snapshots

    Captures health metrics at regular intervals for:
    - Trend analysis
    - Pattern detection
    - Anomaly identification
    - Predictive maintenance
    - Performance reporting
    """
    __tablename__ = "asset_health_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)

    # Snapshot timestamp
    snapshot_time = Column(DateTime(timezone=True), nullable=False, index=True)

    # Health metrics
    health_score = Column(Float, nullable=False, index=True)  # 0-100
    health_status = Column(String(50), nullable=False, index=True)  # excellent, good, fair, poor, critical

    # Issue counts
    issues_count = Column(Integer, default=0, nullable=False)
    warnings_count = Column(Integer, default=0, nullable=False)
    attributes_evaluated = Column(Integer, default=0, nullable=False)

    # Attribute-level details
    attribute_scores = Column(JSONB, default=dict, nullable=False)
    # Format: {"attribute_name": {"score": 85, "value": 75.5, "status": "good"}}

    # Issues and warnings snapshot
    issues_snapshot = Column(JSONB, default=list, nullable=False)
    warnings_snapshot = Column(JSONB, default=list, nullable=False)

    # Asset metadata at snapshot time
    asset_metadata = Column(JSONB, default=dict, nullable=False)
    # Stores: asset_name, asset_type, full_path for historical reference

    # Statistical metrics
    health_score_change = Column(Float, nullable=True)  # Change from previous snapshot
    trend_direction = Column(String(20), nullable=True)  # improving, degrading, stable

    # Calculated from this and previous snapshots
    velocity = Column(Float, nullable=True)  # Rate of change (points per hour)

    # Record metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    asset = relationship("Asset", backref="health_history")

    def __repr__(self):
        return f"<AssetHealthHistory {self.asset_id} @ {self.snapshot_time} ({self.health_score:.1f})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "snapshot_time": self.snapshot_time.isoformat(),
            "health_score": self.health_score,
            "health_status": self.health_status,
            "issues_count": self.issues_count,
            "warnings_count": self.warnings_count,
            "attributes_evaluated": self.attributes_evaluated,
            "attribute_scores": self.attribute_scores,
            "issues_snapshot": self.issues_snapshot,
            "warnings_snapshot": self.warnings_snapshot,
            "asset_metadata": self.asset_metadata,
            "health_score_change": self.health_score_change,
            "trend_direction": self.trend_direction,
            "velocity": self.velocity,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def create_snapshot(cls, asset, health_data, previous_snapshot=None):
        """
        Factory method to create a health history snapshot

        Args:
            asset: Asset model instance
            health_data: Dict from AssetHealthCalculator
            previous_snapshot: Previous snapshot for trend calculation
        """
        # Extract attribute-level scores
        attribute_scores = {}
        for attr_data in health_data.get("attribute_details", []):
            attr_name = attr_data.get("attribute", {}).get("name")
            if attr_name:
                attribute_scores[attr_name] = {
                    "score": attr_data.get("score", 100),
                    "value": attr_data.get("value"),
                    "status": attr_data.get("status", "unknown")
                }

        # Calculate change and trend
        health_score = health_data.get("health_score", 100)
        health_score_change = None
        trend_direction = "stable"
        velocity = None

        if previous_snapshot:
            health_score_change = health_score - previous_snapshot.health_score

            # Determine trend direction
            if health_score_change > 5:
                trend_direction = "improving"
            elif health_score_change < -5:
                trend_direction = "degrading"
            else:
                trend_direction = "stable"

            # Calculate velocity (points per hour)
            from datetime import datetime
            time_diff = (datetime.utcnow() - previous_snapshot.snapshot_time).total_seconds() / 3600
            if time_diff > 0:
                velocity = health_score_change / time_diff

        return cls(
            asset_id=asset.id,
            snapshot_time=func.now(),
            health_score=health_score,
            health_status=health_data.get("status", "unknown"),
            issues_count=len(health_data.get("issues", [])),
            warnings_count=len(health_data.get("warnings", [])),
            attributes_evaluated=len(health_data.get("attribute_details", [])),
            attribute_scores=attribute_scores,
            issues_snapshot=health_data.get("issues", [])[:10],  # Keep top 10
            warnings_snapshot=health_data.get("warnings", [])[:10],  # Keep top 10
            asset_metadata={
                "asset_name": asset.name,
                "asset_type": asset.asset_type.value,
                "full_path": asset.full_path,
            },
            health_score_change=health_score_change,
            trend_direction=trend_direction,
            velocity=velocity,
        )
