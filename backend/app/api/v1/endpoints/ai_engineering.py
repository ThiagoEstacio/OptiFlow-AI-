"""
AI Engineering Tools API Endpoints

Advanced AI-powered engineering analysis tools:
- Auto-dashboard generation
- Failure analysis with RCA
- Pareto charts and analysis
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.auto_dashboard_generator import AutoDashboardGenerator
from app.services.failure_analyzer import FailureAnalyzer
from app.services.pareto_analyzer import ParetoAnalyzer

router = APIRouter()
logger = logging.getLogger(__name__)


# Auto Dashboard Generation Endpoints


@router.post("/dashboards/generate/{asset_id}", response_model=Dict[str, Any])
async def generate_dashboard(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Automatically generate a dashboard for an asset.

    Creates an intelligent dashboard with appropriate widgets
    based on the asset type.
    """
    try:
        generator = AutoDashboardGenerator(db)
        dashboard = await generator.generate_dashboard(asset_id)

        logger.info(f"Generated dashboard for asset {asset_id}")

        return dashboard

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dashboards/generate/site/{site_id}", response_model=Dict[str, Any])
async def generate_site_dashboards(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate dashboards for all assets in a site.

    Returns a list of generated dashboard configurations.
    """
    try:
        generator = AutoDashboardGenerator(db)
        dashboards = await generator.generate_dashboards_for_site(site_id)

        logger.info(f"Generated {len(dashboards)} dashboards for site {site_id}")

        return {
            "site_id": site_id,
            "dashboard_count": len(dashboards),
            "dashboards": dashboards,
        }

    except Exception as e:
        logger.error(f"Error generating site dashboards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboards/templates", response_model=Dict[str, Any])
async def get_dashboard_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get list of available dashboard templates.

    Returns templates for different asset types.
    """
    try:
        generator = AutoDashboardGenerator(db)
        templates = generator.get_available_templates()

        return {
            "templates": templates,
            "count": len(templates),
        }

    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Failure Analysis Endpoints


@router.post("/failure-analysis/{asset_id}", response_model=Dict[str, Any])
async def analyze_failure(
    asset_id: str,
    failure_time: Optional[datetime] = None,
    failure_description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Perform root cause analysis on an equipment failure.

    Analyzes:
    - Alarms before failure
    - Sensor anomalies
    - Historical patterns
    - Correlated failures

    Returns probable causes and recommendations.
    """
    try:
        analyzer = FailureAnalyzer(db)

        # Use current time if not specified
        if not failure_time:
            failure_time = datetime.utcnow()

        analysis = await analyzer.analyze_failure(
            asset_id=asset_id,
            failure_time=failure_time,
            failure_description=failure_description
        )

        logger.info(f"Completed failure analysis for asset {asset_id}")

        return analysis

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Pareto Analysis Endpoints


@router.get("/pareto/asset/{asset_id}", response_model=Dict[str, Any])
async def get_asset_pareto(
    asset_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    min_occurrences: int = Query(1, ge=1, description="Minimum occurrences to include"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate Pareto chart for an asset's failures.

    Shows failure frequency distribution following the 80/20 rule.
    Identifies the vital few failure types that cause most issues.
    """
    try:
        analyzer = ParetoAnalyzer(db)

        pareto = await analyzer.generate_pareto(
            asset_id=asset_id,
            days=days,
            min_occurrences=min_occurrences
        )

        logger.info(f"Generated Pareto analysis for asset {asset_id}")

        return pareto

    except Exception as e:
        logger.error(f"Error generating Pareto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pareto/site/{site_id}", response_model=Dict[str, Any])
async def get_site_pareto(
    site_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    min_occurrences: int = Query(1, ge=1, description="Minimum occurrences to include"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate Pareto chart for all failures in a site.

    Shows site-wide failure distribution.
    Useful for identifying systemic issues across multiple assets.
    """
    try:
        analyzer = ParetoAnalyzer(db)

        pareto = await analyzer.generate_pareto(
            site_id=site_id,
            days=days,
            min_occurrences=min_occurrences
        )

        logger.info(f"Generated Pareto analysis for site {site_id}")

        return pareto

    except Exception as e:
        logger.error(f"Error generating Pareto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pareto/compare/{asset_id}", response_model=Dict[str, Any])
async def compare_pareto_periods(
    asset_id: str,
    current_days: int = Query(30, ge=1, le=180, description="Days in current period"),
    previous_days: int = Query(30, ge=1, le=180, description="Days in previous period"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Compare Pareto analysis between two time periods.

    Shows if failures are increasing, decreasing, or stable.
    Useful for tracking improvement initiatives.
    """
    try:
        analyzer = ParetoAnalyzer(db)

        comparison = await analyzer.compare_periods(
            current_days=current_days,
            previous_days=previous_days,
            asset_id=asset_id
        )

        logger.info(f"Compared Pareto periods for asset {asset_id}")

        return comparison

    except Exception as e:
        logger.error(f"Error comparing Pareto periods: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Combined Analysis Endpoint


@router.get("/analysis/comprehensive/{asset_id}", response_model=Dict[str, Any])
async def get_comprehensive_analysis(
    asset_id: str,
    days: int = Query(30, ge=1, le=90, description="Analysis period in days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive engineering analysis for an asset.

    Combines:
    - Pareto chart (failure frequency)
    - Historical failure analysis
    - Dashboard recommendations
    - Priority actions

    One-stop analysis for engineering decisions.
    """
    try:
        # Generate Pareto
        pareto_analyzer = ParetoAnalyzer(db)
        pareto = await pareto_analyzer.generate_pareto(
            asset_id=asset_id,
            days=days
        )

        # Get dashboard template
        dashboard_generator = AutoDashboardGenerator(db)
        dashboard = await dashboard_generator.generate_dashboard(asset_id)

        # Combine results
        comprehensive = {
            "asset_id": asset_id,
            "analysis_period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
            "pareto_analysis": {
                "total_failures": pareto.get("total_failures", 0),
                "vital_few": pareto.get("vital_few", []),
                "recommendations": pareto.get("recommendations", []),
            },
            "dashboard": {
                "name": dashboard.get("name"),
                "widgets_count": len(dashboard.get("widgets", [])),
            },
            "priority_actions": pareto.get("recommendations", [])[:3],
            "insights": pareto.get("insights", []),
        }

        logger.info(f"Generated comprehensive analysis for asset {asset_id}")

        return comprehensive

    except Exception as e:
        logger.error(f"Error generating comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
