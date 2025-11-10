"""
Executive Dashboard 360° Service

Provides unified view of maintenance + operations with real-time KPIs,
correlation analysis, and strategic insights for executive decision-making.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, distinct
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
import logging

from app.models.asset import Asset, AssetType
from app.models.alarm import AlarmDefinition, AlarmSeverity
from app.models.operational_data import TruckEntry, ShipLoading
from app.models.organization import Site

logger = logging.getLogger(__name__)


class ExecutiveDashboard:
    """
    Executive Dashboard 360° - Unified view of terminal operations and maintenance.

    Provides strategic insights by correlating maintenance health with operational
    performance, calculating ROI, and identifying risks and opportunities.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_360(
        self,
        site_id: int,
        period_days: int = 7
    ) -> Dict[str, Any]:
        """
        Get complete 360° dashboard with maintenance + operations insights.

        Args:
            site_id: Site identifier
            period_days: Analysis period in days (default: 7)

        Returns:
            Comprehensive dashboard with all KPIs, correlations, and insights
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=period_days)

            # Execute all queries in parallel
            maintenance_kpis = await self._get_maintenance_kpis(site_id, start_date)
            operational_kpis = await self._get_operational_kpis(site_id, start_date)
            critical_alerts = await self._get_critical_alerts(site_id)
            asset_health = await self._get_asset_health_summary(site_id)
            correlations = await self._get_maintenance_operation_correlations(site_id, start_date)
            risks = await self._identify_risks(site_id)
            opportunities = await self._identify_opportunities(site_id, start_date)

            return {
                "status": "success",
                "site_id": site_id,
                "period_days": period_days,
                "timestamp": datetime.utcnow().isoformat(),

                # Core KPIs
                "maintenance": maintenance_kpis,
                "operations": operational_kpis,

                # Health & Status
                "asset_health": asset_health,
                "critical_alerts": critical_alerts,

                # Strategic Insights
                "correlations": correlations,
                "risks": risks,
                "opportunities": opportunities,

                # Overall Score
                "overall_health_score": self._calculate_overall_health(
                    maintenance_kpis,
                    operational_kpis,
                    asset_health
                )
            }

        except Exception as e:
            logger.error(f"Error generating 360° dashboard: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def _get_maintenance_kpis(
        self,
        site_id: int,
        start_date: datetime
    ) -> Dict[str, Any]:
        """Get maintenance-related KPIs."""

        # Total assets
        total_assets_query = select(func.count(Asset.id)).where(Asset.site_id == site_id)
        total_assets_result = await self.db.execute(total_assets_query)
        total_assets = total_assets_result.scalar() or 0

        # Average health score
        avg_health_query = select(func.avg(Asset.health_score)).where(
            and_(Asset.site_id == site_id, Asset.health_score.isnot(None))
        )
        avg_health_result = await self.db.execute(avg_health_query)
        avg_health = avg_health_result.scalar() or 0

        # Assets by health category
        critical_assets_query = select(func.count(Asset.id)).where(
            and_(Asset.site_id == site_id, Asset.health_score < 40)
        )
        critical_result = await self.db.execute(critical_assets_query)
        critical_assets = critical_result.scalar() or 0

        warning_assets_query = select(func.count(Asset.id)).where(
            and_(Asset.site_id == site_id, Asset.health_score >= 40, Asset.health_score < 70)
        )
        warning_result = await self.db.execute(warning_assets_query)
        warning_assets = warning_result.scalar() or 0

        healthy_assets_query = select(func.count(Asset.id)).where(
            and_(Asset.site_id == site_id, Asset.health_score >= 70)
        )
        healthy_result = await self.db.execute(healthy_assets_query)
        healthy_assets = healthy_result.scalar() or 0

        # Alarms in period
        total_alarms_query = select(func.count(AlarmDefinition.id)).where(
            and_(
                AlarmDefinition.site_id == site_id,
                AlarmDefinition.timestamp >= start_date
            )
        )
        total_alarms_result = await self.db.execute(total_alarms_query)
        total_alarms = total_alarms_result.scalar() or 0

        # Critical alarms
        critical_alarms_query = select(func.count(AlarmDefinition.id)).where(
            and_(
                AlarmDefinition.site_id == site_id,
                AlarmDefinition.timestamp >= start_date,
                AlarmDefinition.severity == AlarmSeverity.CRITICAL
            )
        )
        critical_alarms_result = await self.db.execute(critical_alarms_query)
        critical_alarms = critical_alarms_result.scalar() or 0

        # Assets needing maintenance (overdue or health < 60)
        maintenance_needed_query = select(func.count(Asset.id)).where(
            and_(
                Asset.site_id == site_id,
                or_(
                    Asset.health_score < 60,
                    Asset.last_maintenance < datetime.utcnow() - timedelta(days=90)
                )
            )
        )
        maintenance_needed_result = await self.db.execute(maintenance_needed_query)
        maintenance_needed = maintenance_needed_result.scalar() or 0

        return {
            "total_assets": total_assets,
            "average_health_score": round(avg_health, 1),
            "assets_by_health": {
                "critical": critical_assets,
                "warning": warning_assets,
                "healthy": healthy_assets
            },
            "alarms": {
                "total": total_alarms,
                "critical": critical_alarms,
                "avg_per_day": round(total_alarms / max(1, (datetime.utcnow() - start_date).days), 1)
            },
            "maintenance_needed": maintenance_needed,
            "health_trend": await self._get_health_trend(site_id)
        }

    async def _get_operational_kpis(
        self,
        site_id: int,
        start_date: datetime
    ) -> Dict[str, Any]:
        """Get operations-related KPIs."""

        # Trucks processed
        trucks_query = select(func.count(TruckEntry.id)).where(
            and_(
                TruckEntry.site_id == site_id,
                TruckEntry.entry_time >= start_date
            )
        )
        trucks_result = await self.db.execute(trucks_query)
        total_trucks = trucks_result.scalar() or 0

        # Total tonnage from trucks
        tonnage_query = select(func.sum(TruckEntry.net_weight)).where(
            and_(
                TruckEntry.site_id == site_id,
                TruckEntry.entry_time >= start_date,
                TruckEntry.net_weight.isnot(None)
            )
        )
        tonnage_result = await self.db.execute(tonnage_query)
        total_tonnage = tonnage_result.scalar() or 0

        # Ships in period
        ships_query = select(func.count(ShipLoading.id)).where(
            and_(
                ShipLoading.site_id == site_id,
                ShipLoading.scheduled_arrival >= start_date
            )
        )
        ships_result = await self.db.execute(ships_query)
        total_ships = ships_result.scalar() or 0

        # Completed ships
        completed_ships_query = select(func.count(ShipLoading.id)).where(
            and_(
                ShipLoading.site_id == site_id,
                ShipLoading.scheduled_arrival >= start_date,
                ShipLoading.status == "completed"
            )
        )
        completed_result = await self.db.execute(completed_ships_query)
        completed_ships = completed_result.scalar() or 0

        # Currently loading
        loading_now_query = select(func.count(ShipLoading.id)).where(
            and_(
                ShipLoading.site_id == site_id,
                ShipLoading.status == "loading"
            )
        )
        loading_result = await self.db.execute(loading_now_query)
        loading_now = loading_result.scalar() or 0

        # Berth utilization
        berth_utilization = await self._calculate_berth_utilization(site_id, start_date)

        # Average truck processing time
        avg_time_query = select(
            func.avg(
                func.extract('epoch', TruckEntry.exit_time - TruckEntry.entry_time) / 3600
            )
        ).where(
            and_(
                TruckEntry.site_id == site_id,
                TruckEntry.entry_time >= start_date,
                TruckEntry.exit_time.isnot(None)
            )
        )
        avg_time_result = await self.db.execute(avg_time_query)
        avg_processing_time = avg_time_result.scalar() or 0

        return {
            "trucks": {
                "total": total_trucks,
                "avg_per_day": round(total_trucks / max(1, (datetime.utcnow() - start_date).days), 1),
                "avg_processing_time_hours": round(avg_processing_time, 2)
            },
            "tonnage": {
                "total": round(total_tonnage / 1000, 2) if total_tonnage else 0,  # Convert to tons
                "avg_per_day": round((total_tonnage / 1000) / max(1, (datetime.utcnow() - start_date).days), 2)
            },
            "ships": {
                "total": total_ships,
                "completed": completed_ships,
                "loading_now": loading_now,
                "completion_rate": round((completed_ships / total_ships * 100), 1) if total_ships > 0 else 0
            },
            "berth_utilization_percent": berth_utilization,
            "efficiency_score": await self._calculate_efficiency_score(site_id, start_date)
        }

    async def _get_critical_alerts(self, site_id: int) -> List[Dict[str, Any]]:
        """Get current critical alerts requiring immediate attention."""

        # Critical alarms in last 24 hours
        query = select(AlarmDefinition).where(
            and_(
                AlarmDefinition.site_id == site_id,
                AlarmDefinition.severity == AlarmSeverity.CRITICAL,
                AlarmDefinition.timestamp >= datetime.utcnow() - timedelta(hours=24),
                AlarmDefinition.acknowledged == False
            )
        ).order_by(AlarmDefinition.timestamp.desc()).limit(10)

        result = await self.db.execute(query)
        alarms = result.scalars().all()

        alerts = []
        for alarm in alarms:
            # Get asset if available
            asset = None
            if alarm.asset_id:
                asset = await self.db.get(Asset, alarm.asset_id)

            alerts.append({
                "type": "critical_alarm",
                "severity": "critical",
                "message": alarm.message,
                "asset_id": alarm.asset_id,
                "asset_name": asset.name if asset else "Unknown",
                "timestamp": alarm.timestamp.isoformat(),
                "duration_hours": round((datetime.utcnow() - alarm.timestamp).total_seconds() / 3600, 1)
            })

        # Add critical health assets
        critical_assets_query = select(Asset).where(
            and_(
                Asset.site_id == site_id,
                Asset.health_score < 40
            )
        ).limit(5)

        critical_assets_result = await self.db.execute(critical_assets_query)
        critical_assets = critical_assets_result.scalars().all()

        for asset in critical_assets:
            alerts.append({
                "type": "critical_health",
                "severity": "high",
                "message": f"{asset.name} has critical health score",
                "asset_id": asset.id,
                "asset_name": asset.name,
                "health_score": asset.health_score,
                "recommendation": "Schedule immediate maintenance"
            })

        return alerts[:15]  # Return top 15 alerts

    async def _get_asset_health_summary(self, site_id: int) -> Dict[str, Any]:
        """Get summary of asset health by type and category."""

        # Health by asset type
        type_query = select(
            Asset.asset_type,
            func.count(Asset.id).label('count'),
            func.avg(Asset.health_score).label('avg_health')
        ).where(
            Asset.site_id == site_id
        ).group_by(Asset.asset_type)

        type_result = await self.db.execute(type_query)
        type_data = type_result.all()

        by_type = {}
        for row in type_data:
            by_type[row.asset_type.value if row.asset_type else "unknown"] = {
                "count": row.count,
                "avg_health": round(row.avg_health, 1) if row.avg_health else 0
            }

        # Top 5 worst assets
        worst_query = select(Asset).where(
            Asset.site_id == site_id
        ).order_by(Asset.health_score.asc()).limit(5)

        worst_result = await self.db.execute(worst_query)
        worst_assets = worst_result.scalars().all()

        worst_list = [
            {
                "asset_id": asset.id,
                "name": asset.name,
                "type": asset.asset_type.value if asset.asset_type else "unknown",
                "health_score": asset.health_score,
                "priority": "critical" if asset.health_score < 40 else "high"
            }
            for asset in worst_assets
        ]

        return {
            "by_type": by_type,
            "worst_performing": worst_list,
            "total_at_risk": len([a for a in worst_list if a["health_score"] < 60])
        }

    async def _get_maintenance_operation_correlations(
        self,
        site_id: int,
        start_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Identify correlations between maintenance events and operational impact.
        This is a key differentiator - showing HOW maintenance affects operations.
        """
        correlations = []

        # Find recent critical alarms with associated assets
        alarm_query = select(AlarmDefinition).where(
            and_(
                AlarmDefinition.site_id == site_id,
                AlarmDefinition.timestamp >= start_date,
                AlarmDefinition.severity.in_([AlarmSeverity.CRITICAL, AlarmSeverity.HIGH]),
                AlarmDefinition.asset_id.isnot(None)
            )
        ).order_by(AlarmDefinition.timestamp.desc())

        alarm_result = await self.db.execute(alarm_query)
        alarms = alarm_result.scalars().all()

        for alarm in alarms[:10]:  # Analyze top 10 recent critical alarms
            asset = await self.db.get(Asset, alarm.asset_id)
            if not asset:
                continue

            # Check operational impact based on asset type
            impact = await self._calculate_operational_impact(
                site_id,
                asset,
                alarm.timestamp
            )

            if impact["has_impact"]:
                correlations.append({
                    "event_type": "alarm",
                    "asset_name": asset.name,
                    "asset_type": asset.asset_type.value if asset.asset_type else "unknown",
                    "alarm_message": alarm.message,
                    "timestamp": alarm.timestamp.isoformat(),
                    "operational_impact": impact,
                    "correlation_confidence": impact.get("confidence", 0.7)
                })

        return correlations

    async def _calculate_operational_impact(
        self,
        site_id: int,
        asset: Asset,
        event_time: datetime
    ) -> Dict[str, Any]:
        """Calculate operational impact of a maintenance event."""

        impact = {
            "has_impact": False,
            "confidence": 0.5
        }

        # Check if asset type affects operations
        if asset.asset_type in [AssetType.CONVEYOR, AssetType.LOADER, AssetType.STACKER]:
            # Check for operational slowdowns after the event
            window_start = event_time
            window_end = event_time + timedelta(hours=6)

            # Check ship loading delays
            ships_query = select(ShipLoading).where(
                and_(
                    ShipLoading.site_id == site_id,
                    ShipLoading.actual_arrival.between(window_start, window_end)
                )
            )
            ships_result = await self.db.execute(ships_query)
            ships = ships_result.scalars().all()

            delayed_count = 0
            total_delay_hours = 0

            for ship in ships:
                if ship.actual_arrival and ship.scheduled_arrival:
                    delay = (ship.actual_arrival - ship.scheduled_arrival).total_seconds() / 3600
                    if delay > 1:  # More than 1 hour delay
                        delayed_count += 1
                        total_delay_hours += delay

            if delayed_count > 0:
                impact["has_impact"] = True
                impact["type"] = "ship_delay"
                impact["ships_affected"] = delayed_count
                impact["total_delay_hours"] = round(total_delay_hours, 1)
                impact["estimated_cost"] = round(total_delay_hours * 5000, 2)  # $5k per hour estimate
                impact["confidence"] = 0.8

            # Check truck processing slowdown
            trucks_before_query = select(func.count(TruckEntry.id)).where(
                and_(
                    TruckEntry.site_id == site_id,
                    TruckEntry.entry_time.between(
                        event_time - timedelta(hours=2),
                        event_time
                    )
                )
            )
            trucks_before_result = await self.db.execute(trucks_before_query)
            trucks_before = trucks_before_result.scalar() or 0

            trucks_after_query = select(func.count(TruckEntry.id)).where(
                and_(
                    TruckEntry.site_id == site_id,
                    TruckEntry.entry_time.between(
                        event_time,
                        event_time + timedelta(hours=2)
                    )
                )
            )
            trucks_after_result = await self.db.execute(trucks_after_query)
            trucks_after = trucks_after_result.scalar() or 0

            if trucks_before > 0 and trucks_after < trucks_before * 0.7:  # 30% reduction
                impact["has_impact"] = True
                impact["type"] = "throughput_reduction"
                impact["reduction_percent"] = round((1 - trucks_after / trucks_before) * 100, 1)
                impact["trucks_before"] = trucks_before
                impact["trucks_after"] = trucks_after
                impact["confidence"] = 0.75

        return impact

    async def _identify_risks(self, site_id: int) -> List[Dict[str, Any]]:
        """Identify current and upcoming risks."""
        risks = []

        # Risk: Critical assets
        critical_query = select(Asset).where(
            and_(
                Asset.site_id == site_id,
                Asset.health_score < 40
            )
        )
        critical_result = await self.db.execute(critical_query)
        critical_assets = critical_result.scalars().all()

        for asset in critical_assets:
            risks.append({
                "risk_type": "asset_failure",
                "severity": "critical",
                "asset_id": asset.id,
                "asset_name": asset.name,
                "description": f"{asset.name} has critical health score ({asset.health_score})",
                "potential_impact": "Unplanned downtime, operational disruption",
                "estimated_cost": 50000,  # Estimated cost of failure
                "mitigation": "Schedule immediate preventive maintenance"
            })

        # Risk: Overdue maintenance
        overdue_query = select(Asset).where(
            and_(
                Asset.site_id == site_id,
                Asset.last_maintenance < datetime.utcnow() - timedelta(days=120)
            )
        ).limit(10)
        overdue_result = await self.db.execute(overdue_query)
        overdue_assets = overdue_result.scalars().all()

        for asset in overdue_assets:
            days_overdue = (datetime.utcnow() - asset.last_maintenance).days - 90 if asset.last_maintenance else 0
            risks.append({
                "risk_type": "overdue_maintenance",
                "severity": "high" if days_overdue > 60 else "medium",
                "asset_id": asset.id,
                "asset_name": asset.name,
                "description": f"{asset.name} maintenance overdue by {days_overdue} days",
                "potential_impact": "Increased failure probability",
                "mitigation": "Schedule maintenance within next 2 weeks"
            })

        return risks[:20]  # Top 20 risks

    async def _identify_opportunities(
        self,
        site_id: int,
        start_date: datetime
    ) -> List[Dict[str, Any]]:
        """Identify optimization opportunities."""
        opportunities = []

        # Opportunity: Maintenance windows
        # Find periods with low ship activity
        ships_query = select(ShipLoading).where(
            and_(
                ShipLoading.site_id == site_id,
                ShipLoading.scheduled_arrival >= datetime.utcnow(),
                ShipLoading.scheduled_arrival <= datetime.utcnow() + timedelta(days=7)
            )
        ).order_by(ShipLoading.scheduled_arrival)

        ships_result = await self.db.execute(ships_query)
        ships = ships_result.scalars().all()

        # Find gaps between ships
        for i in range(len(ships) - 1):
            gap_hours = (ships[i+1].scheduled_arrival - ships[i].scheduled_arrival).total_seconds() / 3600
            if gap_hours > 12:  # Gap of more than 12 hours
                opportunities.append({
                    "opportunity_type": "maintenance_window",
                    "description": f"12+ hour window for maintenance",
                    "start_time": ships[i].scheduled_arrival.isoformat(),
                    "duration_hours": round(gap_hours, 1),
                    "benefit": "Zero operational impact maintenance",
                    "recommendation": "Schedule preventive maintenance for critical assets"
                })

        # Opportunity: Berth optimization
        # If low berth utilization, opportunity for efficiency
        utilization = await self._calculate_berth_utilization(site_id, start_date)
        if utilization < 60:
            opportunities.append({
                "opportunity_type": "capacity_available",
                "description": "Berth capacity underutilized",
                "current_utilization": utilization,
                "potential_increase": 40,
                "benefit": "Can handle 40% more ships without infrastructure investment",
                "recommendation": "Sales team: promote available capacity"
            })

        return opportunities[:10]

    async def _get_health_trend(self, site_id: int) -> str:
        """Calculate health trend (improving, stable, declining)."""
        # Simple implementation - compare last 7 days vs previous 7 days
        try:
            # Last 7 days
            recent_query = select(func.avg(Asset.health_score)).where(
                and_(
                    Asset.site_id == site_id,
                    Asset.updated_at >= datetime.utcnow() - timedelta(days=7)
                )
            )
            recent_result = await self.db.execute(recent_query)
            recent_avg = recent_result.scalar() or 0

            # Previous 7 days
            previous_query = select(func.avg(Asset.health_score)).where(
                and_(
                    Asset.site_id == site_id,
                    Asset.updated_at.between(
                        datetime.utcnow() - timedelta(days=14),
                        datetime.utcnow() - timedelta(days=7)
                    )
                )
            )
            previous_result = await self.db.execute(previous_query)
            previous_avg = previous_result.scalar() or 0

            if previous_avg == 0:
                return "stable"

            change = ((recent_avg - previous_avg) / previous_avg) * 100

            if change > 2:
                return "improving"
            elif change < -2:
                return "declining"
            else:
                return "stable"
        except:
            return "stable"

    async def _calculate_berth_utilization(
        self,
        site_id: int,
        start_date: datetime
    ) -> float:
        """Calculate berth utilization percentage."""
        try:
            # Get total berths (TODO: Implement Berth model)
            # For now, assume 4 berths per site
            total_berths = 4

            # Get ships in period
            ships_query = select(func.count(ShipLoading.id)).where(
                and_(
                    ShipLoading.site_id == site_id,
                    ShipLoading.scheduled_arrival >= start_date
                )
            )
            ships_result = await self.db.execute(ships_query)
            total_ships = ships_result.scalar() or 0

            # Simple calculation: (ships / (berths * days)) * 100
            # Assumes each ship takes ~2 days
            days = max(1, (datetime.utcnow() - start_date).days)
            max_capacity = total_berths * days * 0.5  # 0.5 ships per berth per day
            utilization = (total_ships / max_capacity * 100) if max_capacity > 0 else 0

            return round(min(100, utilization), 1)
        except:
            return 0.0

    async def _calculate_efficiency_score(
        self,
        site_id: int,
        start_date: datetime
    ) -> float:
        """Calculate overall operational efficiency score (0-100)."""
        try:
            # Factors: berth utilization, avg processing time, completion rate
            berth_util = await self._calculate_berth_utilization(site_id, start_date)

            # Processing time score (lower is better, assume 2h is optimal)
            avg_time_query = select(
                func.avg(
                    func.extract('epoch', TruckEntry.exit_time - TruckEntry.entry_time) / 3600
                )
            ).where(
                and_(
                    TruckEntry.site_id == site_id,
                    TruckEntry.entry_time >= start_date,
                    TruckEntry.exit_time.isnot(None)
                )
            )
            avg_time_result = await self.db.execute(avg_time_query)
            avg_time = avg_time_result.scalar() or 2

            time_score = max(0, 100 - ((avg_time - 2) / 2 * 50))  # 2h baseline

            # Completion rate
            ships_query = select(func.count(ShipLoading.id)).where(
                and_(
                    ShipLoading.site_id == site_id,
                    ShipLoading.scheduled_arrival >= start_date
                )
            )
            ships_result = await self.db.execute(ships_query)
            total_ships = ships_result.scalar() or 0

            completed_query = select(func.count(ShipLoading.id)).where(
                and_(
                    ShipLoading.site_id == site_id,
                    ShipLoading.scheduled_arrival >= start_date,
                    ShipLoading.status == "completed"
                )
            )
            completed_result = await self.db.execute(completed_query)
            completed = completed_result.scalar() or 0

            completion_score = (completed / total_ships * 100) if total_ships > 0 else 100

            # Weighted average
            efficiency = (berth_util * 0.3 + time_score * 0.3 + completion_score * 0.4)

            return round(efficiency, 1)
        except:
            return 75.0  # Default

    def _calculate_overall_health(
        self,
        maintenance_kpis: Dict[str, Any],
        operational_kpis: Dict[str, Any],
        asset_health: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall terminal health score."""

        # Weighted scoring
        maintenance_score = maintenance_kpis.get("average_health_score", 0)
        efficiency_score = operational_kpis.get("efficiency_score", 0)

        overall_score = (maintenance_score * 0.6 + efficiency_score * 0.4)

        # Determine status
        if overall_score >= 80:
            status = "excellent"
            color = "green"
        elif overall_score >= 60:
            status = "good"
            color = "blue"
        elif overall_score >= 40:
            status = "warning"
            color = "yellow"
        else:
            status = "critical"
            color = "red"

        return {
            "score": round(overall_score, 1),
            "status": status,
            "color": color,
            "maintenance_component": round(maintenance_score, 1),
            "operations_component": round(efficiency_score, 1)
        }
