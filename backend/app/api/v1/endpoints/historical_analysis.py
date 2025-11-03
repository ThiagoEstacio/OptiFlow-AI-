"""
Historical Analysis API Endpoints

Endpoints for historical trend analysis and comparisons:
- Monthly comparisons
- Trend analysis
- Period comparisons
- Seasonal patterns
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.historical_analysis_service import HistoricalAnalysisService

router = APIRouter()


@router.get("/monthly-comparison/{site_id}")
async def get_monthly_comparison(
    site_id: int,
    months: int = Query(12, ge=1, le=36, description="Number of months to compare"),
    metric: str = Query("all", description="Specific metric or 'all'"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get month-over-month comparison.

    Returns monthly data with MoM and YoY comparisons for the last N months.
    """
    service = HistoricalAnalysisService(db)
    return await service.get_monthly_comparison(site_id, months, metric)


@router.get("/trend-analysis/{site_id}")
async def get_trend_analysis(
    site_id: int,
    metric: str = Query(..., description="Metric to analyze (tonnage, operations, loading_time)"),
    period_days: int = Query(90, ge=7, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze trend for a specific metric.

    Returns trend direction, strength, statistics, and forecast.
    """
    service = HistoricalAnalysisService(db)
    return await service.get_trend_analysis(site_id, metric, period_days)


@router.get("/compare-periods/{site_id}")
async def compare_periods(
    site_id: int,
    period1_start: date = Query(..., description="First period start date"),
    period1_end: date = Query(..., description="First period end date"),
    period2_start: date = Query(..., description="Second period start date"),
    period2_end: date = Query(..., description="Second period end date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compare two arbitrary time periods.

    Returns comparative analysis showing changes between periods.
    """
    service = HistoricalAnalysisService(db)
    return await service.compare_periods(
        site_id,
        period1_start,
        period1_end,
        period2_start,
        period2_end
    )


@router.get("/seasonal-analysis/{site_id}")
async def get_seasonal_analysis(
    site_id: int,
    years: int = Query(2, ge=1, le=5, description="Number of years to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze seasonal patterns.

    Returns average patterns by month across multiple years.
    """
    service = HistoricalAnalysisService(db)
    return await service.get_seasonal_analysis(site_id, years)


@router.get("/quick-stats/{site_id}")
async def get_quick_stats(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get quick historical statistics.

    Returns current month vs last month comparison.
    """
    service = HistoricalAnalysisService(db)

    # Get last 2 months
    data = await service.get_monthly_comparison(site_id, months=2)

    if data["status"] != "success" or len(data["monthly_data"]) < 2:
        return {
            "status": "insufficient_data",
            "message": "Need at least 2 months of data"
        }

    current_month = data["monthly_data"][-1]
    last_month = data["monthly_data"][-2]

    return {
        "status": "success",
        "current_month": current_month,
        "last_month": last_month,
        "comparison": {
            "operations_change": current_month.get("mom_operations", 0),
            "tonnage_change": current_month.get("mom_tonnage", 0),
            "revenue_change": current_month.get("mom_revenue", 0)
        }
    }
