"""
Executive Dashboard API Endpoints

Provides endpoints for:
- 360° Dashboard with unified maintenance + operations view
- ROI Calculator and financial metrics
- Weekly executive reports
- Cost-benefit analysis
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from datetime import date, datetime
import logging

from app.db.session import get_db
from app.models.user import User
from app.core.deps import get_current_user
from app.services.executive_dashboard import ExecutiveDashboard
from app.services.roi_calculator import ROICalculator
# from app.services.executive_report_generator import ExecutiveReportGenerator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard360/{site_id}", response_model=Dict[str, Any])
async def get_dashboard_360(
    site_id: int,
    period_days: int = Query(7, ge=1, le=90, description="Analysis period in days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive 360° dashboard with maintenance + operations insights.

    Provides unified view of terminal health, correlating maintenance events
    with operational impact, identifying risks and opportunities.

    **Key Features:**
    - Real-time KPIs for maintenance and operations
    - Asset health summary by type and criticality
    - Correlation analysis between maintenance and operations
    - Critical alerts requiring immediate action
    - Risk identification and mitigation recommendations
    - Optimization opportunities

    **Use Cases:**
    - Executive overview of terminal status
    - Daily operations briefing
    - Strategic planning and decision-making
    - Performance monitoring
    """
    try:
        dashboard = ExecutiveDashboard(db)
        result = await dashboard.get_dashboard_360(site_id, period_days)

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))

        logger.info(f"Dashboard 360° accessed for site {site_id} by user {current_user.id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard 360°: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roi/{site_id}", response_model=Dict[str, Any])
async def calculate_roi(
    site_id: int,
    period_days: int = Query(30, ge=7, le=365, description="Analysis period in days"),
    hourly_downtime_cost: Optional[float] = Query(None, description="Custom hourly downtime cost ($)"),
    ship_delay_cost: Optional[float] = Query(None, description="Custom ship delay cost per hour ($)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Calculate Return on Investment for OptiFlow AI.

    **Calculates:**
    - Downtime costs avoided through predictive maintenance
    - Operational efficiency savings from optimization
    - Equipment life extension value
    - Total cost savings and ROI percentage
    - Annual projections

    **Breakdown by Category:**
    - Predictive Maintenance: Failures prevented, emergency costs avoided
    - Optimization: Ship waiting time reduced, loading efficiency improved
    - Efficiency: Truck processing time savings, fuel savings
    - Downtime Avoided: Critical alerts handled, disruptions prevented

    **Use Cases:**
    - Demonstrate business value to stakeholders
    - Justify system investment
    - Track cost savings over time
    - Support budget planning
    """
    try:
        custom_costs = {}
        if hourly_downtime_cost:
            custom_costs["hourly_downtime_cost"] = hourly_downtime_cost
        if ship_delay_cost:
            custom_costs["ship_delay_cost_per_hour"] = ship_delay_cost

        roi_calculator = ROICalculator(db)
        result = await roi_calculator.calculate_roi(
            site_id,
            period_days,
            custom_costs if custom_costs else None
        )

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))

        logger.info(f"ROI calculated for site {site_id} (period: {period_days} days)")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating ROI: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roi/trend/{site_id}", response_model=Dict[str, Any])
async def get_roi_trend(
    site_id: int,
    months: int = Query(6, ge=3, le=12, description="Number of months to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get monthly ROI trend for the last N months.

    Shows historical progression of cost savings and ROI metrics,
    helping identify trends and performance improvements over time.

    **Returns:**
    - Monthly savings data
    - Failures prevented per month
    - Downtime avoided per month
    - 6-month total savings

    **Use Cases:**
    - Track ROI improvement over time
    - Demonstrate consistent value delivery
    - Identify seasonal patterns
    - Support renewal decisions
    """
    try:
        roi_calculator = ROICalculator(db)
        result = await roi_calculator.get_monthly_trend(site_id, months)

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))

        logger.info(f"ROI trend calculated for site {site_id} ({months} months)")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating ROI trend: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost-benefit/{site_id}", response_model=Dict[str, Any])
async def get_cost_benefit_analysis(
    site_id: int,
    system_cost_annual: float = Query(50000, description="Annual system cost ($)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Comprehensive cost-benefit analysis for executive decision-making.

    Compares OptiFlow AI investment against benefits, calculating:
    - Net monthly and annual benefit
    - Benefit-cost ratio
    - Break-even period
    - ROI percentage
    - Benefits by category

    **Includes:**
    - Investment costs (system, implementation, training)
    - Return breakdown (predictive maintenance, optimization, efficiency)
    - Net benefit calculations
    - Executive summary narrative

    **Use Cases:**
    - C-level presentations
    - Budget justification
    - Contract renewals
    - Board meetings
    """
    try:
        roi_calculator = ROICalculator(db)
        result = await roi_calculator.get_cost_benefit_analysis(site_id, system_cost_annual)

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))

        logger.info(f"Cost-benefit analysis for site {site_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating cost-benefit: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weekly-report/data/{site_id}", response_model=Dict[str, Any])
async def get_weekly_summary_data(
    site_id: int,
    week_start: Optional[str] = Query(None, description="Week start date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get weekly executive summary in JSON format.

    Aggregates key metrics and insights for weekly review:
    - Overall terminal health score
    - Financial performance (savings, ROI)
    - Operational KPIs
    - Top risks and opportunities
    - Strategic recommendations

    **Perfect for:**
    - Weekly executive meetings
    - Dashboard displays
    - Web applications
    - Mobile apps
    - API integrations

    **Note:** For PDF report, use `/weekly-report/pdf` endpoint.
    """
    try:
        week_start_date = None
        if week_start:
            week_start_date = datetime.strptime(week_start, "%Y-%m-%d").date()

        report_gen = ExecutiveReportGenerator(db)
        result = await report_gen.get_weekly_summary_data(site_id, week_start_date)

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))

        logger.info(f"Weekly summary data for site {site_id}")
        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting weekly summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weekly-report/pdf/{site_id}")
async def generate_weekly_report_pdf(
    site_id: int,
    week_start: Optional[str] = Query(None, description="Week start date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate comprehensive weekly executive report in PDF format.

    Creates professional multi-page report with:
    - Executive summary with key metrics
    - Financial performance breakdown
    - Operational KPIs and trends
    - Maintenance and asset health status
    - Strategic insights (risks & opportunities)
    - Data-driven recommendations

    **Report Sections:**
    1. **Executive Summary** - Overall health, savings, ROI
    2. **Financial Performance** - Savings by category, projections
    3. **Operational Performance** - Trucks, ships, tonnage, efficiency
    4. **Maintenance & Assets** - Health scores, alarms, trends
    5. **Strategic Insights** - Risks, opportunities
    6. **Recommendations** - Action items for leadership

    **Use Cases:**
    - Weekly leadership meetings
    - Board presentations
    - Investor updates
    - Performance reviews
    - Historical documentation

    **Returns:**
    - `filename`: Path to generated PDF
    - `file_size_bytes`: Size of PDF file
    - `generation_time_ms`: Time taken to generate
    """
    try:
        week_start_date = None
        if week_start:
            week_start_date = datetime.strptime(week_start, "%Y-%m-%d").date()

        report_gen = ExecutiveReportGenerator(db)

        # Generate PDF
        start_time = datetime.utcnow()
        filename = await report_gen.generate_weekly_report_pdf(site_id, week_start_date)
        end_time = datetime.utcnow()

        # Get file size
        import os
        file_size = os.path.getsize(filename)
        generation_time_ms = (end_time - start_time).total_seconds() * 1000

        logger.info(f"Weekly PDF report generated for site {site_id}: {filename}")

        return {
            "status": "success",
            "filename": filename,
            "file_size_bytes": file_size,
            "generation_time_ms": round(generation_time_ms, 1),
            "week_start": week_start_date.isoformat() if week_start_date else None
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating weekly PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/highlights/{site_id}", response_model=Dict[str, Any])
async def get_executive_highlights(
    site_id: int,
    period_days: int = Query(7, ge=1, le=30, description="Period for highlights"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get top executive highlights and key achievements.

    Returns concise, actionable highlights perfect for:
    - Email summaries
    - Slack/Teams notifications
    - Mobile push notifications
    - Dashboard widgets
    - Quick status checks

    **Highlights Include:**
    - Total cost savings this period
    - Failures prevented
    - Downtime avoided
    - Ships optimized
    - Top ROI contributor

    **Format:** Ready-to-display text with emojis and formatting.
    """
    try:
        # Get ROI data
        roi_calculator = ROICalculator(db)
        roi_data = await roi_calculator.calculate_roi(site_id, period_days)

        if roi_data.get("status") == "error":
            raise HTTPException(status_code=500, detail=roi_data.get("error"))

        highlights = roi_data.get("highlights", [])

        # Get dashboard for additional context
        dashboard = ExecutiveDashboard(db)
        dashboard_data = await dashboard.get_dashboard_360(site_id, period_days)

        overall_health = dashboard_data.get("overall_health_score", {})

        return {
            "status": "success",
            "site_id": site_id,
            "period_days": period_days,
            "timestamp": datetime.utcnow().isoformat(),
            "overall_health": {
                "score": overall_health.get("score", 0),
                "status": overall_health.get("status", "unknown"),
                "color": overall_health.get("color", "grey")
            },
            "highlights": highlights,
            "quick_stats": {
                "total_savings": roi_data.get("total_savings", 0),
                "failures_prevented": roi_data.get("predictive_maintenance", {}).get("failures_prevented", 0),
                "critical_alerts": len(dashboard_data.get("critical_alerts", []))
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting highlights: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpi-summary/{site_id}", response_model=Dict[str, Any])
async def get_kpi_summary(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get lightweight KPI summary for dashboards and widgets.

    Returns essential metrics only, optimized for:
    - Real-time dashboards
    - Mobile apps
    - Status displays
    - Quick checks

    **Minimal payload, maximum insight.**

    **Returns:**
    - Overall health score
    - Critical alerts count
    - Assets at risk
    - Weekly savings
    - Efficiency score
    """
    try:
        dashboard = ExecutiveDashboard(db)
        dashboard_data = await dashboard.get_dashboard_360(site_id, period_days=7)

        roi_calculator = ROICalculator(db)
        roi_data = await roi_calculator.calculate_roi(site_id, period_days=7)

        overall_health = dashboard_data.get("overall_health_score", {})
        maintenance = dashboard_data.get("maintenance", {})
        operations = dashboard_data.get("operations", {})

        return {
            "status": "success",
            "site_id": site_id,
            "timestamp": datetime.utcnow().isoformat(),

            # Core metrics
            "overall_health_score": overall_health.get("score", 0),
            "health_status": overall_health.get("status", "unknown"),

            # Maintenance
            "avg_asset_health": maintenance.get("average_health_score", 0),
            "critical_assets": maintenance.get("assets_by_health", {}).get("critical", 0),
            "critical_alerts": maintenance.get("alarms", {}).get("critical", 0),

            # Operations
            "efficiency_score": operations.get("efficiency_score", 0),
            "berth_utilization": operations.get("berth_utilization_percent", 0),

            # Financial
            "weekly_savings": roi_data.get("total_savings", 0),
            "annual_projection": roi_data.get("annual_projection", 0),

            # Counts
            "risks_count": len(dashboard_data.get("risks", [])),
            "opportunities_count": len(dashboard_data.get("opportunities", []))
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting KPI summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
