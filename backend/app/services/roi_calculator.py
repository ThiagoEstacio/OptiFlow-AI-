"""
ROI Calculator Service

Calculates Return on Investment by measuring:
- Downtime costs avoided through predictive maintenance
- Operational efficiency gains
- Cost savings from optimization
- Overall financial impact of OptiFlow AI
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from app.models.asset import Asset, AssetType
from app.models.alarm import Alarm, AlarmSeverity
from app.models.operations import TruckEntry, ShipLoading, Silo

logger = logging.getLogger(__name__)


class ROICalculator:
    """
    Calculate Return on Investment and demonstrate business value.

    This service quantifies the financial impact of OptiFlow AI by tracking:
    - Prevented failures and avoided downtime costs
    - Operational efficiency improvements
    - Resource optimization savings
    - Overall cost reductions
    """

    # Cost assumptions (configurable per client)
    DEFAULT_HOURLY_DOWNTIME_COST = 5000  # $/hour
    DEFAULT_SHIP_DELAY_COST_PER_HOUR = 8000  # $/hour
    DEFAULT_EMERGENCY_MAINTENANCE_MULTIPLIER = 2.5  # vs planned maintenance
    DEFAULT_PLANNED_MAINTENANCE_COST = 3000  # $ per maintenance
    DEFAULT_FAILURE_COST = 25000  # $ average failure cost

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_roi(
        self,
        site_id: int,
        period_days: int = 30,
        custom_costs: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive ROI for a period.

        Args:
            site_id: Site identifier
            period_days: Analysis period (default: 30 days)
            custom_costs: Optional custom cost parameters

        Returns:
            Complete ROI analysis with costs avoided, savings, and projections
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=period_days)

            # Apply custom costs if provided
            costs = self._get_cost_parameters(custom_costs)

            # Calculate all ROI components
            predictive_maintenance_roi = await self._calculate_predictive_maintenance_roi(
                site_id, start_date, costs
            )
            optimization_roi = await self._calculate_optimization_roi(
                site_id, start_date, costs
            )
            efficiency_roi = await self._calculate_efficiency_roi(
                site_id, start_date, costs
            )
            downtime_avoided = await self._calculate_downtime_avoided(
                site_id, start_date, costs
            )

            # Calculate totals
            total_savings = (
                predictive_maintenance_roi.get("total_savings", 0) +
                optimization_roi.get("total_savings", 0) +
                efficiency_roi.get("total_savings", 0) +
                downtime_avoided.get("total_cost_avoided", 0)
            )

            # Project annual savings
            daily_avg = total_savings / period_days
            annual_projection = daily_avg * 365

            # Calculate ROI percentage (assuming OptiFlow AI cost)
            # This should be customized per client
            estimated_system_cost_annual = 50000  # Example: $50k/year
            roi_percentage = ((annual_projection - estimated_system_cost_annual) /
                            estimated_system_cost_annual * 100)

            return {
                "status": "success",
                "site_id": site_id,
                "period_days": period_days,
                "analysis_date": datetime.utcnow().isoformat(),

                # Detailed breakdowns
                "predictive_maintenance": predictive_maintenance_roi,
                "optimization": optimization_roi,
                "efficiency": efficiency_roi,
                "downtime_avoided": downtime_avoided,

                # Summary
                "total_savings": round(total_savings, 2),
                "daily_average_savings": round(daily_avg, 2),
                "annual_projection": round(annual_projection, 2),

                # ROI metrics
                "roi_percentage": round(roi_percentage, 1),
                "payback_period_months": round(estimated_system_cost_annual / (daily_avg * 30), 1) if daily_avg > 0 else 0,

                # Key highlights
                "highlights": self._generate_highlights(
                    total_savings,
                    predictive_maintenance_roi,
                    optimization_roi,
                    downtime_avoided
                )
            }

        except Exception as e:
            logger.error(f"Error calculating ROI: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def _calculate_predictive_maintenance_roi(
        self,
        site_id: int,
        start_date: datetime,
        costs: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate ROI from predictive maintenance preventing failures.

        Key assumption: Catching issues early saves emergency repair costs.
        """

        # Count predicted failures that triggered preventive maintenance
        # In real implementation, track predictions that led to maintenance
        predicted_failures_prevented = await self._count_predicted_failures_prevented(
            site_id, start_date
        )

        # Cost comparison: planned vs emergency maintenance
        planned_cost = costs["planned_maintenance_cost"] * predicted_failures_prevented
        emergency_cost_if_failed = (
            costs["failure_cost"] +
            costs["hourly_downtime_cost"] * 4  # Assume 4h downtime per failure
        ) * predicted_failures_prevented

        savings = emergency_cost_if_failed - planned_cost

        # Additional savings from extended asset life
        # Preventive maintenance extends life by ~20%
        asset_life_extension_value = planned_cost * 0.2

        total_savings = savings + asset_life_extension_value

        return {
            "failures_prevented": predicted_failures_prevented,
            "planned_maintenance_cost": round(planned_cost, 2),
            "emergency_cost_avoided": round(emergency_cost_if_failed, 2),
            "asset_life_extension_value": round(asset_life_extension_value, 2),
            "total_savings": round(total_savings, 2),
            "breakdown": [
                {
                    "category": "Emergency repair costs avoided",
                    "amount": round(emergency_cost_if_failed - planned_cost, 2)
                },
                {
                    "category": "Asset life extension",
                    "amount": round(asset_life_extension_value, 2)
                }
            ]
        }

    async def _calculate_optimization_roi(
        self,
        site_id: int,
        start_date: datetime,
        costs: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate ROI from operational optimizations (berth allocation, loading sequence).
        """

        # Calculate time savings from berth optimization
        # Assumption: Optimization reduces avg ship waiting time by 20%
        ships_query = select(func.count(ShipLoading.id)).where(
            and_(
                ShipLoading.site_id == site_id,
                ShipLoading.scheduled_arrival >= start_date,
                ShipLoading.status.in_(["completed", "loading"])
            )
        )
        ships_result = await self.db.execute(ships_query)
        total_ships = ships_result.scalar() or 0

        # Estimate baseline waiting time: 8 hours per ship (industry avg)
        baseline_waiting_hours = total_ships * 8
        optimized_waiting_hours = baseline_waiting_hours * 0.8  # 20% reduction
        hours_saved = baseline_waiting_hours - optimized_waiting_hours

        ship_delay_savings = hours_saved * costs["ship_delay_cost_per_hour"]

        # Loading sequence optimization
        # Assumption: Optimal sequence reduces loading time by 10%
        loading_time_saved_hours = total_ships * 30 * 0.1  # 30h avg per ship, 10% savings
        loading_efficiency_savings = loading_time_saved_hours * costs["hourly_downtime_cost"]

        # Berth utilization improvement
        # Better allocation = more ships handled with same infrastructure
        berth_capacity_improvement = total_ships * 0.05  # 5% more capacity
        capacity_value = berth_capacity_improvement * 50000  # Revenue per ship

        total_savings = ship_delay_savings + loading_efficiency_savings + capacity_value

        return {
            "ships_optimized": total_ships,
            "waiting_hours_saved": round(hours_saved, 1),
            "loading_hours_saved": round(loading_time_saved_hours, 1),
            "ship_delay_savings": round(ship_delay_savings, 2),
            "loading_efficiency_savings": round(loading_efficiency_savings, 2),
            "capacity_improvement_value": round(capacity_value, 2),
            "total_savings": round(total_savings, 2),
            "breakdown": [
                {
                    "category": "Reduced ship waiting time",
                    "amount": round(ship_delay_savings, 2)
                },
                {
                    "category": "Optimized loading sequences",
                    "amount": round(loading_efficiency_savings, 2)
                },
                {
                    "category": "Capacity improvement",
                    "amount": round(capacity_value, 2)
                }
            ]
        }

    async def _calculate_efficiency_roi(
        self,
        site_id: int,
        start_date: datetime,
        costs: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate ROI from operational efficiency improvements.
        """

        # Truck processing efficiency
        trucks_query = select(func.count(TruckEntry.id)).where(
            and_(
                TruckEntry.site_id == site_id,
                TruckEntry.entry_time >= start_date
            )
        )
        trucks_result = await self.db.execute(trucks_query)
        total_trucks = trucks_result.scalar() or 0

        # Average time saved per truck: 15 minutes with OptiFlow AI optimizations
        minutes_saved_per_truck = 15
        total_hours_saved = (total_trucks * minutes_saved_per_truck) / 60

        # Cost of driver waiting time: $50/hour
        driver_time_savings = total_hours_saved * 50

        # Fuel savings (trucks idling less)
        # $5 per truck in fuel savings
        fuel_savings = total_trucks * 5

        # Reduced overtime due to better planning
        # Estimate 10% reduction in overtime hours
        # Assume 100 labor hours per week at $40/hour overtime
        overtime_hours_saved = ((datetime.utcnow() - start_date).days / 7) * 100 * 0.1
        overtime_savings = overtime_hours_saved * 40

        total_savings = driver_time_savings + fuel_savings + overtime_savings

        return {
            "trucks_processed": total_trucks,
            "processing_hours_saved": round(total_hours_saved, 1),
            "driver_time_savings": round(driver_time_savings, 2),
            "fuel_savings": round(fuel_savings, 2),
            "overtime_savings": round(overtime_savings, 2),
            "total_savings": round(total_savings, 2),
            "breakdown": [
                {
                    "category": "Driver waiting time reduced",
                    "amount": round(driver_time_savings, 2)
                },
                {
                    "category": "Fuel savings",
                    "amount": round(fuel_savings, 2)
                },
                {
                    "category": "Overtime reduction",
                    "amount": round(overtime_savings, 2)
                }
            ]
        }

    async def _calculate_downtime_avoided(
        self,
        site_id: int,
        start_date: datetime,
        costs: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate downtime costs avoided through monitoring and alerts.
        """

        # Count critical alarms that were addressed quickly
        critical_alarms_query = select(func.count(Alarm.id)).where(
            and_(
                Alarm.site_id == site_id,
                Alarm.timestamp >= start_date,
                Alarm.severity == AlarmSeverity.CRITICAL,
                Alarm.acknowledged == True
            )
        )
        critical_result = await self.db.execute(critical_alarms_query)
        critical_alarms_handled = critical_result.scalar() or 0

        # Assumption: Each quickly-handled critical alarm prevents 2h of downtime
        downtime_hours_avoided = critical_alarms_handled * 2
        downtime_cost_avoided = downtime_hours_avoided * costs["hourly_downtime_cost"]

        # Secondary impacts avoided
        # Each major downtime affects: ships, trucks, labor
        ships_disruption_avoided = critical_alarms_handled * 0.3  # 30% chance each alarm affects ship
        ship_disruption_cost = ships_disruption_avoided * costs["ship_delay_cost_per_hour"] * 4

        total_cost_avoided = downtime_cost_avoided + ship_disruption_cost

        return {
            "critical_alarms_handled": critical_alarms_handled,
            "downtime_hours_avoided": round(downtime_hours_avoided, 1),
            "downtime_cost_avoided": round(downtime_cost_avoided, 2),
            "ship_disruption_cost_avoided": round(ship_disruption_cost, 2),
            "total_cost_avoided": round(total_cost_avoided, 2),
            "breakdown": [
                {
                    "category": "Direct downtime costs avoided",
                    "amount": round(downtime_cost_avoided, 2)
                },
                {
                    "category": "Ship disruption avoided",
                    "amount": round(ship_disruption_cost, 2)
                }
            ]
        }

    async def _count_predicted_failures_prevented(
        self,
        site_id: int,
        start_date: datetime
    ) -> int:
        """
        Count failures prevented through predictive maintenance.

        In production, this should track:
        - ML predictions with high failure probability
        - Followed by maintenance action
        - Where no failure occurred after maintenance
        """

        # For now, estimate based on assets with low health that were maintained
        maintained_assets_query = select(func.count(Asset.id)).where(
            and_(
                Asset.site_id == site_id,
                Asset.health_score < 60,
                Asset.last_maintenance >= start_date
            )
        )
        result = await self.db.execute(maintained_assets_query)
        count = result.scalar() or 0

        # Conservative estimate: 70% of these would have failed without intervention
        return int(count * 0.7)

    def _get_cost_parameters(
        self,
        custom_costs: Optional[Dict[str, float]]
    ) -> Dict[str, float]:
        """Get cost parameters with defaults or custom values."""
        defaults = {
            "hourly_downtime_cost": self.DEFAULT_HOURLY_DOWNTIME_COST,
            "ship_delay_cost_per_hour": self.DEFAULT_SHIP_DELAY_COST_PER_HOUR,
            "emergency_maintenance_multiplier": self.DEFAULT_EMERGENCY_MAINTENANCE_MULTIPLIER,
            "planned_maintenance_cost": self.DEFAULT_PLANNED_MAINTENANCE_COST,
            "failure_cost": self.DEFAULT_FAILURE_COST
        }

        if custom_costs:
            defaults.update(custom_costs)

        return defaults

    def _generate_highlights(
        self,
        total_savings: float,
        predictive_maintenance: Dict[str, Any],
        optimization: Dict[str, Any],
        downtime: Dict[str, Any]
    ) -> List[str]:
        """Generate key highlights for executive summary."""

        highlights = []

        # Total savings highlight
        if total_savings > 100000:
            highlights.append(
                f"💰 Generated ${total_savings:,.0f} in total savings this period"
            )

        # Failures prevented
        failures = predictive_maintenance.get("failures_prevented", 0)
        if failures > 0:
            highlights.append(
                f"🛡️ Prevented {failures} equipment failures through predictive maintenance"
            )

        # Downtime avoided
        hours = downtime.get("downtime_hours_avoided", 0)
        if hours > 0:
            highlights.append(
                f"⚡ Avoided {hours:.1f} hours of unplanned downtime"
            )

        # Ship optimization
        ships = optimization.get("ships_optimized", 0)
        if ships > 0:
            hours_saved = optimization.get("waiting_hours_saved", 0)
            highlights.append(
                f"🚢 Optimized {ships} ship loadings, saving {hours_saved:.1f} waiting hours"
            )

        # Efficiency
        trucks = optimization.get("ships_optimized", 0)
        if trucks > 50:
            highlights.append(
                f"📦 Processed {trucks}+ operations with improved efficiency"
            )

        # Cost per category
        if predictive_maintenance.get("total_savings", 0) > total_savings * 0.3:
            highlights.append(
                "🔧 Predictive maintenance was the highest ROI contributor"
            )

        return highlights[:5]  # Top 5 highlights

    async def get_monthly_trend(
        self,
        site_id: int,
        months: int = 6
    ) -> Dict[str, Any]:
        """Get monthly ROI trend for the last N months."""
        try:
            monthly_data = []

            for month_offset in range(months):
                end_date = datetime.utcnow() - timedelta(days=30 * month_offset)
                start_date = end_date - timedelta(days=30)

                # Calculate ROI for this month
                roi_data = await self.calculate_roi(site_id, period_days=30)

                if roi_data.get("status") == "success":
                    monthly_data.append({
                        "month": end_date.strftime("%Y-%m"),
                        "total_savings": roi_data.get("total_savings", 0),
                        "failures_prevented": roi_data.get("predictive_maintenance", {}).get("failures_prevented", 0),
                        "downtime_avoided_hours": roi_data.get("downtime_avoided", {}).get("downtime_hours_avoided", 0)
                    })

            return {
                "status": "success",
                "site_id": site_id,
                "months": months,
                "trend_data": list(reversed(monthly_data)),  # Oldest to newest
                "total_savings_6months": sum(m["total_savings"] for m in monthly_data)
            }

        except Exception as e:
            logger.error(f"Error calculating monthly trend: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def get_cost_benefit_analysis(
        self,
        site_id: int,
        system_cost_annual: float = 50000
    ) -> Dict[str, Any]:
        """
        Comprehensive cost-benefit analysis for executives.

        Compares system cost vs benefits over time periods.
        """
        try:
            # Calculate ROI for different periods
            monthly_roi = await self.calculate_roi(site_id, period_days=30)
            quarterly_roi = await self.calculate_roi(site_id, period_days=90)

            if monthly_roi.get("status") != "success":
                return monthly_roi

            annual_projection = monthly_roi.get("annual_projection", 0)
            monthly_avg = monthly_roi.get("daily_average_savings", 0) * 30

            # Calculate break-even
            monthly_system_cost = system_cost_annual / 12
            net_monthly_benefit = monthly_avg - monthly_system_cost
            break_even_months = (system_cost_annual / monthly_avg) if monthly_avg > 0 else 0

            # ROI by category
            categories = {
                "Predictive Maintenance": monthly_roi.get("predictive_maintenance", {}).get("total_savings", 0),
                "Optimization": monthly_roi.get("optimization", {}).get("total_savings", 0),
                "Efficiency": monthly_roi.get("efficiency", {}).get("total_savings", 0),
                "Downtime Avoided": monthly_roi.get("downtime_avoided", {}).get("total_cost_avoided", 0)
            }

            return {
                "status": "success",
                "site_id": site_id,
                "analysis_date": datetime.utcnow().isoformat(),

                # Investment
                "annual_system_cost": system_cost_annual,
                "monthly_system_cost": round(monthly_system_cost, 2),

                # Returns
                "monthly_benefits": round(monthly_avg, 2),
                "annual_benefits_projection": round(annual_projection, 2),

                # Net benefit
                "net_monthly_benefit": round(net_monthly_benefit, 2),
                "net_annual_benefit": round(annual_projection - system_cost_annual, 2),

                # Ratios
                "benefit_cost_ratio": round(annual_projection / system_cost_annual, 2),
                "roi_percentage": round(((annual_projection - system_cost_annual) / system_cost_annual * 100), 1),
                "break_even_months": round(break_even_months, 1),

                # Breakdown by category
                "benefits_by_category": {
                    k: round(v, 2) for k, v in sorted(
                        categories.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                },

                # Executive summary
                "executive_summary": self._generate_executive_summary(
                    annual_projection,
                    system_cost_annual,
                    net_monthly_benefit,
                    break_even_months
                )
            }

        except Exception as e:
            logger.error(f"Error calculating cost-benefit: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def _generate_executive_summary(
        self,
        annual_projection: float,
        system_cost: float,
        net_monthly: float,
        break_even: float
    ) -> str:
        """Generate executive summary text."""

        roi_pct = ((annual_projection - system_cost) / system_cost * 100)

        summary = f"""
OptiFlow AI delivers strong ROI with ${annual_projection:,.0f} in projected annual benefits
against ${system_cost:,.0f} investment ({roi_pct:.0f}% ROI).

System generates positive net cash flow of ${net_monthly:,.0f} per month and reaches
break-even in {break_even:.1f} months.

Key value drivers: predictive maintenance preventing costly failures, operational optimization
reducing wait times, and real-time monitoring avoiding unplanned downtime.
        """.strip()

        return summary
