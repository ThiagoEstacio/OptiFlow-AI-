"""
Quality Management Endpoints

Provides endpoints for quality tools:
- Pareto Analysis
- Statistical Process Control (SPC)
- Root Cause Analysis
- Quality Insights
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import logging

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.pareto_analyzer import ParetoAnalyzer

# === SPRINT 1: Quality Gate (CORR-004) ===
try:
    from app.services.quality_gate import get_quality_gate
    QUALITY_GATE_AVAILABLE = True
except ImportError:
    QUALITY_GATE_AVAILABLE = False

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/pareto")
async def get_pareto_analysis(
    days: int = Query(default=7, ge=1, le=365, description="Number of days to analyze"),
    asset_id: Optional[str] = Query(default=None, description="Specific asset ID"),
    site_id: Optional[int] = Query(default=None, description="Specific site ID"),
    min_occurrences: int = Query(default=1, ge=1, description="Minimum occurrences to include"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate Pareto analysis for failures.

    The Pareto principle (80/20 rule) states that roughly 80% of consequences
    come from 20% of causes. This endpoint identifies the "vital few" failure
    types that cause the most problems.

    Returns:
        - items: List of failure types sorted by frequency
        - vital_few: Items causing ~80% of problems
        - statistics: Summary metrics
    """
    try:
        logger.info(
            f"Generating Pareto analysis: days={days}, asset_id={asset_id}, "
            f"site_id={site_id}, min_occurrences={min_occurrences}"
        )

        analyzer = ParetoAnalyzer(db)
        result = await analyzer.generate_pareto(
            asset_id=asset_id,
            site_id=site_id,
            days=days,
            min_occurrences=min_occurrences
        )

        logger.info(f"Pareto analysis completed: status={result.get('status')}")
        return result

    except Exception as e:
        logger.error(f"Error generating Pareto analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Pareto analysis: {str(e)}"
        )


@router.get("/pareto/summary")
async def get_pareto_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a quick summary of Pareto analysis for dashboard KPIs.

    Returns key metrics without full chart data.
    """
    try:
        analyzer = ParetoAnalyzer(db)
        result = await analyzer.generate_pareto(days=7, min_occurrences=1)

        if result.get("status") == "success":
            return {
                "total_failure_types": len(result.get("items", [])),
                "vital_few_count": result.get("vital_few_count", 0),
                "vital_few_percentage": result.get("vital_few_percentage", 0),
                "total_failures": result.get("total_failures", 0),
                "analysis_period_days": result.get("analysis_period_days", 7),
                "generated_at": result.get("generated_at"),
            }
        else:
            return {
                "total_failure_types": 0,
                "vital_few_count": 0,
                "vital_few_percentage": 0,
                "total_failures": 0,
                "analysis_period_days": 7,
                "message": result.get("message", "No data available"),
            }

    except Exception as e:
        logger.error(f"Error generating Pareto summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Pareto summary: {str(e)}"
        )


@router.get("/insights/quality")
async def get_quality_insights(
    limit: int = Query(default=20, ge=1, le=100),
    severity: Optional[str] = Query(default=None, description="Filter by severity"),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get quality-specific insights from the Autonomous Agent.

    Filters insights that are related to quality tools:
    - Pareto analysis
    - SPC (Statistical Process Control)
    - Pattern analysis
    - Root cause analysis
    """
    try:
        from app.services.autonomous_agent import get_autonomous_agent

        agent = get_autonomous_agent()
        if not agent:
            return {
                "insights": [],
                "total": 0,
                "message": "Autonomous agent not initialized"
            }

        # Get all insights
        all_insights = agent.get_insights(severity=severity, limit=limit * 2)

        # Filter for quality-related insights
        quality_insights = [
            insight for insight in all_insights
            if any(tag in insight.get("tags", []) for tag in ["quality", "pareto", "spc", "pattern"])
            or "Pareto" in insight.get("title", "")
            or "Variabilidade" in insight.get("title", "")
            or "Padrão" in insight.get("title", "")
        ]

        return {
            "insights": quality_insights[:limit],
            "total": len(quality_insights),
            "total_all_insights": len(all_insights),
        }

    except Exception as e:
        logger.error(f"Error getting quality insights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get quality insights: {str(e)}"
        )


@router.get("/spc/tags")
async def get_spc_analysis_for_tags(
    tag_ids: Optional[str] = Query(default=None, description="Comma-separated tag IDs"),
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get Statistical Process Control (SPC) analysis for specific tags.

    Calculates:
    - Coefficient of Variation (CV)
    - Mean, Standard Deviation
    - Process stability indicators
    """
    try:
        from app.services.agent_tools import AgentToolkit
        from app.services.data_service import DataService
        from app.models.tag import Tag
        from sqlalchemy import select

        data_service = DataService(db)
        toolkit = AgentToolkit(data_service)

        # Get tags
        if tag_ids:
            tag_id_list = tag_ids.split(",")
            result = await db.execute(
                select(Tag).where(Tag.id.in_(tag_id_list))
            )
            tags = result.scalars().all()
        else:
            # Get first 5 process tags
            result = await db.execute(
                select(Tag)
                .where(Tag.is_active == True)
                .where(Tag.category.in_(["process", "control"]))
                .limit(5)
            )
            tags = result.scalars().all()

        spc_results = []
        for tag in tags:
            try:
                # Calculate statistics
                result = await toolkit.execute_tool(
                    "calculate_statistics",
                    {
                        "tag_id": str(tag.id),
                        "duration": f"{hours}h"
                    }
                )

                if result.success and result.data:
                    stats = result.data
                    mean = stats.get("mean", 0)
                    stddev = stats.get("stddev", 0)
                    cv = (stddev / mean * 100) if mean != 0 else 0

                    spc_results.append({
                        "tag_id": str(tag.id),
                        "tag_name": tag.name,
                        "mean": mean,
                        "stddev": stddev,
                        "coefficient_of_variation": cv,
                        "is_stable": cv <= 15,
                        "stability_status": "stable" if cv <= 15 else "high_variability" if cv <= 25 else "very_high_variability",
                        "data_points": stats.get("count", 0),
                        "min": stats.get("min"),
                        "max": stats.get("max"),
                    })

            except Exception as e:
                logger.error(f"Error analyzing SPC for tag {tag.id}: {e}")
                continue

        return {
            "spc_analysis": spc_results,
            "total_tags": len(spc_results),
            "analysis_period_hours": hours,
            "stable_count": sum(1 for r in spc_results if r["is_stable"]),
            "unstable_count": sum(1 for r in spc_results if not r["is_stable"]),
        }

    except Exception as e:
        logger.error(f"Error in SPC analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform SPC analysis: {str(e)}"
        )


@router.get("/tools")
async def get_quality_tools_info(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get information about available quality tools and their status.
    """
    return {
        "available_tools": [
            {
                "name": "Pareto Analysis",
                "description": "80/20 rule - Identify vital few causing most problems",
                "status": "active",
                "endpoint": "/api/v1/quality/pareto",
                "integrated_with_agent": True,
            },
            {
                "name": "Statistical Process Control (SPC)",
                "description": "Monitor process variability using Coefficient of Variation",
                "status": "active",
                "endpoint": "/api/v1/quality/spc/tags",
                "integrated_with_agent": True,
            },
            {
                "name": "Pattern Analysis",
                "description": "Detect recurring failures indicating systematic issues",
                "status": "active",
                "endpoint": "Integrated in agent insights",
                "integrated_with_agent": True,
            },
            {
                "name": "Ishikawa Diagram",
                "description": "Fishbone diagram for root cause analysis",
                "status": "development",
                "endpoint": "Coming soon",
                "integrated_with_agent": False,
            },
            {
                "name": "Control Charts",
                "description": "Full SPC with UCL/LCL and Western Electric rules",
                "status": "development",
                "endpoint": "Coming soon",
                "integrated_with_agent": False,
            },
            {
                "name": "Check Sheets",
                "description": "Digital data collection forms for quality tracking",
                "status": "planned",
                "endpoint": "Coming soon",
                "integrated_with_agent": False,
            },
            {
                "name": "Histograms",
                "description": "Distribution analysis and capability studies",
                "status": "planned",
                "endpoint": "Coming soon",
                "integrated_with_agent": False,
            },
        ],
        "agent_integration": {
            "status": "active",
            "monitoring_interval_seconds": 60,
            "quality_insights_enabled": True,
            "tools_integrated": ["pareto", "spc", "pattern_analysis"],
        },
    }


# === SPRINT 1: Quality Gate Endpoints (CORR-004) ===

@router.get("/gate/stats")
async def get_quality_gate_statistics(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get Quality Gate statistics.

    CORR-004: Shows how many data points have been:
    - Passed: Allowed through the quality gate
    - Flagged: Allowed but with quality warnings
    - Blocked: Rejected due to bad quality

    Quality gates ensure data integrity by filtering out invalid data
    before it is stored in the time-series database.
    """
    if not QUALITY_GATE_AVAILABLE:
        return {
            "available": False,
            "message": "Quality gate service not available"
        }

    try:
        quality_gate = get_quality_gate()
        stats = quality_gate.get_statistics()

        return {
            "available": True,
            **stats
        }

    except Exception as e:
        logger.error(f"Error getting quality gate stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get quality gate statistics: {str(e)}"
        )


@router.post("/gate/config")
async def configure_quality_gate(
    strict_mode: Optional[bool] = Query(default=None, description="Enable strict mode (blocks bad quality)"),
    enabled: Optional[bool] = Query(default=None, description="Enable/disable quality gates"),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Configure Quality Gate behavior.

    CORR-004: Allows operators to adjust quality gate behavior:
    - strict_mode: If True, blocks bad quality data; if False, only flags
    - enabled: Enable or disable quality gates entirely
    """
    if not QUALITY_GATE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Quality gate service not available"
        )

    try:
        quality_gate = get_quality_gate()

        if strict_mode is not None:
            quality_gate.set_strict_mode(strict_mode)

        if enabled is not None:
            quality_gate.config.enabled = enabled
            logger.info(f"Quality gate {'enabled' if enabled else 'disabled'}")

        return {
            "success": True,
            "config": {
                "strict_mode": quality_gate.config.strict_mode,
                "enabled": quality_gate.config.enabled,
                "action_on_bad": quality_gate.config.action_on_bad.value,
                "action_on_comm_loss": quality_gate.config.action_on_comm_loss.value,
            }
        }

    except Exception as e:
        logger.error(f"Error configuring quality gate: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure quality gate: {str(e)}"
        )


@router.post("/gate/reset")
async def reset_quality_gate_stats(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Reset Quality Gate statistics.

    Clears accumulated statistics but keeps configuration intact.
    """
    if not QUALITY_GATE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Quality gate service not available"
        )

    try:
        quality_gate = get_quality_gate()
        quality_gate.reset_statistics()

        return {
            "success": True,
            "message": "Quality gate statistics reset"
        }

    except Exception as e:
        logger.error(f"Error resetting quality gate stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset quality gate statistics: {str(e)}"
        )
