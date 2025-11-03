"""
GBM Logistics Insights Service

Generate actionable insights from imported GBM Logística data:
- Performance analysis
- Bottleneck identification
- Cost optimization opportunities
- Predictive trends
- Quality monitoring

NOTE: Uses InfluxDB for fast KPI aggregations, PostgreSQL for detailed analysis
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
import pandas as pd
import numpy as np

from app.models.external_data import GBMLogisticsData
from app.models.operational_data import DailyOperations
from app.services.influxdb import influxdb_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class GBMInsightsService:
    """
    Service for generating insights from GBM operational data.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== PERFORMANCE ANALYTICS ====================

    async def get_operational_overview(
        self,
        site_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Get comprehensive operational overview from GBM data.

        Returns KPIs, trends, and insights.
        Uses InfluxDB for fast KPI aggregations, PostgreSQL for detailed analysis.
        """
        # Fast KPI query from InfluxDB (10-100x faster than PostgreSQL)
        influx_metrics = influxdb_service.query_aggregated_metrics(
            site_id=site_id,
            start_date=start_date,
            end_date=end_date
        )

        if influx_metrics["operations"] == 0:
            return {
                "status": "no_data",
                "message": "No GBM data found for the period"
            }

        # Calculate fast KPIs from InfluxDB
        kpis = {
            "total_operations": influx_metrics["operations"],
            "total_tonnage": influx_metrics["tonnage"],
            "avg_tonnage_per_operation": influx_metrics["tonnage"] / influx_metrics["operations"] if influx_metrics["operations"] > 0 else 0,
            "avg_loading_time_minutes": influx_metrics["avg_loading_time"],
            "avg_waiting_time_minutes": influx_metrics["avg_waiting_time"],
            "avg_total_time_minutes": influx_metrics["avg_loading_time"] + influx_metrics["avg_waiting_time"] if influx_metrics["avg_loading_time"] and influx_metrics["avg_waiting_time"] else None,
        }

        # Query PostgreSQL only for detailed analysis (needs complex filtering and joins)
        result = await self.db.execute(
            select(GBMLogisticsData).where(
                and_(
                    GBMLogisticsData.site_id == site_id,
                    GBMLogisticsData.operation_date >= start_date,
                    GBMLogisticsData.operation_date <= end_date,
                    GBMLogisticsData.validated == True
                )
            )
        )
        records = result.scalars().all()
        df = pd.DataFrame([r.to_dict() for r in records]) if records else pd.DataFrame()

        # Add status and quality metrics to KPIs from PostgreSQL (these need detailed records)
        if not df.empty:
            kpis["operations_completed"] = len(df[df["status"] == "completed"])
            kpis["operations_pending"] = len(df[df["status"] == "pending"])
            kpis["quality_approved_rate"] = float((df["quality_approved"] == True).sum() / len(df) * 100) if "quality_approved" in df.columns else None

        # Performance by operation type
        performance_by_type = self._analyze_by_operation_type(df) if not df.empty else []

        # Product analysis
        product_analysis = self._analyze_by_product(df) if not df.empty else []

        # Time-based trends from InfluxDB (FAST!)
        daily_trends = self._get_daily_trends_from_influx(site_id, start_date, end_date)

        # Quality metrics
        quality_metrics = self._analyze_quality_metrics(df) if not df.empty else {"status": "no_quality_data"}

        # Financial summary
        financial_summary = self._analyze_financial_metrics(df) if not df.empty else {"status": "no_financial_data"}

        # Identify insights (needs full records for complex analysis)
        insights = await self._generate_insights(df, site_id) if not df.empty else []

        return {
            "status": "success",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days + 1
            },
            "kpis": kpis,
            "performance_by_type": performance_by_type,
            "product_analysis": product_analysis,
            "daily_trends": daily_trends,
            "quality_metrics": quality_metrics,
            "financial_summary": financial_summary,
            "insights": insights,
            "records_analyzed": len(records) if records else 0
        }

    def _calculate_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate key performance indicators."""
        return {
            "total_operations": len(df),
            "total_tonnage": float(df["net_weight_kg"].sum() / 1000),  # Convert to tons
            "avg_tonnage_per_operation": float(df["net_weight_kg"].mean() / 1000),
            "avg_loading_time_minutes": float(df["loading_time_minutes"].mean()) if "loading_time_minutes" in df.columns else None,
            "avg_waiting_time_minutes": float(df["waiting_time_minutes"].mean()) if "waiting_time_minutes" in df.columns else None,
            "avg_total_time_minutes": float(df["total_time_minutes"].mean()) if "total_time_minutes" in df.columns else None,
            "operations_completed": len(df[df["status"] == "completed"]),
            "operations_pending": len(df[df["status"] == "pending"]),
            "quality_approved_rate": float((df["quality_approved"] == True).sum() / len(df) * 100) if "quality_approved" in df.columns else None
        }

    def _analyze_by_operation_type(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze performance by operation type."""
        analysis = []

        for op_type in df["operation_type"].unique():
            type_df = df[df["operation_type"] == op_type]

            analysis.append({
                "operation_type": op_type,
                "count": len(type_df),
                "total_tonnage": float(type_df["net_weight_kg"].sum() / 1000),
                "avg_tonnage": float(type_df["net_weight_kg"].mean() / 1000),
                "avg_loading_time": float(type_df["loading_time_minutes"].mean()) if "loading_time_minutes" in type_df.columns and type_df["loading_time_minutes"].notna().any() else None,
                "avg_waiting_time": float(type_df["waiting_time_minutes"].mean()) if "waiting_time_minutes" in type_df.columns and type_df["waiting_time_minutes"].notna().any() else None,
                "completion_rate": float(len(type_df[type_df["status"] == "completed"]) / len(type_df) * 100)
            })

        return analysis

    def _analyze_by_product(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze performance by product type."""
        analysis = []

        for product in df["product_type"].unique():
            if pd.isna(product) or product == "":
                continue

            product_df = df[df["product_type"] == product]

            analysis.append({
                "product_type": product,
                "count": len(product_df),
                "total_tonnage": float(product_df["net_weight_kg"].sum() / 1000),
                "avg_quality_moisture": float(product_df["moisture_percent"].mean()) if "moisture_percent" in product_df.columns and product_df["moisture_percent"].notna().any() else None,
                "avg_quality_impurity": float(product_df["impurity_percent"].mean()) if "impurity_percent" in product_df.columns and product_df["impurity_percent"].notna().any() else None,
                "quality_approved_rate": float((product_df["quality_approved"] == True).sum() / len(product_df) * 100) if "quality_approved" in product_df.columns else None,
                "avg_value_per_ton": float(product_df["total_value"].sum() / (product_df["net_weight_kg"].sum() / 1000)) if "total_value" in product_df.columns and product_df["total_value"].notna().any() else None
            })

        return sorted(analysis, key=lambda x: x["total_tonnage"], reverse=True)

    def _analyze_daily_trends(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze daily operational trends (DEPRECATED - use _get_daily_trends_from_influx for performance)."""
        df["operation_date"] = pd.to_datetime(df["operation_date"])
        df["date"] = df["operation_date"].dt.date

        daily = df.groupby("date").agg({
            "net_weight_kg": ["count", "sum", "mean"],
            "loading_time_minutes": "mean",
            "waiting_time_minutes": "mean",
            "total_value": "sum"
        }).reset_index()

        trends = []
        for _, row in daily.iterrows():
            trends.append({
                "date": str(row["date"]),
                "operations": int(row[("net_weight_kg", "count")]),
                "total_tonnage": float(row[("net_weight_kg", "sum")] / 1000),
                "avg_tonnage": float(row[("net_weight_kg", "mean")] / 1000),
                "avg_loading_time": float(row[("loading_time_minutes", "mean")]) if pd.notna(row[("loading_time_minutes", "mean")]) else None,
                "avg_waiting_time": float(row[("waiting_time_minutes", "mean")]) if pd.notna(row[("waiting_time_minutes", "mean")]) else None,
                "total_value": float(row[("total_value", "sum")]) if pd.notna(row[("total_value", "sum")]) else None
            })

        return trends

    def _get_daily_trends_from_influx(
        self,
        site_id: int,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Get daily trends from InfluxDB (FAST!)."""
        # Query daily data for tonnage
        tonnage_data = influxdb_service.query_daily_stats(
            site_id=site_id,
            start_date=start_date,
            end_date=end_date,
            metric="net_weight_kg"
        )

        # Query daily data for loading times
        loading_time_data = influxdb_service.query_daily_stats(
            site_id=site_id,
            start_date=start_date,
            end_date=end_date,
            metric="loading_time_minutes"
        )

        # Query daily data for waiting times
        waiting_time_data = influxdb_service.query_daily_stats(
            site_id=site_id,
            start_date=start_date,
            end_date=end_date,
            metric="waiting_time_minutes"
        )

        # Merge data by date
        trends_dict = {}

        # Add tonnage data
        for row in tonnage_data:
            date_key = row["date"]
            trends_dict[date_key] = {
                "date": date_key,
                "operations": row["operations"],
                "total_tonnage": float(row["value"] / 1000),  # Convert kg to tons
                "avg_tonnage": float(row["value"] / 1000 / row["operations"]) if row["operations"] > 0 else 0,
                "avg_loading_time": None,
                "avg_waiting_time": None,
                "total_value": None
            }

        # Add loading time data
        for row in loading_time_data:
            date_key = row["date"]
            if date_key in trends_dict:
                trends_dict[date_key]["avg_loading_time"] = float(row["value"])

        # Add waiting time data
        for row in waiting_time_data:
            date_key = row["date"]
            if date_key in trends_dict:
                trends_dict[date_key]["avg_waiting_time"] = float(row["value"])

        # Convert to sorted list
        return sorted(trends_dict.values(), key=lambda x: x["date"])

    def _analyze_quality_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze quality metrics."""
        if "quality_approved" not in df.columns:
            return {"status": "no_quality_data"}

        quality_df = df[df["quality_approved"].notna()]

        return {
            "total_inspections": len(quality_df),
            "approved": int((quality_df["quality_approved"] == True).sum()),
            "rejected": int((quality_df["quality_approved"] == False).sum()),
            "approval_rate": float((quality_df["quality_approved"] == True).sum() / len(quality_df) * 100),
            "avg_moisture": float(df["moisture_percent"].mean()) if "moisture_percent" in df.columns and df["moisture_percent"].notna().any() else None,
            "avg_impurity": float(df["impurity_percent"].mean()) if "impurity_percent" in df.columns and df["impurity_percent"].notna().any() else None,
            "avg_protein": float(df["protein_percent"].mean()) if "protein_percent" in df.columns and df["protein_percent"].notna().any() else None
        }

    def _analyze_financial_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze financial metrics."""
        if "total_value" not in df.columns or df["total_value"].notna().sum() == 0:
            return {"status": "no_financial_data"}

        financial_df = df[df["total_value"].notna()]

        return {
            "total_revenue": float(financial_df["total_value"].sum()),
            "avg_revenue_per_operation": float(financial_df["total_value"].mean()),
            "total_freight": float(financial_df["freight_value"].sum()) if "freight_value" in financial_df.columns and financial_df["freight_value"].notna().any() else None,
            "total_storage": float(financial_df["storage_value"].sum()) if "storage_value" in financial_df.columns and financial_df["storage_value"].notna().any() else None,
            "revenue_per_ton": float(financial_df["total_value"].sum() / (financial_df["net_weight_kg"].sum() / 1000))
        }

    async def _generate_insights(
        self,
        df: pd.DataFrame,
        site_id: int
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable insights from data analysis.

        Returns list of insights with priority and recommendations.
        """
        insights = []

        # 1. Waiting time insights
        if "waiting_time_minutes" in df.columns and df["waiting_time_minutes"].notna().any():
            avg_waiting = df["waiting_time_minutes"].mean()
            if avg_waiting > 60:  # More than 1 hour average
                insights.append({
                    "type": "bottleneck",
                    "priority": "high",
                    "title": "High Average Waiting Time Detected",
                    "description": f"Average waiting time is {avg_waiting:.1f} minutes, indicating potential bottlenecks",
                    "impact": "Operations efficiency reduced by excessive waiting",
                    "recommendation": "Review queuing process, consider adding more loading bays or optimizing scheduling",
                    "potential_savings": self._calculate_waiting_time_cost(df, avg_waiting)
                })

        # 2. Loading efficiency insights
        if "loading_time_minutes" in df.columns and df["loading_time_minutes"].notna().any():
            df["loading_rate_tons_per_hour"] = (df["net_weight_kg"] / 1000) / (df["loading_time_minutes"] / 60)
            avg_rate = df["loading_rate_tons_per_hour"].mean()
            benchmark_rate = 1200  # tons/hour (industry benchmark)

            if avg_rate < benchmark_rate * 0.8:
                insights.append({
                    "type": "performance",
                    "priority": "medium",
                    "title": "Loading Rate Below Industry Benchmark",
                    "description": f"Current average loading rate is {avg_rate:.0f} t/h vs benchmark {benchmark_rate} t/h",
                    "impact": f"Operating at {(avg_rate/benchmark_rate*100):.1f}% of benchmark capacity",
                    "recommendation": "Investigate equipment performance, operator training, or maintenance issues",
                    "potential_improvement": f"Could increase throughput by {((benchmark_rate/avg_rate - 1)*100):.1f}%"
                })

        # 3. Quality issues insights
        if "quality_approved" in df.columns:
            rejection_rate = (df["quality_approved"] == False).sum() / len(df) * 100
            if rejection_rate > 5:  # More than 5% rejection
                insights.append({
                    "type": "quality",
                    "priority": "high",
                    "title": "High Quality Rejection Rate",
                    "description": f"Quality rejection rate is {rejection_rate:.1f}%, above acceptable threshold",
                    "impact": "Increased costs from rejections, delays, and reputation risk",
                    "recommendation": "Implement pre-arrival quality checks with suppliers, improve receiving inspection processes",
                    "affected_operations": int((df["quality_approved"] == False).sum())
                })

        # 4. Product concentration insights
        if "product_type" in df.columns:
            product_concentration = df.groupby("product_type")["net_weight_kg"].sum()
            top_product_pct = (product_concentration.max() / product_concentration.sum()) * 100

            if top_product_pct > 80:
                insights.append({
                    "type": "risk",
                    "priority": "low",
                    "title": "High Product Concentration Risk",
                    "description": f"Single product accounts for {top_product_pct:.1f}% of operations",
                    "impact": "High dependency on single product creates market risk",
                    "recommendation": "Consider diversifying product portfolio to reduce market exposure"
                })

        # 5. Time utilization insights
        if "total_time_minutes" in df.columns and "loading_time_minutes" in df.columns:
            productive_time_pct = (df["loading_time_minutes"].sum() / df["total_time_minutes"].sum()) * 100

            if productive_time_pct < 60:
                insights.append({
                    "type": "efficiency",
                    "priority": "high",
                    "title": "Low Productive Time Utilization",
                    "description": f"Only {productive_time_pct:.1f}% of total operation time is productive loading",
                    "impact": "Significant time waste in non-productive activities",
                    "recommendation": "Streamline documentation, pre-positioning, and coordination processes",
                    "potential_time_savings": f"{(100 - productive_time_pct):.1f}% of operational time"
                })

        # 6. Financial optimization insights
        if "total_value" in df.columns and df["total_value"].notna().any():
            revenue_per_ton = df["total_value"].sum() / (df["net_weight_kg"].sum() / 1000)
            # Group by product and find variance
            product_revenue = df.groupby("product_type").apply(
                lambda x: x["total_value"].sum() / (x["net_weight_kg"].sum() / 1000)
            )
            if len(product_revenue) > 1:
                best_margin_product = product_revenue.idxmax()
                best_margin_value = product_revenue.max()

                insights.append({
                    "type": "opportunity",
                    "priority": "medium",
                    "title": "Product Mix Optimization Opportunity",
                    "description": f"{best_margin_product} generates highest revenue per ton (R$ {best_margin_value:.2f}/t)",
                    "impact": "Product mix optimization could increase revenue",
                    "recommendation": f"Consider increasing volume of {best_margin_product} to maximize revenue"
                })

        # 7. Seasonal/trend insights
        if len(df) > 7:
            df_sorted = df.sort_values("operation_date")
            recent_ops = df_sorted.tail(7)["net_weight_kg"].sum()
            previous_ops = df_sorted.iloc[-14:-7]["net_weight_kg"].sum() if len(df) >= 14 else recent_ops

            if recent_ops < previous_ops * 0.8:
                insights.append({
                    "type": "alert",
                    "priority": "high",
                    "title": "Significant Volume Decrease Detected",
                    "description": f"Last 7 days volume is {((recent_ops/previous_ops - 1)*100):.1f}% lower than previous period",
                    "impact": "Declining operational volume affecting revenue",
                    "recommendation": "Investigate market conditions, customer relationships, or operational issues"
                })
            elif recent_ops > previous_ops * 1.2:
                insights.append({
                    "type": "opportunity",
                    "priority": "medium",
                    "title": "Volume Growth Opportunity",
                    "description": f"Last 7 days volume is {((recent_ops/previous_ops - 1)*100):.1f}% higher than previous period",
                    "impact": "Growing demand may require capacity expansion",
                    "recommendation": "Assess capacity constraints and consider scaling operations to capture growth"
                })

        return sorted(insights, key=lambda x: {"high": 3, "medium": 2, "low": 1}.get(x["priority"], 0), reverse=True)

    def _calculate_waiting_time_cost(self, df: pd.DataFrame, avg_waiting: float) -> str:
        """Calculate estimated cost of excessive waiting time."""
        # Assumptions:
        # - Hourly cost per operation: R$ 500
        # - Acceptable waiting time: 30 minutes
        # - Cost = (actual - acceptable) * hourly_rate

        if avg_waiting <= 30:
            return "No excess cost"

        excess_minutes = avg_waiting - 30
        hourly_rate = 500
        operations_count = len(df)

        cost_per_operation = (excess_minutes / 60) * hourly_rate
        total_cost = cost_per_operation * operations_count

        return f"Estimated R$ {total_cost:,.2f} in excess waiting costs"

    # ==================== BENCHMARKING ====================

    async def get_benchmarks(
        self,
        site_id: int,
        operation_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get performance benchmarks.

        Compares site performance against historical averages and industry standards.
        """
        # Get last 30 days of data
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)

        result = await self.db.execute(
            select(GBMLogisticsData).where(
                and_(
                    GBMLogisticsData.site_id == site_id,
                    GBMLogisticsData.operation_date >= start_date,
                    GBMLogisticsData.operation_date <= end_date,
                    GBMLogisticsData.validated == True
                )
            )
        )
        records = result.scalars().all()

        if not records:
            return {"status": "no_data"}

        df = pd.DataFrame([r.to_dict() for r in records])

        # Calculate current performance
        current_performance = {
            "avg_loading_time": float(df["loading_time_minutes"].mean()) if "loading_time_minutes" in df.columns and df["loading_time_minutes"].notna().any() else None,
            "avg_waiting_time": float(df["waiting_time_minutes"].mean()) if "waiting_time_minutes" in df.columns and df["waiting_time_minutes"].notna().any() else None,
            "avg_throughput": float((df["net_weight_kg"] / 1000).sum() / len(df)) if len(df) > 0 else None,
            "quality_approval_rate": float((df["quality_approved"] == True).sum() / len(df) * 100) if "quality_approved" in df.columns else None
        }

        # Industry benchmarks (these would normally come from a database or external source)
        industry_benchmarks = {
            "avg_loading_time": 120,  # minutes
            "avg_waiting_time": 30,   # minutes
            "avg_throughput": 35,     # tons per operation
            "quality_approval_rate": 95  # percentage
        }

        # Calculate performance score
        scores = {}
        for metric, current_value in current_performance.items():
            if current_value is not None and metric in industry_benchmarks:
                benchmark_value = industry_benchmarks[metric]

                if metric in ["avg_loading_time", "avg_waiting_time"]:
                    # Lower is better
                    score = (benchmark_value / current_value * 100) if current_value > 0 else 100
                else:
                    # Higher is better
                    score = (current_value / benchmark_value * 100) if benchmark_value > 0 else 100

                scores[metric] = min(score, 100)  # Cap at 100

        overall_score = sum(scores.values()) / len(scores) if scores else 0

        return {
            "status": "success",
            "period_days": 30,
            "current_performance": current_performance,
            "industry_benchmarks": industry_benchmarks,
            "performance_scores": scores,
            "overall_score": round(overall_score, 1),
            "rating": self._get_performance_rating(overall_score)
        }

    def _get_performance_rating(self, score: float) -> str:
        """Convert score to rating."""
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Average"
        elif score >= 40:
            return "Below Average"
        else:
            return "Poor"

    # ==================== PREDICTIONS ====================

    async def predict_volume(
        self,
        site_id: int,
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Predict operational volume for upcoming days.

        Simple time-series prediction based on historical trends.
        """
        # Get last 90 days of data
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=90)

        result = await self.db.execute(
            select(GBMLogisticsData).where(
                and_(
                    GBMLogisticsData.site_id == site_id,
                    GBMLogisticsData.operation_date >= start_date,
                    GBMLogisticsData.operation_date <= end_date
                )
            )
        )
        records = result.scalars().all()

        if len(records) < 14:
            return {"status": "insufficient_data", "message": "Need at least 14 days of data for prediction"}

        df = pd.DataFrame([r.to_dict() for r in records])
        df["operation_date"] = pd.to_datetime(df["operation_date"])
        df["date"] = df["operation_date"].dt.date

        # Aggregate by day
        daily = df.groupby("date").agg({
            "net_weight_kg": "sum"
        }).reset_index()
        daily["tonnage"] = daily["net_weight_kg"] / 1000

        # Simple moving average prediction
        window = 7
        daily["ma"] = daily["tonnage"].rolling(window=window).mean()

        # Predict next days
        last_ma = daily["ma"].iloc[-1]
        predictions = []

        for i in range(1, days_ahead + 1):
            pred_date = end_date + timedelta(days=i)
            predictions.append({
                "date": pred_date.isoformat(),
                "predicted_tonnage": round(float(last_ma), 2),
                "confidence": "medium"
            })

        return {
            "status": "success",
            "prediction_method": "moving_average",
            "days_ahead": days_ahead,
            "predictions": predictions,
            "historical_avg": round(float(daily["tonnage"].mean()), 2)
        }
