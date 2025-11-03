"""
Asset Health Alert Manager - Automated alert generation and management

Creates, manages, and auto-resolves health alerts based on asset health monitoring
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from uuid import UUID

from app.models.asset import Asset
from app.models.asset_health_alert import AssetHealthAlert, HealthAlertSeverity, HealthAlertState
from app.services.asset_health import AssetHealthCalculator

logger = logging.getLogger(__name__)


class AssetHealthAlertManager:
    """
    Manages asset health alerts:
    - Creates new alerts when assets have health issues
    - Auto-resolves alerts when health improves
    - Prevents duplicate alerts
    - Tracks alert history
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.health_calculator = AssetHealthCalculator(db)

        # Alert thresholds
        self.critical_threshold = 30  # Health score below this triggers critical alert
        self.poor_threshold = 50  # Health score below this triggers high alert
        self.fair_threshold = 70  # Health score below this triggers medium alert

        # Auto-resolution threshold
        self.resolution_threshold = 75  # Health score above this auto-resolves alerts

    async def check_and_create_alerts(self, asset_id: str) -> Optional[AssetHealthAlert]:
        """
        Check asset health and create alert if needed

        Returns:
            AssetHealthAlert if alert was created, None otherwise
        """
        try:
            # Calculate current health
            health_data = await self.health_calculator.calculate_asset_health(asset_id)

            health_score = health_data.get("health_score", 100)
            status = health_data.get("status", "unknown")
            issues = health_data.get("issues", [])
            warnings = health_data.get("warnings", [])

            # Only create alerts for problematic assets
            if status not in ["critical", "poor", "fair"]:
                # Check if there's an active alert that should be auto-resolved
                await self.auto_resolve_alerts(asset_id, health_score)
                return None

            # Check if there's already an active alert for this asset
            existing_alert = await self._get_active_alert(asset_id)

            if existing_alert:
                # Update existing alert if health has changed significantly
                if abs(existing_alert.health_score - health_score) > 10:
                    await self._update_alert(existing_alert, health_data)
                return None

            # Get asset details
            result = await self.db.execute(
                select(Asset).where(Asset.id == UUID(asset_id))
            )
            asset = result.scalar_one_or_none()

            if not asset:
                return None

            # Determine severity
            severity = self._calculate_severity(health_score, status)

            # Build title and message
            title = f"⚠️ {asset.name}: Health Score {status.upper()}"

            problems = []
            if issues:
                problems.append(f"{len(issues)} critical issues")
            if warnings:
                problems.append(f"{len(warnings)} warnings")

            problems_str = " and ".join(problems) if problems else "Parameters out of recommended limits"
            message = f"Asset health score is {health_score:.1f}/100. {problems_str}. Asset type: {asset.asset_type.value}."

            # Build problematic attributes list
            problematic_attrs = []
            for issue in issues[:5]:
                attr = issue.get("attribute", {})
                problematic_attrs.append({
                    "name": attr.get("name", "Unknown"),
                    "current_value": issue.get("value"),
                    "expected_range": issue.get("expected_range"),
                    "severity": "critical"
                })

            for warning in warnings[:5]:
                attr = warning.get("attribute", {})
                problematic_attrs.append({
                    "name": attr.get("name", "Unknown"),
                    "current_value": warning.get("value"),
                    "expected_range": warning.get("expected_range"),
                    "severity": "warning"
                })

            # Build recommendations
            recommendations = []
            if issues:
                recommendations.append("🔴 Immediate action required for critical issues")
                for issue in issues[:3]:
                    attr_name = issue.get("attribute", {}).get("name", "Unknown")
                    recommendations.append(f"  • Check: {attr_name}")

            if warnings:
                recommendations.append("⚠️ Monitor warnings closely")
                for warning in warnings[:2]:
                    attr_name = warning.get("attribute", {}).get("name", "Unknown")
                    recommendations.append(f"  • Review: {attr_name}")

            if not recommendations:
                recommendations = [
                    "Review attribute threshold configuration",
                    "Verify asset operating conditions",
                    "Consider preventive maintenance"
                ]

            # Create new alert
            new_alert = AssetHealthAlert(
                asset_id=UUID(asset_id),
                title=title,
                message=message,
                severity=severity,
                state=HealthAlertState.ACTIVE,
                health_score=health_score,
                health_status=status,
                issues_count=len(issues),
                warnings_count=len(warnings),
                problematic_attributes=problematic_attrs,
                recommendations=recommendations,
                alert_metadata={
                    "asset_name": asset.name,
                    "asset_type": asset.asset_type.value,
                    "asset_path": asset.full_path,
                    "health_data": health_data
                },
                triggered_at=datetime.utcnow()
            )

            self.db.add(new_alert)
            await self.db.commit()
            await self.db.refresh(new_alert)

            logger.info(
                f"🚨 Health Alert Created: {asset.name} - "
                f"Score: {health_score:.1f} ({status}), "
                f"Severity: {severity.value}, "
                f"Issues: {len(issues)}, Warnings: {len(warnings)}"
            )

            return new_alert

        except Exception as e:
            logger.error(f"Error checking/creating alert for asset {asset_id}: {e}")
            await self.db.rollback()
            return None

    async def auto_resolve_alerts(self, asset_id: str, current_health_score: float) -> int:
        """
        Auto-resolve active alerts if health has improved

        Returns:
            Number of alerts auto-resolved
        """
        try:
            if current_health_score < self.resolution_threshold:
                return 0

            # Get all active alerts for this asset
            result = await self.db.execute(
                select(AssetHealthAlert).where(
                    and_(
                        AssetHealthAlert.asset_id == UUID(asset_id),
                        AssetHealthAlert.state == HealthAlertState.ACTIVE
                    )
                )
            )
            active_alerts = result.scalars().all()

            if not active_alerts:
                return 0

            resolved_count = 0
            for alert in active_alerts:
                alert.state = HealthAlertState.RESOLVED
                alert.resolved_at = datetime.utcnow()
                alert.resolved_health_score = current_health_score
                alert.auto_resolved = True
                alert.resolution_comment = f"Auto-resolved: Health score improved to {current_health_score:.1f}"
                resolved_count += 1

                logger.info(
                    f"✅ Auto-resolved alert for asset {asset_id}: "
                    f"Health improved from {alert.health_score:.1f} to {current_health_score:.1f}"
                )

            await self.db.commit()
            return resolved_count

        except Exception as e:
            logger.error(f"Error auto-resolving alerts for asset {asset_id}: {e}")
            await self.db.rollback()
            return 0

    async def acknowledge_alert(
        self,
        alert_id: str,
        user_id: Optional[str] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Acknowledge an alert

        Returns:
            True if acknowledged successfully
        """
        try:
            result = await self.db.execute(
                select(AssetHealthAlert).where(AssetHealthAlert.id == UUID(alert_id))
            )
            alert = result.scalar_one_or_none()

            if not alert:
                return False

            alert.state = HealthAlertState.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            if user_id:
                alert.acknowledged_by = UUID(user_id)
            alert.acknowledgment_comment = comment

            await self.db.commit()

            logger.info(f"✓ Alert {alert_id} acknowledged by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {e}")
            await self.db.rollback()
            return False

    async def resolve_alert(
        self,
        alert_id: str,
        user_id: Optional[str] = None,
        comment: Optional[str] = None,
        resolved_health_score: Optional[float] = None
    ) -> bool:
        """
        Manually resolve an alert

        Returns:
            True if resolved successfully
        """
        try:
            result = await self.db.execute(
                select(AssetHealthAlert).where(AssetHealthAlert.id == UUID(alert_id))
            )
            alert = result.scalar_one_or_none()

            if not alert:
                return False

            alert.state = HealthAlertState.RESOLVED
            alert.resolved_at = datetime.utcnow()
            if user_id:
                alert.resolved_by = UUID(user_id)
            alert.resolution_comment = comment
            if resolved_health_score is not None:
                alert.resolved_health_score = resolved_health_score

            await self.db.commit()

            logger.info(f"✓ Alert {alert_id} resolved by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {e}")
            await self.db.rollback()
            return False

    async def get_active_alerts(
        self,
        asset_id: Optional[str] = None,
        severity: Optional[HealthAlertSeverity] = None,
        limit: int = 100
    ) -> List[AssetHealthAlert]:
        """Get active alerts with optional filters"""
        try:
            conditions = [AssetHealthAlert.state == HealthAlertState.ACTIVE]

            if asset_id:
                conditions.append(AssetHealthAlert.asset_id == UUID(asset_id))

            if severity:
                conditions.append(AssetHealthAlert.severity == severity)

            result = await self.db.execute(
                select(AssetHealthAlert)
                .where(and_(*conditions))
                .order_by(AssetHealthAlert.triggered_at.desc())
                .limit(limit)
            )

            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []

    async def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics for dashboard"""
        try:
            # Count by state
            result = await self.db.execute(
                select(AssetHealthAlert).where(AssetHealthAlert.state == HealthAlertState.ACTIVE)
            )
            active_alerts = result.scalars().all()

            by_severity = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }

            for alert in active_alerts:
                by_severity[alert.severity.value] += 1

            return {
                "total_active": len(active_alerts),
                "by_severity": by_severity,
                "critical_count": by_severity["critical"],
                "high_count": by_severity["high"],
            }

        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            return {
                "total_active": 0,
                "by_severity": {},
                "critical_count": 0,
                "high_count": 0,
            }

    async def _get_active_alert(self, asset_id: str) -> Optional[AssetHealthAlert]:
        """Get active alert for an asset"""
        result = await self.db.execute(
            select(AssetHealthAlert).where(
                and_(
                    AssetHealthAlert.asset_id == UUID(asset_id),
                    AssetHealthAlert.state == HealthAlertState.ACTIVE
                )
            )
        )
        return result.scalar_one_or_none()

    async def _update_alert(self, alert: AssetHealthAlert, health_data: Dict[str, Any]):
        """Update existing alert with new health data"""
        alert.health_score = health_data.get("health_score", alert.health_score)
        alert.health_status = health_data.get("status", alert.health_status)
        alert.issues_count = len(health_data.get("issues", []))
        alert.warnings_count = len(health_data.get("warnings", []))
        alert.updated_at = datetime.utcnow()
        await self.db.commit()

    def _calculate_severity(self, health_score: float, status: str) -> HealthAlertSeverity:
        """Calculate alert severity based on health score and status"""
        if health_score < self.critical_threshold or status == "critical":
            return HealthAlertSeverity.CRITICAL
        elif health_score < self.poor_threshold or status == "poor":
            return HealthAlertSeverity.HIGH
        elif health_score < self.fair_threshold or status == "fair":
            return HealthAlertSeverity.MEDIUM
        else:
            return HealthAlertSeverity.LOW
