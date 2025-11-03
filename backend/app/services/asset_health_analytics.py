"""
Asset Health Analytics Service

Provides trend analysis, pattern detection, and predictive insights
based on historical health data.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from uuid import UUID
import statistics

from app.models.asset import Asset
from app.models.asset_health_history import AssetHealthHistory
from app.services.asset_health import AssetHealthCalculator

logger = logging.getLogger(__name__)


class AssetHealthAnalytics:
    """
    Analytics service for asset health trends and predictions
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.health_calculator = AssetHealthCalculator(db)

    async def record_health_snapshot(self, asset_id: str) -> Optional[AssetHealthHistory]:
        """
        Record a health snapshot for an asset

        Returns:
            AssetHealthHistory instance if successful
        """
        try:
            # Get asset
            result = await self.db.execute(
                select(Asset).where(Asset.id == UUID(asset_id))
            )
            asset = result.scalar_one_or_none()

            if not asset:
                logger.error(f"Asset {asset_id} not found")
                return None

            # Calculate current health
            health_data = await self.health_calculator.calculate_asset_health(asset_id)

            # Get previous snapshot for trend calculation
            previous_result = await self.db.execute(
                select(AssetHealthHistory)
                .where(AssetHealthHistory.asset_id == UUID(asset_id))
                .order_by(desc(AssetHealthHistory.snapshot_time))
                .limit(1)
            )
            previous_snapshot = previous_result.scalar_one_or_none()

            # Create new snapshot
            snapshot = AssetHealthHistory.create_snapshot(
                asset=asset,
                health_data=health_data,
                previous_snapshot=previous_snapshot
            )

            self.db.add(snapshot)
            await self.db.commit()
            await self.db.refresh(snapshot)

            logger.debug(
                f"Health snapshot recorded for {asset.name}: "
                f"Score={snapshot.health_score:.1f}, Trend={snapshot.trend_direction}"
            )

            return snapshot

        except Exception as e:
            logger.error(f"Error recording health snapshot for {asset_id}: {e}")
            await self.db.rollback()
            return None

    async def get_health_trend(
        self,
        asset_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get health trend data for an asset

        Args:
            asset_id: Asset UUID
            start_time: Start of time range (default: 7 days ago)
            end_time: End of time range (default: now)
            limit: Maximum number of points

        Returns:
            List of health snapshots
        """
        try:
            if not end_time:
                end_time = datetime.utcnow()
            if not start_time:
                start_time = end_time - timedelta(days=7)

            result = await self.db.execute(
                select(AssetHealthHistory)
                .where(
                    and_(
                        AssetHealthHistory.asset_id == UUID(asset_id),
                        AssetHealthHistory.snapshot_time >= start_time,
                        AssetHealthHistory.snapshot_time <= end_time
                    )
                )
                .order_by(AssetHealthHistory.snapshot_time)
                .limit(limit)
            )

            snapshots = result.scalars().all()
            return [snapshot.to_dict() for snapshot in snapshots]

        except Exception as e:
            logger.error(f"Error getting health trend for {asset_id}: {e}")
            return []

    async def get_trend_statistics(
        self,
        asset_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get statistical summary of health trend

        Returns:
            Dict with mean, min, max, stddev, trend, etc.
        """
        try:
            start_time = datetime.utcnow() - timedelta(days=days)

            result = await self.db.execute(
                select(AssetHealthHistory)
                .where(
                    and_(
                        AssetHealthHistory.asset_id == UUID(asset_id),
                        AssetHealthHistory.snapshot_time >= start_time
                    )
                )
                .order_by(AssetHealthHistory.snapshot_time)
            )

            snapshots = result.scalars().all()

            if not snapshots:
                return {
                    "error": "No historical data available",
                    "days": days
                }

            scores = [s.health_score for s in snapshots]

            # Calculate statistics
            stats = {
                "period_days": days,
                "data_points": len(scores),
                "mean_score": statistics.mean(scores),
                "median_score": statistics.median(scores),
                "min_score": min(scores),
                "max_score": max(scores),
                "stddev": statistics.stdev(scores) if len(scores) > 1 else 0,
                "current_score": scores[-1],
                "first_score": scores[0],
                "total_change": scores[-1] - scores[0],
            }

            # Determine overall trend
            if stats["total_change"] > 5:
                stats["overall_trend"] = "improving"
            elif stats["total_change"] < -5:
                stats["overall_trend"] = "degrading"
            else:
                stats["overall_trend"] = "stable"

            # Calculate volatility (coefficient of variation)
            if stats["mean_score"] > 0:
                stats["volatility"] = (stats["stddev"] / stats["mean_score"]) * 100
            else:
                stats["volatility"] = 0

            # Count trend changes
            improving_count = sum(1 for s in snapshots if s.trend_direction == "improving")
            degrading_count = sum(1 for s in snapshots if s.trend_direction == "degrading")
            stable_count = sum(1 for s in snapshots if s.trend_direction == "stable")

            stats["trend_distribution"] = {
                "improving": improving_count,
                "degrading": degrading_count,
                "stable": stable_count
            }

            return stats

        except Exception as e:
            logger.error(f"Error calculating trend statistics: {e}")
            return {"error": str(e)}

    async def compare_periods(
        self,
        asset_id: str,
        period1_days: int = 7,
        period2_days: int = 7
    ) -> Dict[str, Any]:
        """
        Compare two time periods for an asset

        Args:
            period1_days: Days in period 1 (most recent)
            period2_days: Days in period 2 (before period 1)

        Returns:
            Comparison metrics
        """
        try:
            now = datetime.utcnow()
            period1_start = now - timedelta(days=period1_days)
            period2_start = period1_start - timedelta(days=period2_days)
            period2_end = period1_start

            # Get period 1 data (recent)
            result1 = await self.db.execute(
                select(AssetHealthHistory)
                .where(
                    and_(
                        AssetHealthHistory.asset_id == UUID(asset_id),
                        AssetHealthHistory.snapshot_time >= period1_start
                    )
                )
            )
            period1_snapshots = result1.scalars().all()

            # Get period 2 data (previous)
            result2 = await self.db.execute(
                select(AssetHealthHistory)
                .where(
                    and_(
                        AssetHealthHistory.asset_id == UUID(asset_id),
                        AssetHealthHistory.snapshot_time >= period2_start,
                        AssetHealthHistory.snapshot_time < period2_end
                    )
                )
            )
            period2_snapshots = result2.scalars().all()

            if not period1_snapshots or not period2_snapshots:
                return {"error": "Insufficient data for comparison"}

            # Calculate metrics for each period
            period1_scores = [s.health_score for s in period1_snapshots]
            period2_scores = [s.health_score for s in period2_snapshots]

            comparison = {
                "period1": {
                    "days": period1_days,
                    "start": period1_start.isoformat(),
                    "end": now.isoformat(),
                    "data_points": len(period1_scores),
                    "mean_score": statistics.mean(period1_scores),
                    "min_score": min(period1_scores),
                    "max_score": max(period1_scores),
                },
                "period2": {
                    "days": period2_days,
                    "start": period2_start.isoformat(),
                    "end": period2_end.isoformat(),
                    "data_points": len(period2_scores),
                    "mean_score": statistics.mean(period2_scores),
                    "min_score": min(period2_scores),
                    "max_score": max(period2_scores),
                },
            }

            # Calculate changes
            comparison["changes"] = {
                "mean_change": comparison["period1"]["mean_score"] - comparison["period2"]["mean_score"],
                "mean_change_percent": (
                    (comparison["period1"]["mean_score"] - comparison["period2"]["mean_score"]) /
                    comparison["period2"]["mean_score"] * 100
                ) if comparison["period2"]["mean_score"] > 0 else 0,
            }

            # Determine if improvement or degradation
            if comparison["changes"]["mean_change"] > 2:
                comparison["assessment"] = "improved"
            elif comparison["changes"]["mean_change"] < -2:
                comparison["assessment"] = "degraded"
            else:
                comparison["assessment"] = "stable"

            return comparison

        except Exception as e:
            logger.error(f"Error comparing periods: {e}")
            return {"error": str(e)}

    async def detect_anomalies(
        self,
        asset_id: str,
        days: int = 30,
        sensitivity: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in health score using statistical methods

        Args:
            asset_id: Asset UUID
            days: Number of days to analyze
            sensitivity: Number of standard deviations for threshold (default: 2.0)

        Returns:
            List of detected anomalies
        """
        try:
            start_time = datetime.utcnow() - timedelta(days=days)

            result = await self.db.execute(
                select(AssetHealthHistory)
                .where(
                    and_(
                        AssetHealthHistory.asset_id == UUID(asset_id),
                        AssetHealthHistory.snapshot_time >= start_time
                    )
                )
                .order_by(AssetHealthHistory.snapshot_time)
            )

            snapshots = result.scalars().all()

            if len(snapshots) < 10:
                return []

            scores = [s.health_score for s in snapshots]
            mean_score = statistics.mean(scores)
            stddev = statistics.stdev(scores)

            # Detect anomalies (scores outside sensitivity * stddev)
            threshold_low = mean_score - (sensitivity * stddev)
            threshold_high = mean_score + (sensitivity * stddev)

            anomalies = []
            for snapshot in snapshots:
                if snapshot.health_score < threshold_low or snapshot.health_score > threshold_high:
                    anomalies.append({
                        "snapshot_time": snapshot.snapshot_time.isoformat(),
                        "health_score": snapshot.health_score,
                        "deviation": abs(snapshot.health_score - mean_score) / stddev if stddev > 0 else 0,
                        "type": "low" if snapshot.health_score < threshold_low else "high",
                        "mean": mean_score,
                        "stddev": stddev,
                    })

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    async def predict_maintenance_need(
        self,
        asset_id: str,
        days_history: int = 30,
        forecast_days: int = 7
    ) -> Dict[str, Any]:
        """
        Predict if asset will need maintenance based on health trends

        Uses linear regression on recent health scores to forecast

        Returns:
            Prediction with confidence level
        """
        try:
            start_time = datetime.utcnow() - timedelta(days=days_history)

            result = await self.db.execute(
                select(AssetHealthHistory)
                .where(
                    and_(
                        AssetHealthHistory.asset_id == UUID(asset_id),
                        AssetHealthHistory.snapshot_time >= start_time
                    )
                )
                .order_by(AssetHealthHistory.snapshot_time)
            )

            snapshots = result.scalars().all()

            if len(snapshots) < 5:
                return {"error": "Insufficient data for prediction"}

            # Simple linear regression
            x = list(range(len(snapshots)))
            y = [s.health_score for s in snapshots]

            # Calculate slope
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(xi * yi for xi, yi in zip(x, y))
            sum_x2 = sum(xi * xi for xi in x)

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n

            # Forecast
            last_x = len(snapshots) - 1
            current_score = y[-1]

            # Predict score in forecast_days
            # Assuming one snapshot per hour (60 cycles per day)
            forecast_x = last_x + (forecast_days * 24)  # Rough estimation
            predicted_score = slope * forecast_x + intercept

            # Limit to 0-100 range
            predicted_score = max(0, min(100, predicted_score))

            prediction = {
                "current_score": current_score,
                "predicted_score": predicted_score,
                "forecast_days": forecast_days,
                "trend_slope": slope,
                "confidence": "high" if len(snapshots) > 20 else "medium" if len(snapshots) > 10 else "low",
                "data_points": len(snapshots),
            }

            # Maintenance recommendation
            if predicted_score < 50 or slope < -0.5:
                prediction["maintenance_needed"] = True
                prediction["urgency"] = "high" if predicted_score < 30 else "medium"
                prediction["recommendation"] = "Schedule preventive maintenance soon"
            elif predicted_score < 70 or slope < -0.2:
                prediction["maintenance_needed"] = True
                prediction["urgency"] = "low"
                prediction["recommendation"] = "Monitor closely, plan maintenance"
            else:
                prediction["maintenance_needed"] = False
                prediction["urgency"] = "none"
                prediction["recommendation"] = "Continue normal operation"

            return prediction

        except Exception as e:
            logger.error(f"Error predicting maintenance: {e}")
            return {"error": str(e)}

    async def get_attribute_trends(
        self,
        asset_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get trend data for individual attributes

        Returns:
            Attribute-level trend analysis
        """
        try:
            start_time = datetime.utcnow() - timedelta(days=days)

            result = await self.db.execute(
                select(AssetHealthHistory)
                .where(
                    and_(
                        AssetHealthHistory.asset_id == UUID(asset_id),
                        AssetHealthHistory.snapshot_time >= start_time
                    )
                )
                .order_by(AssetHealthHistory.snapshot_time)
            )

            snapshots = result.scalars().all()

            if not snapshots:
                return {}

            # Collect attribute scores over time
            attribute_data = {}

            for snapshot in snapshots:
                for attr_name, attr_scores in snapshot.attribute_scores.items():
                    if attr_name not in attribute_data:
                        attribute_data[attr_name] = []

                    attribute_data[attr_name].append({
                        "time": snapshot.snapshot_time.isoformat(),
                        "score": attr_scores.get("score", 100),
                        "value": attr_scores.get("value"),
                        "status": attr_scores.get("status", "unknown")
                    })

            # Calculate statistics for each attribute
            attribute_trends = {}
            for attr_name, data_points in attribute_data.items():
                scores = [d["score"] for d in data_points]

                attribute_trends[attr_name] = {
                    "data_points": data_points,
                    "current_score": scores[-1] if scores else 0,
                    "mean_score": statistics.mean(scores) if scores else 0,
                    "min_score": min(scores) if scores else 0,
                    "max_score": max(scores) if scores else 0,
                    "trend": "degrading" if scores[-1] < scores[0] - 5 else "improving" if scores[-1] > scores[0] + 5 else "stable"
                }

            return attribute_trends

        except Exception as e:
            logger.error(f"Error getting attribute trends: {e}")
            return {}
