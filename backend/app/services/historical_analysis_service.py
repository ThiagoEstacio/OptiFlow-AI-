"""
Historical Analysis Service

Provides historical trend analysis and month-over-month comparisons:
- Time-series analysis
- Month-over-month comparisons
- Year-over-year comparisons
- Trend detection
- Seasonal analysis
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
import pandas as pd
import numpy as np

from app.models.external_data import GBMLogisticsData
from app.models.operational_data import DailyOperations, TruckEntry, ShipLoading
from app.core.logging import get_logger

logger = get_logger(__name__)


class HistoricalAnalysisService:
    """
    Service for historical data analysis and comparisons.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== MONTHLY COMPARISONS ====================

    async def get_monthly_comparison(
        self,
        site_id: int,
        months: int = 12,
        metric: str = "all"
    ) -> Dict[str, Any]:
        """
        Get month-over-month comparison for the last N months.

        Args:
            site_id: Site ID
            months: Number of months to compare (default 12)
            metric: Specific metric or "all"

        Returns:
            Monthly data with MoM comparisons
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - relativedelta(months=months)

        # Get GBM data grouped by month
        result = await self.db.execute(
            select(
                func.date_trunc('month', GBMLogisticsData.operation_date).label('month'),
                func.count(GBMLogisticsData.id).label('operations'),
                func.sum(GBMLogisticsData.net_weight_kg).label('total_weight'),
                func.avg(GBMLogisticsData.loading_time_minutes).label('avg_loading_time'),
                func.avg(GBMLogisticsData.waiting_time_minutes).label('avg_waiting_time'),
                func.sum(GBMLogisticsData.total_value).label('total_revenue')
            ).where(
                and_(
                    GBMLogisticsData.site_id == site_id,
                    GBMLogisticsData.operation_date >= start_date,
                    GBMLogisticsData.operation_date <= end_date
                )
            ).group_by(
                func.date_trunc('month', GBMLogisticsData.operation_date)
            ).order_by(
                func.date_trunc('month', GBMLogisticsData.operation_date)
            )
        )

        monthly_data = []
        rows = result.all()

        for i, row in enumerate(rows):
            month_data = {
                "month": row.month.strftime("%Y-%m") if row.month else None,
                "month_name": row.month.strftime("%B %Y") if row.month else None,
                "operations": int(row.operations) if row.operations else 0,
                "total_tonnage": float(row.total_weight / 1000) if row.total_weight else 0,
                "avg_loading_time": float(row.avg_loading_time) if row.avg_loading_time else 0,
                "avg_waiting_time": float(row.avg_waiting_time) if row.avg_waiting_time else 0,
                "total_revenue": float(row.total_revenue) if row.total_revenue else 0,
            }

            # Calculate MoM change if not first month
            if i > 0:
                prev_row = rows[i - 1]
                month_data["mom_operations"] = self._calculate_change_percent(
                    row.operations, prev_row.operations
                )
                month_data["mom_tonnage"] = self._calculate_change_percent(
                    row.total_weight, prev_row.total_weight
                )
                month_data["mom_loading_time"] = self._calculate_change_percent(
                    row.avg_loading_time, prev_row.avg_loading_time
                )
                month_data["mom_revenue"] = self._calculate_change_percent(
                    row.total_revenue, prev_row.total_revenue
                )
            else:
                month_data["mom_operations"] = 0
                month_data["mom_tonnage"] = 0
                month_data["mom_loading_time"] = 0
                month_data["mom_revenue"] = 0

            monthly_data.append(month_data)

        # Calculate YoY if we have 12+ months
        if len(monthly_data) >= 12:
            for i in range(len(monthly_data)):
                if i >= 12:
                    yoy_index = i - 12
                    monthly_data[i]["yoy_operations"] = self._calculate_change_percent(
                        monthly_data[i]["operations"],
                        monthly_data[yoy_index]["operations"]
                    )
                    monthly_data[i]["yoy_tonnage"] = self._calculate_change_percent(
                        monthly_data[i]["total_tonnage"],
                        monthly_data[yoy_index]["total_tonnage"]
                    )

        return {
            "status": "success",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "months": len(monthly_data)
            },
            "monthly_data": monthly_data,
            "summary": self._calculate_summary_stats(monthly_data)
        }

    # ==================== TREND ANALYSIS ====================

    async def get_trend_analysis(
        self,
        site_id: int,
        metric: str,
        period_days: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze trend for a specific metric over time.

        Args:
            site_id: Site ID
            metric: Metric to analyze (tonnage, operations, loading_time, etc.)
            period_days: Number of days to analyze

        Returns:
            Trend analysis with direction, strength, and forecast
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=period_days)

        # Get daily data
        result = await self.db.execute(
            select(
                func.date(GBMLogisticsData.operation_date).label('date'),
                func.count(GBMLogisticsData.id).label('operations'),
                func.sum(GBMLogisticsData.net_weight_kg).label('total_weight'),
                func.avg(GBMLogisticsData.loading_time_minutes).label('avg_loading_time')
            ).where(
                and_(
                    GBMLogisticsData.site_id == site_id,
                    GBMLogisticsData.operation_date >= start_date,
                    GBMLogisticsData.operation_date <= end_date
                )
            ).group_by(
                func.date(GBMLogisticsData.operation_date)
            ).order_by(
                func.date(GBMLogisticsData.operation_date)
            )
        )

        daily_data = []
        for row in result.all():
            daily_data.append({
                "date": row.date.isoformat() if row.date else None,
                "value": self._get_metric_value(row, metric)
            })

        if len(daily_data) < 7:
            return {
                "status": "insufficient_data",
                "message": "Need at least 7 days of data for trend analysis"
            }

        # Convert to pandas for analysis
        df = pd.DataFrame(daily_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        # Calculate trend
        trend_result = self._calculate_trend(df['value'].values)

        # Calculate moving averages
        df['ma_7'] = df['value'].rolling(window=7).mean()
        df['ma_30'] = df['value'].rolling(window=30).mean() if len(df) >= 30 else None

        return {
            "status": "success",
            "metric": metric,
            "period_days": period_days,
            "trend": {
                "direction": trend_result["direction"],
                "strength": trend_result["strength"],
                "slope": trend_result["slope"],
                "r_squared": trend_result["r_squared"]
            },
            "statistics": {
                "mean": float(df['value'].mean()),
                "median": float(df['value'].median()),
                "std": float(df['value'].std()),
                "min": float(df['value'].min()),
                "max": float(df['value'].max()),
                "current": float(df['value'].iloc[-1]) if len(df) > 0 else 0
            },
            "daily_data": daily_data,
            "moving_averages": {
                "ma_7": df['ma_7'].dropna().tolist(),
                "ma_30": df['ma_30'].dropna().tolist() if df['ma_30'] is not None else None
            },
            "forecast": self._simple_forecast(df['value'].values, days=7)
        }

    # ==================== PERIOD COMPARISON ====================

    async def compare_periods(
        self,
        site_id: int,
        period1_start: date,
        period1_end: date,
        period2_start: date,
        period2_end: date
    ) -> Dict[str, Any]:
        """
        Compare two arbitrary time periods.

        Args:
            site_id: Site ID
            period1_start/end: First period dates
            period2_start/end: Second period dates

        Returns:
            Comparative analysis between periods
        """
        # Get data for period 1
        period1_data = await self._get_period_metrics(site_id, period1_start, period1_end)

        # Get data for period 2
        period2_data = await self._get_period_metrics(site_id, period2_start, period2_end)

        # Calculate comparisons
        comparison = {
            "operations": {
                "period1": period1_data["operations"],
                "period2": period2_data["operations"],
                "change": period2_data["operations"] - period1_data["operations"],
                "change_percent": self._calculate_change_percent(
                    period2_data["operations"],
                    period1_data["operations"]
                )
            },
            "tonnage": {
                "period1": period1_data["tonnage"],
                "period2": period2_data["tonnage"],
                "change": period2_data["tonnage"] - period1_data["tonnage"],
                "change_percent": self._calculate_change_percent(
                    period2_data["tonnage"],
                    period1_data["tonnage"]
                )
            },
            "avg_loading_time": {
                "period1": period1_data["avg_loading_time"],
                "period2": period2_data["avg_loading_time"],
                "change": period2_data["avg_loading_time"] - period1_data["avg_loading_time"],
                "change_percent": self._calculate_change_percent(
                    period2_data["avg_loading_time"],
                    period1_data["avg_loading_time"]
                )
            },
            "revenue": {
                "period1": period1_data["revenue"],
                "period2": period2_data["revenue"],
                "change": period2_data["revenue"] - period1_data["revenue"],
                "change_percent": self._calculate_change_percent(
                    period2_data["revenue"],
                    period1_data["revenue"]
                )
            }
        }

        return {
            "status": "success",
            "period1": {
                "start": period1_start.isoformat(),
                "end": period1_end.isoformat(),
                "days": (period1_end - period1_start).days + 1
            },
            "period2": {
                "start": period2_start.isoformat(),
                "end": period2_end.isoformat(),
                "days": (period2_end - period2_start).days + 1
            },
            "comparison": comparison,
            "winner": self._determine_winner(comparison)
        }

    # ==================== SEASONAL ANALYSIS ====================

    async def get_seasonal_analysis(
        self,
        site_id: int,
        years: int = 2
    ) -> Dict[str, Any]:
        """
        Analyze seasonal patterns in operational data.

        Args:
            site_id: Site ID
            years: Number of years to analyze

        Returns:
            Seasonal patterns by month
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - relativedelta(years=years)

        result = await self.db.execute(
            select(
                extract('month', GBMLogisticsData.operation_date).label('month'),
                extract('year', GBMLogisticsData.operation_date).label('year'),
                func.count(GBMLogisticsData.id).label('operations'),
                func.sum(GBMLogisticsData.net_weight_kg).label('total_weight')
            ).where(
                and_(
                    GBMLogisticsData.site_id == site_id,
                    GBMLogisticsData.operation_date >= start_date,
                    GBMLogisticsData.operation_date <= end_date
                )
            ).group_by(
                extract('month', GBMLogisticsData.operation_date),
                extract('year', GBMLogisticsData.operation_date)
            ).order_by(
                extract('year', GBMLogisticsData.operation_date),
                extract('month', GBMLogisticsData.operation_date)
            )
        )

        # Group by month across years
        monthly_patterns = {}
        for row in result.all():
            month = int(row.month)
            if month not in monthly_patterns:
                monthly_patterns[month] = {
                    "month": month,
                    "month_name": datetime(2000, month, 1).strftime("%B"),
                    "data_points": [],
                    "operations": [],
                    "tonnage": []
                }

            monthly_patterns[month]["operations"].append(int(row.operations) if row.operations else 0)
            monthly_patterns[month]["tonnage"].append(float(row.total_weight / 1000) if row.total_weight else 0)

        # Calculate averages and patterns
        seasonal_data = []
        for month in sorted(monthly_patterns.keys()):
            pattern = monthly_patterns[month]
            seasonal_data.append({
                "month": pattern["month"],
                "month_name": pattern["month_name"],
                "avg_operations": np.mean(pattern["operations"]) if pattern["operations"] else 0,
                "avg_tonnage": np.mean(pattern["tonnage"]) if pattern["tonnage"] else 0,
                "std_operations": np.std(pattern["operations"]) if len(pattern["operations"]) > 1 else 0,
                "std_tonnage": np.std(pattern["tonnage"]) if len(pattern["tonnage"]) > 1 else 0,
                "data_points": len(pattern["operations"])
            })

        return {
            "status": "success",
            "period_years": years,
            "seasonal_patterns": seasonal_data,
            "peak_month": max(seasonal_data, key=lambda x: x["avg_tonnage"]) if seasonal_data else None,
            "low_month": min(seasonal_data, key=lambda x: x["avg_tonnage"]) if seasonal_data else None
        }

    # ==================== HELPER METHODS ====================

    async def _get_period_metrics(
        self,
        site_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, float]:
        """Get aggregated metrics for a period."""
        result = await self.db.execute(
            select(
                func.count(GBMLogisticsData.id).label('operations'),
                func.sum(GBMLogisticsData.net_weight_kg).label('total_weight'),
                func.avg(GBMLogisticsData.loading_time_minutes).label('avg_loading_time'),
                func.sum(GBMLogisticsData.total_value).label('total_revenue')
            ).where(
                and_(
                    GBMLogisticsData.site_id == site_id,
                    GBMLogisticsData.operation_date >= start_date,
                    GBMLogisticsData.operation_date <= end_date
                )
            )
        )

        row = result.first()
        return {
            "operations": int(row.operations) if row and row.operations else 0,
            "tonnage": float(row.total_weight / 1000) if row and row.total_weight else 0,
            "avg_loading_time": float(row.avg_loading_time) if row and row.avg_loading_time else 0,
            "revenue": float(row.total_revenue) if row and row.total_revenue else 0
        }

    def _calculate_change_percent(self, current: float, previous: float) -> float:
        """Calculate percentage change."""
        if previous == 0 or previous is None or current is None:
            return 0.0
        return round(((current - previous) / previous) * 100, 2)

    def _get_metric_value(self, row: Any, metric: str) -> float:
        """Extract metric value from row."""
        if metric == "tonnage":
            return float(row.total_weight / 1000) if row.total_weight else 0
        elif metric == "operations":
            return float(row.operations) if row.operations else 0
        elif metric == "loading_time":
            return float(row.avg_loading_time) if row.avg_loading_time else 0
        return 0.0

    def _calculate_trend(self, values: np.ndarray) -> Dict[str, Any]:
        """Calculate trend direction and strength using linear regression."""
        if len(values) < 2:
            return {"direction": "flat", "strength": 0, "slope": 0, "r_squared": 0}

        x = np.arange(len(values))
        y = values

        # Remove NaN values
        mask = ~np.isnan(y)
        x = x[mask]
        y = y[mask]

        if len(x) < 2:
            return {"direction": "flat", "strength": 0, "slope": 0, "r_squared": 0}

        # Linear regression
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]

        # Calculate R²
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Determine direction and strength
        if abs(slope) < 0.01:
            direction = "flat"
        elif slope > 0:
            direction = "up"
        else:
            direction = "down"

        strength = min(abs(r_squared * 100), 100)

        return {
            "direction": direction,
            "strength": round(strength, 2),
            "slope": round(slope, 4),
            "r_squared": round(r_squared, 4)
        }

    def _simple_forecast(self, values: np.ndarray, days: int = 7) -> List[float]:
        """Simple forecast using linear trend."""
        if len(values) < 7:
            return []

        x = np.arange(len(values))
        y = values

        # Remove NaN
        mask = ~np.isnan(y)
        x = x[mask]
        y = y[mask]

        if len(x) < 2:
            return []

        coeffs = np.polyfit(x, y, 1)

        # Forecast next days
        forecast_x = np.arange(len(values), len(values) + days)
        forecast_y = np.polyval(coeffs, forecast_x)

        return [max(0, float(val)) for val in forecast_y]

    def _calculate_summary_stats(self, monthly_data: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics from monthly data."""
        if not monthly_data:
            return {}

        operations = [m["operations"] for m in monthly_data]
        tonnage = [m["total_tonnage"] for m in monthly_data]
        revenue = [m["total_revenue"] for m in monthly_data]

        return {
            "avg_monthly_operations": round(np.mean(operations), 2) if operations else 0,
            "avg_monthly_tonnage": round(np.mean(tonnage), 2) if tonnage else 0,
            "avg_monthly_revenue": round(np.mean(revenue), 2) if revenue else 0,
            "total_operations": sum(operations),
            "total_tonnage": round(sum(tonnage), 2),
            "total_revenue": round(sum(revenue), 2),
            "best_month": max(monthly_data, key=lambda x: x["total_tonnage"]) if monthly_data else None,
            "worst_month": min(monthly_data, key=lambda x: x["total_tonnage"]) if monthly_data else None
        }

    def _determine_winner(self, comparison: Dict) -> str:
        """Determine which period performed better."""
        score = 0

        # More operations is better
        if comparison["operations"]["change"] > 0:
            score += 1

        # More tonnage is better
        if comparison["tonnage"]["change"] > 0:
            score += 1

        # Less loading time is better
        if comparison["avg_loading_time"]["change"] < 0:
            score += 1

        # More revenue is better
        if comparison["revenue"]["change"] > 0:
            score += 1

        if score > 2:
            return "period2"
        elif score < 2:
            return "period1"
        else:
            return "tie"
