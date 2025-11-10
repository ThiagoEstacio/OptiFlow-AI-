"""
Pareto Analyzer

Generates Pareto charts and analysis for failure frequency analysis.
Implements the 80/20 rule to identify the most impactful issues.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text
from collections import Counter

from app.models.asset import Asset
from app.models.alarm import AlarmDefinition

logger = logging.getLogger(__name__)


class ParetoAnalyzer:
    """
    Engineering tool for Pareto analysis.

    Creates Pareto charts showing:
    - Failure frequency by type
    - Cumulative percentage
    - 80/20 identification
    - Priority recommendations
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_pareto(
        self,
        asset_id: Optional[str] = None,
        site_id: Optional[int] = None,
        days: int = 30,
        min_occurrences: int = 1
    ) -> Dict[str, Any]:
        """
        Generate Pareto analysis for failures.

        Args:
            asset_id: Specific asset (optional)
            site_id: Specific site (optional)
            days: Number of days to analyze
            min_occurrences: Minimum occurrences to include

        Returns:
            Pareto chart data and analysis
        """
        try:
            logger.info(f"Generating Pareto analysis for {days} days")

            # Get failure data
            failures = await self._get_failures(asset_id, site_id, days)

            if not failures:
                return {
                    "status": "no_data",
                    "message": "No failure data available for analysis",
                    "items": [],
                }

            # Count failures by type
            failure_counts = Counter()
            for failure in failures:
                failure_type = failure.get('alarm_type', 'Unknown')
                failure_counts[failure_type] += 1

            # Filter by minimum occurrences
            filtered_counts = {
                k: v for k, v in failure_counts.items()
                if v >= min_occurrences
            }

            if not filtered_counts:
                return {
                    "status": "insufficient_data",
                    "message": f"No failures with at least {min_occurrences} occurrences",
                    "items": [],
                }

            # Sort by frequency (descending)
            sorted_failures = sorted(
                filtered_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # Calculate cumulative percentages
            total_count = sum(filtered_counts.values())
            cumulative = 0
            pareto_items = []

            for i, (failure_type, count) in enumerate(sorted_failures):
                percentage = (count / total_count) * 100
                cumulative += percentage

                pareto_items.append({
                    "rank": i + 1,
                    "failure_type": failure_type,
                    "count": count,
                    "percentage": round(percentage, 2),
                    "cumulative_percentage": round(cumulative, 2),
                    "is_vital_few": cumulative <= 80,  # 80/20 rule
                })

            # Identify vital few (items contributing to 80%)
            vital_few = [item for item in pareto_items if item['is_vital_few']]
            trivial_many = [item for item in pareto_items if not item['is_vital_few']]

            # Generate insights
            insights = self._generate_insights(
                pareto_items,
                vital_few,
                trivial_many,
                total_count,
                days
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(vital_few)

            result = {
                "status": "success",
                "analysis_period_days": days,
                "total_failures": total_count,
                "unique_failure_types": len(pareto_items),
                "vital_few_count": len(vital_few),
                "vital_few_percentage": round((len(vital_few) / len(pareto_items)) * 100, 1),
                "items": pareto_items,
                "vital_few": vital_few,
                "trivial_many": trivial_many,
                "insights": insights,
                "recommendations": recommendations,
                "generated_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Pareto analysis complete: {len(vital_few)} vital few, "
                f"{len(trivial_many)} trivial many"
            )

            return result

        except Exception as e:
            logger.error(f"Error generating Pareto analysis: {e}")
            raise

    async def _get_failures(
        self,
        asset_id: Optional[str],
        site_id: Optional[int],
        days: int
    ) -> List[Dict[str, Any]]:
        """Get failure records for analysis."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            query = select(AlarmDefinition).where(
                and_(
                    AlarmDefinition.triggered_at >= start_date,
                    AlarmDefinition.severity.in_(["critical", "high", "medium"])
                )
            )

            if asset_id:
                query = query.where(AlarmDefinition.asset_id == asset_id)

            if site_id:
                # Join with assets to filter by site
                query = query.join(Asset).where(Asset.site_id == site_id)

            result = await self.db.execute(query)
            alarms = result.scalars().all()

            return [
                {
                    "alarm_type": alarm.alarm_type,
                    "severity": alarm.severity,
                    "triggered_at": alarm.triggered_at.isoformat() if alarm.triggered_at else None,
                    "asset_id": alarm.asset_id,
                }
                for alarm in alarms
            ]

        except Exception as e:
            logger.error(f"Error getting failures: {e}")
            return []

    def _generate_insights(
        self,
        pareto_items: List[Dict[str, Any]],
        vital_few: List[Dict[str, Any]],
        trivial_many: List[Dict[str, Any]],
        total_count: int,
        days: int
    ) -> List[str]:
        """Generate insights from Pareto analysis."""
        insights = []

        # Vital few insight
        if vital_few:
            vital_few_failures = sum(item['count'] for item in vital_few)
            vital_few_percent = (vital_few_failures / total_count) * 100

            insights.append(
                f"Top {len(vital_few)} failure types ({len(vital_few) / len(pareto_items) * 100:.0f}% of types) "
                f"account for {vital_few_percent:.1f}% of all failures"
            )

        # Frequency insight
        avg_failures_per_day = total_count / days
        insights.append(
            f"Average of {avg_failures_per_day:.1f} failures per day over {days} days"
        )

        # Top failure insight
        if pareto_items:
            top_failure = pareto_items[0]
            insights.append(
                f"Most frequent failure: '{top_failure['failure_type']}' "
                f"({top_failure['count']} occurrences, {top_failure['percentage']:.1f}%)"
            )

        # Diversity insight
        if len(pareto_items) > 10:
            insights.append(
                f"High failure diversity detected ({len(pareto_items)} different types) - "
                f"suggests multiple underlying issues"
            )
        elif len(pareto_items) <= 3:
            insights.append(
                f"Low failure diversity ({len(pareto_items)} types) - "
                f"suggests focused problem area"
            )

        # 80/20 compliance
        if vital_few:
            actual_ratio = (len(vital_few) / len(pareto_items)) * 100
            if actual_ratio <= 20:
                insights.append(
                    f"Follows Pareto principle: {actual_ratio:.0f}% of failure types "
                    f"cause 80% of occurrences"
                )
            else:
                insights.append(
                    f"Deviation from Pareto principle: {actual_ratio:.0f}% of types "
                    f"needed to reach 80% of failures (typical is 20%)"
                )

        return insights

    def _generate_recommendations(
        self,
        vital_few: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on vital few."""
        recommendations = []

        for item in vital_few[:5]:  # Top 5 priorities
            failure_type = item['failure_type']
            count = item['count']

            # Generate failure-specific recommendations
            rec = {
                "priority": item['rank'],
                "failure_type": failure_type,
                "occurrences": count,
                "actions": self._get_failure_specific_actions(failure_type),
                "expected_impact": f"Could reduce failures by up to {item['percentage']:.1f}%",
            }

            recommendations.append(rec)

        return recommendations

    def _get_failure_specific_actions(self, failure_type: str) -> List[str]:
        """Get specific actions for a failure type."""
        failure_lower = failure_type.lower()

        # Pattern-based recommendations
        if 'temperature' in failure_lower or 'temp' in failure_lower:
            return [
                "Inspect and clean cooling system",
                "Verify ambient temperature conditions",
                "Check for excessive load or friction",
                "Review temperature sensor calibration",
            ]
        elif 'vibration' in failure_lower or 'vib' in failure_lower:
            return [
                "Perform vibration analysis",
                "Check alignment and balance",
                "Inspect bearings and mounts",
                "Verify foundation integrity",
            ]
        elif 'current' in failure_lower or 'overload' in failure_lower:
            return [
                "Review load conditions",
                "Check for mechanical binding",
                "Verify motor sizing and ratings",
                "Inspect electrical connections",
            ]
        elif 'pressure' in failure_lower:
            return [
                "Check for leaks or blockages",
                "Inspect seals and gaskets",
                "Verify pump/compressor operation",
                "Review system design pressure",
            ]
        elif 'speed' in failure_lower:
            return [
                "Inspect drive system (belts, gears)",
                "Check speed sensor calibration",
                "Verify control system settings",
                "Review load conditions",
            ]
        else:
            return [
                "Conduct root cause analysis",
                "Review maintenance procedures",
                "Inspect equipment condition",
                "Consult equipment manual",
            ]

    async def compare_periods(
        self,
        current_days: int = 30,
        previous_days: int = 30,
        asset_id: Optional[str] = None,
        site_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Compare Pareto analysis between two time periods.

        Args:
            current_days: Days in current period
            previous_days: Days in previous period
            asset_id: Specific asset (optional)
            site_id: Specific site (optional)

        Returns:
            Comparison analysis
        """
        try:
            # Generate Pareto for current period
            current = await self.generate_pareto(
                asset_id=asset_id,
                site_id=site_id,
                days=current_days
            )

            # Generate Pareto for previous period
            # Adjust date range to be before current period
            start_offset = current_days
            end_offset = current_days + previous_days

            previous_start = datetime.utcnow() - timedelta(days=end_offset)
            previous_end = datetime.utcnow() - timedelta(days=start_offset)

            # Get failures for previous period
            query = select(AlarmDefinition).where(
                and_(
                    AlarmDefinition.triggered_at >= previous_start,
                    AlarmDefinition.triggered_at <= previous_end,
                    AlarmDefinition.severity.in_(["critical", "high", "medium"])
                )
            )

            if asset_id:
                query = query.where(AlarmDefinition.asset_id == asset_id)

            if site_id:
                query = query.join(Asset).where(Asset.site_id == site_id)

            result = await self.db.execute(query)
            previous_alarms = result.scalars().all()

            previous_count = len(previous_alarms)
            current_count = current.get('total_failures', 0)

            # Calculate change
            change_percent = 0
            if previous_count > 0:
                change_percent = ((current_count - previous_count) / previous_count) * 100

            trend = "stable"
            if change_percent > 10:
                trend = "increasing"
            elif change_percent < -10:
                trend = "decreasing"

            return {
                "current_period": {
                    "days": current_days,
                    "total_failures": current_count,
                    "top_failures": current.get('vital_few', [])[:3],
                },
                "previous_period": {
                    "days": previous_days,
                    "total_failures": previous_count,
                },
                "comparison": {
                    "absolute_change": current_count - previous_count,
                    "percent_change": round(change_percent, 1),
                    "trend": trend,
                },
                "analysis": f"Failures {trend} by {abs(change_percent):.1f}% compared to previous period",
            }

        except Exception as e:
            logger.error(f"Error comparing periods: {e}")
            raise
