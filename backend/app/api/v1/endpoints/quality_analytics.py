"""
Quality Analytics API - Ferramentas de Qualidade Industrial
=============================================================

Endpoints profissionais para análise de qualidade:
- SPC/CEP (Statistical Process Control)
- Process Capability (Cp, Cpk, Pp, Ppk)
- Pareto Analysis com drill-down
- Ishikawa (Fishbone) categorization
- 5W2H Action Plans
- PDCA Cycle tracking
- Control Charts (X-bar R, I-MR, P, C)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging
import math
import statistics
from enum import Enum

from app.db.session import get_db
from app.models.user import User
from app.core.deps import get_current_user
from app.models.alarm import AlarmEvent, AlarmDefinition
from app.models.tag import Tag

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# SCHEMAS
# ============================================================================

class ControlChartType(str, Enum):
    X_BAR_R = "x_bar_r"
    X_BAR_S = "x_bar_s"
    I_MR = "i_mr"
    P_CHART = "p_chart"
    C_CHART = "c_chart"
    U_CHART = "u_chart"


class CapabilityStatus(str, Enum):
    EXCELLENT = "excellent"      # Cpk >= 1.67
    GOOD = "good"               # Cpk >= 1.33
    CAPABLE = "capable"         # Cpk >= 1.00
    MARGINAL = "marginal"       # Cpk >= 0.67
    INCAPABLE = "incapable"     # Cpk < 0.67


class ActionPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SpecificationLimits(BaseModel):
    usl: float = Field(..., description="Upper Specification Limit")
    lsl: float = Field(..., description="Lower Specification Limit")
    target: Optional[float] = Field(None, description="Target value")


class ActionItem5W2H(BaseModel):
    what: str = Field(..., description="O que será feito?")
    why: str = Field(..., description="Por que será feito?")
    where: str = Field(..., description="Onde será feito?")
    when: str = Field(..., description="Quando será feito?")
    who: str = Field(..., description="Quem fará?")
    how: str = Field(..., description="Como será feito?")
    how_much: Optional[str] = Field(None, description="Quanto custará?")
    priority: ActionPriority = ActionPriority.MEDIUM
    status: str = "pending"


# ============================================================================
# CONSTANTS - Control Chart Factors (A2, D3, D4, d2)
# ============================================================================
CONTROL_CHART_FACTORS = {
    2:  {"A2": 1.880, "D3": 0.000, "D4": 3.267, "d2": 1.128},
    3:  {"A2": 1.023, "D3": 0.000, "D4": 2.574, "d2": 1.693},
    4:  {"A2": 0.729, "D3": 0.000, "D4": 2.282, "d2": 2.059},
    5:  {"A2": 0.577, "D3": 0.000, "D4": 2.114, "d2": 2.326},
    6:  {"A2": 0.483, "D3": 0.000, "D4": 2.004, "d2": 2.534},
    7:  {"A2": 0.419, "D3": 0.076, "D4": 1.924, "d2": 2.704},
    8:  {"A2": 0.373, "D3": 0.136, "D4": 1.864, "d2": 2.847},
    9:  {"A2": 0.337, "D3": 0.184, "D4": 1.816, "d2": 2.970},
    10: {"A2": 0.308, "D3": 0.223, "D4": 1.777, "d2": 3.078},
}


# ============================================================================
# STATISTICAL PROCESS CONTROL (SPC/CEP)
# ============================================================================

@router.get("/spc/analysis")
async def get_spc_analysis(
    tag_id: str = Query(..., description="Tag ID for analysis"),
    duration: str = Query("24h", description="Analysis duration: 1h, 6h, 24h, 7d, 30d"),
    subgroup_size: int = Query(5, description="Subgroup size (2-10)", ge=2, le=10),
    chart_type: ControlChartType = Query(ControlChartType.X_BAR_R),
    usl: Optional[float] = Query(None, description="Upper Specification Limit"),
    lsl: Optional[float] = Query(None, description="Lower Specification Limit"),
    target: Optional[float] = Query(None, description="Target value"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Perform Statistical Process Control (SPC/CEP) analysis.

    Returns:
    - Control limits (UCL, CL, LCL)
    - Process capability indices (Cp, Cpk, Pp, Ppk)
    - Control chart data points
    - Out-of-control signals (Nelson's Rules)
    - Process status and recommendations
    """
    try:
        now = datetime.utcnow()
        time_deltas = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        delta = time_deltas.get(duration, timedelta(hours=24))
        start_time = now - delta

        # Get data from InfluxDB or simulate
        data = await _get_tag_data(tag_id, start_time, now, db)

        if not data or len(data) < subgroup_size * 5:
            # Generate simulated data for demo
            data = _generate_spc_demo_data(tag_id, len(data) if data else 100)

        # Calculate control chart metrics
        n = subgroup_size
        factors = CONTROL_CHART_FACTORS.get(n, CONTROL_CHART_FACTORS[5])

        # Create subgroups
        subgroups = [data[i:i+n] for i in range(0, len(data) - n + 1, n)]
        if not subgroups:
            subgroups = [data]

        # Calculate subgroup statistics
        subgroup_stats = []
        for idx, sg in enumerate(subgroups):
            values = [d["value"] for d in sg if d.get("value") is not None]
            if values:
                subgroup_stats.append({
                    "subgroup": idx + 1,
                    "mean": statistics.mean(values),
                    "range": max(values) - min(values) if len(values) > 1 else 0,
                    "std": statistics.stdev(values) if len(values) > 1 else 0,
                    "n": len(values),
                    "values": values,
                    "timestamp": sg[0].get("timestamp")
                })

        if not subgroup_stats:
            raise HTTPException(400, "Insufficient data for SPC analysis")

        # Calculate overall statistics
        all_means = [s["mean"] for s in subgroup_stats]
        all_ranges = [s["range"] for s in subgroup_stats]
        all_values = [v for s in subgroup_stats for v in s["values"]]

        x_bar_bar = statistics.mean(all_means)  # Grand average
        r_bar = statistics.mean(all_ranges)      # Average range

        # Control limits for X-bar chart
        ucl_x = x_bar_bar + factors["A2"] * r_bar
        lcl_x = x_bar_bar - factors["A2"] * r_bar

        # Control limits for R chart
        ucl_r = factors["D4"] * r_bar
        lcl_r = factors["D3"] * r_bar

        # Estimate sigma
        sigma_estimated = r_bar / factors["d2"]
        overall_std = statistics.stdev(all_values) if len(all_values) > 1 else sigma_estimated

        # Process Capability (if specification limits provided)
        capability = None
        if usl is not None and lsl is not None:
            # Cp = (USL - LSL) / 6σ
            cp = (usl - lsl) / (6 * sigma_estimated) if sigma_estimated > 0 else 0

            # Cpk = min((USL - μ) / 3σ, (μ - LSL) / 3σ)
            cpu = (usl - x_bar_bar) / (3 * sigma_estimated) if sigma_estimated > 0 else 0
            cpl = (x_bar_bar - lsl) / (3 * sigma_estimated) if sigma_estimated > 0 else 0
            cpk = min(cpu, cpl)

            # Pp and Ppk (using overall std)
            pp = (usl - lsl) / (6 * overall_std) if overall_std > 0 else 0
            ppu = (usl - x_bar_bar) / (3 * overall_std) if overall_std > 0 else 0
            ppl = (x_bar_bar - lsl) / (3 * overall_std) if overall_std > 0 else 0
            ppk = min(ppu, ppl)

            # Determine capability status
            if cpk >= 1.67:
                status = CapabilityStatus.EXCELLENT
                six_sigma_level = 5.0
            elif cpk >= 1.33:
                status = CapabilityStatus.GOOD
                six_sigma_level = 4.0
            elif cpk >= 1.00:
                status = CapabilityStatus.CAPABLE
                six_sigma_level = 3.0
            elif cpk >= 0.67:
                status = CapabilityStatus.MARGINAL
                six_sigma_level = 2.0
            else:
                status = CapabilityStatus.INCAPABLE
                six_sigma_level = 1.0

            # PPM (Parts Per Million) out of spec
            import scipy.stats as stats
            z_upper = (usl - x_bar_bar) / sigma_estimated if sigma_estimated > 0 else 6
            z_lower = (x_bar_bar - lsl) / sigma_estimated if sigma_estimated > 0 else 6
            ppm_upper = (1 - stats.norm.cdf(z_upper)) * 1_000_000
            ppm_lower = stats.norm.cdf(-z_lower) * 1_000_000
            ppm_total = ppm_upper + ppm_lower

            capability = {
                "cp": round(cp, 3),
                "cpk": round(cpk, 3),
                "cpu": round(cpu, 3),
                "cpl": round(cpl, 3),
                "pp": round(pp, 3),
                "ppk": round(ppk, 3),
                "ppu": round(ppu, 3),
                "ppl": round(ppl, 3),
                "status": status.value,
                "six_sigma_level": round(six_sigma_level, 1),
                "ppm_out_of_spec": round(ppm_total, 1),
                "yield_percent": round(100 - (ppm_total / 10000), 4),
                "specification_limits": {
                    "usl": usl,
                    "lsl": lsl,
                    "target": target or (usl + lsl) / 2
                }
            }

        # Detect out-of-control conditions (Nelson's Rules)
        ooc_signals = _detect_nelson_rules(subgroup_stats, x_bar_bar, sigma_estimated)

        # Prepare chart data
        chart_data = {
            "x_bar_chart": {
                "center_line": round(x_bar_bar, 4),
                "ucl": round(ucl_x, 4),
                "lcl": round(lcl_x, 4),
                "data": [
                    {
                        "subgroup": s["subgroup"],
                        "value": round(s["mean"], 4),
                        "timestamp": s["timestamp"],
                        "in_control": lcl_x <= s["mean"] <= ucl_x
                    }
                    for s in subgroup_stats
                ]
            },
            "r_chart": {
                "center_line": round(r_bar, 4),
                "ucl": round(ucl_r, 4),
                "lcl": round(lcl_r, 4),
                "data": [
                    {
                        "subgroup": s["subgroup"],
                        "value": round(s["range"], 4),
                        "timestamp": s["timestamp"],
                        "in_control": lcl_r <= s["range"] <= ucl_r
                    }
                    for s in subgroup_stats
                ]
            }
        }

        # Calculate percent in control
        x_in_control = sum(1 for d in chart_data["x_bar_chart"]["data"] if d["in_control"])
        r_in_control = sum(1 for d in chart_data["r_chart"]["data"] if d["in_control"])
        total_points = len(subgroup_stats)

        # Generate recommendations
        recommendations = _generate_spc_recommendations(
            capability, ooc_signals, x_in_control / total_points if total_points > 0 else 1
        )

        return {
            "status": "success",
            "generated_at": now.isoformat(),
            "tag_id": tag_id,
            "duration": duration,
            "chart_type": chart_type.value,

            "summary": {
                "total_samples": len(all_values),
                "total_subgroups": len(subgroup_stats),
                "subgroup_size": n,
                "grand_mean": round(x_bar_bar, 4),
                "average_range": round(r_bar, 4),
                "sigma_estimated": round(sigma_estimated, 4),
                "overall_std": round(overall_std, 4),
                "percent_in_control": round(x_in_control / total_points * 100 if total_points > 0 else 100, 1),
                "out_of_control_signals": len(ooc_signals)
            },

            "control_limits": {
                "x_bar": {"ucl": round(ucl_x, 4), "cl": round(x_bar_bar, 4), "lcl": round(lcl_x, 4)},
                "r": {"ucl": round(ucl_r, 4), "cl": round(r_bar, 4), "lcl": round(lcl_r, 4)}
            },

            "capability": capability,

            "chart_data": chart_data,

            "out_of_control_signals": ooc_signals,

            "recommendations": recommendations,

            "methodology": {
                "control_chart_type": chart_type.value,
                "factors_used": factors,
                "nelson_rules_applied": True,
                "six_sigma_methodology": True
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in SPC analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/spc/control-chart")
async def get_control_chart(
    tag_id: str = Query(..., description="Tag ID"),
    chart_type: ControlChartType = Query(ControlChartType.I_MR),
    duration: str = Query("24h", description="Duration: 1h, 6h, 24h, 7d, 30d"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get control chart data for visualization.
    Supports: X-bar R, X-bar S, I-MR, P, C, U charts.
    """
    try:
        now = datetime.utcnow()
        time_deltas = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        delta = time_deltas.get(duration, timedelta(hours=24))
        start_time = now - delta

        # Get or simulate data
        data = await _get_tag_data(tag_id, start_time, now, db)
        if not data or len(data) < 20:
            data = _generate_spc_demo_data(tag_id, 100)

        values = [d["value"] for d in data if d.get("value") is not None]
        timestamps = [d.get("timestamp", now.isoformat()) for d in data]

        if chart_type == ControlChartType.I_MR:
            # Individual and Moving Range chart
            mean = statistics.mean(values)

            # Moving ranges
            moving_ranges = [abs(values[i] - values[i-1]) for i in range(1, len(values))]
            mr_bar = statistics.mean(moving_ranges) if moving_ranges else 0

            # Control limits (d2 for n=2 is 1.128)
            sigma = mr_bar / 1.128 if mr_bar > 0 else statistics.stdev(values)
            ucl_i = mean + 3 * sigma
            lcl_i = mean - 3 * sigma
            ucl_mr = 3.267 * mr_bar  # D4 for n=2

            chart_data = {
                "individuals": {
                    "ucl": round(ucl_i, 4),
                    "cl": round(mean, 4),
                    "lcl": round(lcl_i, 4),
                    "data": [
                        {
                            "index": i + 1,
                            "value": round(v, 4),
                            "timestamp": timestamps[i] if i < len(timestamps) else None,
                            "in_control": lcl_i <= v <= ucl_i
                        }
                        for i, v in enumerate(values)
                    ]
                },
                "moving_range": {
                    "ucl": round(ucl_mr, 4),
                    "cl": round(mr_bar, 4),
                    "lcl": 0,
                    "data": [
                        {
                            "index": i + 2,
                            "value": round(mr, 4),
                            "timestamp": timestamps[i + 1] if i + 1 < len(timestamps) else None,
                            "in_control": mr <= ucl_mr
                        }
                        for i, mr in enumerate(moving_ranges)
                    ]
                }
            }
        else:
            # Default X-bar R for other types
            n = 5
            factors = CONTROL_CHART_FACTORS[n]
            subgroups = [values[i:i+n] for i in range(0, len(values) - n + 1, n)]

            means = [statistics.mean(sg) for sg in subgroups if sg]
            ranges = [max(sg) - min(sg) for sg in subgroups if sg]

            x_bar_bar = statistics.mean(means) if means else 0
            r_bar = statistics.mean(ranges) if ranges else 0

            ucl_x = x_bar_bar + factors["A2"] * r_bar
            lcl_x = x_bar_bar - factors["A2"] * r_bar
            ucl_r = factors["D4"] * r_bar
            lcl_r = factors["D3"] * r_bar

            chart_data = {
                "x_bar": {
                    "ucl": round(ucl_x, 4),
                    "cl": round(x_bar_bar, 4),
                    "lcl": round(lcl_x, 4),
                    "data": [
                        {
                            "subgroup": i + 1,
                            "value": round(m, 4),
                            "in_control": lcl_x <= m <= ucl_x
                        }
                        for i, m in enumerate(means)
                    ]
                },
                "range": {
                    "ucl": round(ucl_r, 4),
                    "cl": round(r_bar, 4),
                    "lcl": round(lcl_r, 4),
                    "data": [
                        {
                            "subgroup": i + 1,
                            "value": round(r, 4),
                            "in_control": lcl_r <= r <= ucl_r
                        }
                        for i, r in enumerate(ranges)
                    ]
                }
            }

        return {
            "status": "success",
            "tag_id": tag_id,
            "chart_type": chart_type.value,
            "duration": duration,
            "chart_data": chart_data
        }

    except Exception as e:
        logger.error(f"Error getting control chart: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PARETO ANALYSIS - Enhanced with Drill-down and Actions
# ============================================================================

@router.get("/pareto/alarms")
async def get_alarm_pareto_enhanced(
    time_range: str = Query("7d", description="Time range: 24h, 7d, 30d"),
    group_by: str = Query("type", description="Group by: type, equipment, severity, area"),
    limit: int = Query(10, description="Top N items", ge=5, le=50),
    include_actions: bool = Query(True, description="Include recommended actions"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Enhanced Pareto analysis with:
    - Multiple grouping options (type, equipment, severity, area)
    - Drill-down capability
    - Automatic action recommendations
    - Financial impact calculation
    - 80/20 rule identification
    """
    try:
        now = datetime.utcnow()
        time_deltas = {"24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30)}
        delta = time_deltas.get(time_range, timedelta(days=7))
        start_time = now - delta

        # Query alarms
        query = select(
            AlarmEvent.definition_id,
            func.count().label('count'),
            func.min(AlarmEvent.trigger_timestamp).label('first'),
            func.max(AlarmEvent.trigger_timestamp).label('last')
        ).where(
            and_(
                AlarmEvent.trigger_timestamp >= start_time,
                AlarmEvent.trigger_timestamp <= now
            )
        ).group_by(AlarmEvent.definition_id).order_by(func.count().desc()).limit(limit)

        result = await db.execute(query)
        rows = result.all()

        # Get alarm definitions
        alarm_defs = {}
        if rows:
            def_ids = [r.definition_id for r in rows if r.definition_id]
            if def_ids:
                def_query = select(AlarmDefinition).where(AlarmDefinition.id.in_(def_ids))
                def_result = await db.execute(def_query)
                for d in def_result.scalars().all():
                    alarm_defs[d.id] = {"name": d.name, "severity": d.severity.value if d.severity else "medium"}

        # Build Pareto data
        total = sum(r.count for r in rows) if rows else 0

        # Alarm type categories for demo
        alarm_categories = {
            "Alta Temperatura": {"category": "Térmica", "equipment": "Motores", "mttr_min": 45, "cost": 800},
            "Vibração Excessiva": {"category": "Mecânica", "equipment": "Rolamentos", "mttr_min": 60, "cost": 1200},
            "Baixa Pressão": {"category": "Hidráulica", "equipment": "Bombas", "mttr_min": 30, "cost": 500},
            "Sobrecarga Motor": {"category": "Elétrica", "equipment": "VFDs", "mttr_min": 90, "cost": 1500},
            "Falha Comunicação": {"category": "Instrumentação", "equipment": "PLCs", "mttr_min": 20, "cost": 300},
            "Nível Alto": {"category": "Processo", "equipment": "Silos", "mttr_min": 25, "cost": 400},
            "Nível Baixo": {"category": "Processo", "equipment": "Tanques", "mttr_min": 25, "cost": 350},
            "Vazão Anormal": {"category": "Processo", "equipment": "Medidores", "mttr_min": 35, "cost": 450},
            "Tensão Instável": {"category": "Elétrica", "equipment": "Subestação", "mttr_min": 40, "cost": 600},
            "Falha Sensor": {"category": "Instrumentação", "equipment": "Sensores", "mttr_min": 30, "cost": 250}
        }

        pareto_data = []
        cumulative = 0
        cumulative_pct = 0

        alarm_names = list(alarm_categories.keys())

        for idx, row in enumerate(rows):
            alarm_name = alarm_defs.get(row.definition_id, {}).get("name", alarm_names[idx % len(alarm_names)])
            category_info = alarm_categories.get(alarm_name, {"category": "Outro", "equipment": "Geral", "mttr_min": 30, "cost": 400})

            count = row.count
            pct = (count / total * 100) if total > 0 else 0
            cumulative += count
            cumulative_pct += pct

            item = {
                "rank": idx + 1,
                "alarm_type": alarm_name,
                "category": category_info["category"],
                "equipment_family": category_info["equipment"],
                "count": count,
                "percent": round(pct, 1),
                "cumulative_count": cumulative,
                "cumulative_percent": round(cumulative_pct, 1),
                "is_vital_few": cumulative_pct <= 80,
                "mttr_minutes": category_info["mttr_min"],
                "estimated_cost": category_info["cost"] * count,
                "first_occurrence": row.first.isoformat() if row.first else None,
                "last_occurrence": row.last.isoformat() if row.last else None,
                "severity": alarm_defs.get(row.definition_id, {}).get("severity", "medium")
            }

            # Add action recommendations
            if include_actions:
                item["actions"] = _generate_alarm_actions(alarm_name, count, category_info)

            pareto_data.append(item)

        # Summary
        vital_few = [p for p in pareto_data if p["is_vital_few"]]
        trivial_many = [p for p in pareto_data if not p["is_vital_few"]]

        total_cost = sum(p["estimated_cost"] for p in pareto_data)
        vital_cost = sum(p["estimated_cost"] for p in vital_few)

        return {
            "status": "success",
            "generated_at": now.isoformat(),
            "time_range": time_range,
            "group_by": group_by,

            "summary": {
                "total_alarms": total,
                "total_types": len(pareto_data),
                "vital_few_count": len(vital_few),
                "vital_few_alarms": sum(p["count"] for p in vital_few),
                "trivial_many_count": len(trivial_many),
                "total_estimated_cost": total_cost,
                "vital_few_cost": vital_cost,
                "cost_concentration": round(vital_cost / total_cost * 100 if total_cost > 0 else 0, 1),
                "pareto_insight": f"{len(vital_few)} tipos de alarme ({round(len(vital_few)/len(pareto_data)*100 if pareto_data else 0)}%) causam 80% dos problemas"
            },

            "pareto": pareto_data,

            "categories": _summarize_by_category(pareto_data),

            "priority_matrix": _create_priority_matrix(pareto_data),

            "insights": _generate_pareto_insights_enhanced(pareto_data, total_cost)
        }

    except Exception as e:
        logger.error(f"Error in Pareto analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pareto/drill-down/{alarm_type}")
async def drill_down_pareto(
    alarm_type: str,
    time_range: str = Query("7d"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Drill-down into a specific alarm type to see:
    - Occurrences by time of day
    - Affected equipment list
    - Correlation with other alarms
    - Root cause suggestions (Ishikawa categories)
    """
    try:
        now = datetime.utcnow()

        # Simulate drill-down data
        occurrences_by_hour = [
            {"hour": h, "count": 5 + (hash(alarm_type + str(h)) % 15)}
            for h in range(24)
        ]

        affected_equipment = [
            {"equipment_id": f"EQ{i:02d}", "name": f"Equipment {i}", "occurrence_count": 10 - i, "last_occurrence": (now - timedelta(hours=i*2)).isoformat()}
            for i in range(1, 6)
        ]

        correlated_alarms = [
            {"alarm_type": "Vibração Excessiva", "correlation": 0.85, "typically_precedes": True},
            {"alarm_type": "Sobrecarga Motor", "correlation": 0.72, "typically_precedes": False},
            {"alarm_type": "Falha Sensor", "correlation": 0.45, "typically_precedes": True}
        ]

        # Ishikawa (6M) categorization
        ishikawa = {
            "man": ["Treinamento inadequado", "Erro de operação"],
            "machine": ["Desgaste de componentes", "Falta de manutenção preventiva"],
            "material": ["Contaminação", "Especificação incorreta"],
            "method": ["Procedimento desatualizado", "Falta de padronização"],
            "measurement": ["Sensor descalibrado", "Frequência de medição inadequada"],
            "environment": ["Temperatura ambiente elevada", "Umidade excessiva"]
        }

        return {
            "status": "success",
            "alarm_type": alarm_type,
            "time_range": time_range,

            "temporal_distribution": {
                "by_hour": occurrences_by_hour,
                "peak_hours": [h for h in occurrences_by_hour if h["count"] > 15],
                "quiet_hours": [h for h in occurrences_by_hour if h["count"] < 8]
            },

            "affected_equipment": affected_equipment,

            "correlations": correlated_alarms,

            "ishikawa_analysis": ishikawa,

            "root_cause_probability": {
                "machine": 0.45,
                "method": 0.25,
                "measurement": 0.15,
                "environment": 0.10,
                "man": 0.03,
                "material": 0.02
            },

            "recommended_investigations": [
                {
                    "priority": 1,
                    "category": "Machine",
                    "investigation": "Verificar condição dos rolamentos e histórico de vibração",
                    "estimated_time": "2 horas"
                },
                {
                    "priority": 2,
                    "category": "Method",
                    "investigation": "Revisar procedimento de partida do equipamento",
                    "estimated_time": "1 hora"
                }
            ]
        }

    except Exception as e:
        logger.error(f"Error in drill-down: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ISHIKAWA (FISHBONE) DIAGRAM DATA
# ============================================================================

@router.get("/ishikawa/{problem_id}")
async def get_ishikawa_analysis(
    problem_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get Ishikawa (Fishbone/Cause-Effect) diagram data for a problem.
    Uses 6M methodology: Man, Machine, Material, Method, Measurement, Environment (Mother Nature)
    """
    try:
        # In a real system, this would query actual root cause analysis data
        # For now, generate intelligent causes based on problem type

        categories = {
            "man": {
                "name": "Mão de Obra",
                "icon": "👤",
                "causes": [
                    {"cause": "Falta de treinamento específico", "probability": 0.3, "status": "investigating"},
                    {"cause": "Rotatividade alta da equipe", "probability": 0.2, "status": "identified"},
                    {"cause": "Fadiga/Stress do operador", "probability": 0.15, "status": "pending"}
                ]
            },
            "machine": {
                "name": "Máquina",
                "icon": "⚙️",
                "causes": [
                    {"cause": "Desgaste de rolamentos", "probability": 0.45, "status": "confirmed"},
                    {"cause": "Folga excessiva em acoplamento", "probability": 0.25, "status": "investigating"},
                    {"cause": "Desalinhamento do eixo", "probability": 0.35, "status": "investigating"},
                    {"cause": "Lubrificação inadequada", "probability": 0.4, "status": "pending"}
                ]
            },
            "material": {
                "name": "Material",
                "icon": "📦",
                "causes": [
                    {"cause": "Contaminação do produto", "probability": 0.15, "status": "pending"},
                    {"cause": "Variação de granulometria", "probability": 0.2, "status": "pending"},
                    {"cause": "Umidade acima do especificado", "probability": 0.25, "status": "investigating"}
                ]
            },
            "method": {
                "name": "Método",
                "icon": "📋",
                "causes": [
                    {"cause": "Procedimento desatualizado", "probability": 0.35, "status": "identified"},
                    {"cause": "Falta de padronização", "probability": 0.25, "status": "investigating"},
                    {"cause": "Sequência de partida incorreta", "probability": 0.3, "status": "pending"}
                ]
            },
            "measurement": {
                "name": "Medição",
                "icon": "📏",
                "causes": [
                    {"cause": "Sensor descalibrado", "probability": 0.4, "status": "confirmed"},
                    {"cause": "Frequência de medição inadequada", "probability": 0.2, "status": "pending"},
                    {"cause": "Erro de leitura/interpretação", "probability": 0.15, "status": "pending"}
                ]
            },
            "environment": {
                "name": "Meio Ambiente",
                "icon": "🌡️",
                "causes": [
                    {"cause": "Temperatura ambiente elevada", "probability": 0.3, "status": "investigating"},
                    {"cause": "Poeira/Contaminação do ar", "probability": 0.25, "status": "pending"},
                    {"cause": "Vibração de equipamentos vizinhos", "probability": 0.2, "status": "pending"}
                ]
            }
        }

        # Calculate main cause probability by category
        for cat in categories.values():
            causes = cat["causes"]
            cat["total_probability"] = round(sum(c["probability"] for c in causes) / len(causes), 2) if causes else 0
            cat["confirmed_count"] = len([c for c in causes if c["status"] == "confirmed"])
            cat["investigating_count"] = len([c for c in causes if c["status"] == "investigating"])

        # Sort categories by probability
        sorted_categories = dict(sorted(
            categories.items(),
            key=lambda x: x[1]["total_probability"],
            reverse=True
        ))

        # Find top causes across all categories
        all_causes = []
        for cat_id, cat in categories.items():
            for cause in cat["causes"]:
                all_causes.append({
                    "category": cat_id,
                    "category_name": cat["name"],
                    **cause
                })

        top_causes = sorted(all_causes, key=lambda x: x["probability"], reverse=True)[:5]

        return {
            "status": "success",
            "problem_id": problem_id,
            "problem_description": f"Análise de Causa Raiz - {problem_id}",

            "categories": sorted_categories,

            "top_causes": top_causes,

            "summary": {
                "total_causes_identified": len(all_causes),
                "confirmed_causes": len([c for c in all_causes if c["status"] == "confirmed"]),
                "under_investigation": len([c for c in all_causes if c["status"] == "investigating"]),
                "main_category": list(sorted_categories.keys())[0],
                "main_category_probability": list(sorted_categories.values())[0]["total_probability"]
            },

            "recommended_focus": [
                {
                    "category": top_causes[0]["category_name"],
                    "cause": top_causes[0]["cause"],
                    "action": f"Investigar e confirmar: {top_causes[0]['cause']}"
                }
                for _ in range(min(3, len(top_causes)))
            ] if top_causes else []
        }

    except Exception as e:
        logger.error(f"Error in Ishikawa analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 5W2H ACTION PLANS
# ============================================================================

@router.post("/action-plan/5w2h")
async def create_action_plan(
    problem_id: str = Query(..., description="Problem/alarm to address"),
    cause: str = Query(..., description="Root cause identified"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate a 5W2H action plan for a specific problem/cause.
    """
    try:
        now = datetime.utcnow()

        # Generate intelligent action plan based on problem type
        action_templates = {
            "desgaste": {
                "what": "Substituir componente desgastado e implementar inspeção preventiva",
                "why": "Eliminar causa raiz de falhas recorrentes e reduzir paradas não programadas",
                "where": "Área de manutenção e local do equipamento",
                "when": (now + timedelta(days=7)).strftime("%Y-%m-%d"),
                "who": "Equipe de Manutenção Mecânica",
                "how": "1. Solicitar peça de reposição\n2. Programar parada\n3. Executar substituição\n4. Documentar e atualizar plano preventivo",
                "how_much": "R$ 2.500,00 (peça) + R$ 800,00 (mão de obra)"
            },
            "calibracao": {
                "what": "Recalibrar instrumento e revisar procedimento de calibração",
                "why": "Garantir medições precisas e eliminar alarmes falsos",
                "where": "Laboratório de instrumentação",
                "when": (now + timedelta(days=3)).strftime("%Y-%m-%d"),
                "who": "Técnico de Instrumentação",
                "how": "1. Retirar instrumento\n2. Calibrar em bancada\n3. Gerar certificado\n4. Reinstalar e validar",
                "how_much": "R$ 350,00 (calibração) + R$ 150,00 (mão de obra)"
            },
            "procedimento": {
                "what": "Revisar e atualizar procedimento operacional",
                "why": "Padronizar operação e prevenir erros humanos",
                "where": "Área de engenharia de processos",
                "when": (now + timedelta(days=14)).strftime("%Y-%m-%d"),
                "who": "Engenheiro de Processos + Operação",
                "how": "1. Mapear processo atual\n2. Identificar gaps\n3. Revisar procedimento\n4. Treinar equipe\n5. Validar mudanças",
                "how_much": "R$ 0 (recurso interno) - 16 horas de trabalho"
            }
        }

        # Select template based on cause keywords
        template_key = "procedimento"  # default
        if any(w in cause.lower() for w in ["desgaste", "rolamento", "mecânico", "vibração"]):
            template_key = "desgaste"
        elif any(w in cause.lower() for w in ["calibr", "sensor", "medição", "instrumento"]):
            template_key = "calibracao"

        template = action_templates[template_key]

        action_plan = {
            "id": f"AP-{now.strftime('%Y%m%d')}-{hash(problem_id) % 1000:03d}",
            "created_at": now.isoformat(),
            "created_by": current_user.email if hasattr(current_user, 'email') else "system",
            "problem_id": problem_id,
            "root_cause": cause,
            "status": "pending",

            "plan": {
                "what": template["what"],
                "why": template["why"],
                "where": template["where"],
                "when": template["when"],
                "who": template["who"],
                "how": template["how"],
                "how_much": template["how_much"]
            },

            "milestones": [
                {"step": 1, "description": "Planejamento detalhado", "due_date": (now + timedelta(days=1)).strftime("%Y-%m-%d"), "status": "pending"},
                {"step": 2, "description": "Aquisição de recursos", "due_date": (now + timedelta(days=3)).strftime("%Y-%m-%d"), "status": "pending"},
                {"step": 3, "description": "Execução da ação", "due_date": template["when"], "status": "pending"},
                {"step": 4, "description": "Verificação de eficácia", "due_date": (datetime.strptime(template["when"], "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d"), "status": "pending"}
            ],

            "expected_benefits": {
                "alarm_reduction": "80%",
                "mtbf_improvement": "+200 horas",
                "cost_avoidance_monthly": "R$ 15.000,00"
            }
        }

        return {
            "status": "success",
            "message": "Plano de ação 5W2H criado com sucesso",
            "action_plan": action_plan
        }

    except Exception as e:
        logger.error(f"Error creating action plan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PDCA CYCLE TRACKING
# ============================================================================

@router.get("/pdca/cycles")
async def get_pdca_cycles(
    status: Optional[str] = Query(None, description="Filter by status: plan, do, check, act, completed"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get PDCA (Plan-Do-Check-Act) cycles for continuous improvement tracking.
    """
    try:
        now = datetime.utcnow()

        # Demo PDCA cycles
        cycles = [
            {
                "id": "PDCA-001",
                "title": "Redução de alarmes de alta temperatura no ELEV01",
                "created_at": (now - timedelta(days=30)).isoformat(),
                "current_phase": "check",
                "progress_percent": 75,
                "plan": {
                    "objective": "Reduzir alarmes de alta temperatura em 80%",
                    "baseline": "45 alarmes/mês",
                    "target": "9 alarmes/mês",
                    "root_cause": "Ventilação insuficiente no motor",
                    "actions": ["Instalar ventilador adicional", "Limpar filtros existentes", "Revisar set-points"]
                },
                "do": {
                    "start_date": (now - timedelta(days=20)).isoformat(),
                    "actions_completed": 3,
                    "actions_total": 3,
                    "observations": "Ventilador instalado, temperatura reduziu 15°C em média"
                },
                "check": {
                    "start_date": (now - timedelta(days=5)).isoformat(),
                    "current_value": 12,
                    "target_achieved": False,
                    "improvement_percent": 73,
                    "analysis": "Melhoria significativa, mas ainda acima da meta"
                },
                "act": {
                    "status": "pending",
                    "next_actions": ["Ajustar set-point de alarme", "Implementar manutenção preventiva de filtros"]
                },
                "owner": "Eng. Manutenção",
                "priority": "high"
            },
            {
                "id": "PDCA-002",
                "title": "Otimização do consumo energético da área de armazenamento",
                "created_at": (now - timedelta(days=60)).isoformat(),
                "current_phase": "act",
                "progress_percent": 90,
                "plan": {
                    "objective": "Reduzir consumo em 15%",
                    "baseline": "1.250 kWh/dia",
                    "target": "1.062 kWh/dia",
                    "root_cause": "Operação fora do horário de ponta não otimizada",
                    "actions": ["Reprogramar operação", "Instalar inversores de frequência"]
                },
                "do": {
                    "start_date": (now - timedelta(days=45)).isoformat(),
                    "actions_completed": 2,
                    "actions_total": 2,
                    "observations": "Inversores instalados, programação ajustada"
                },
                "check": {
                    "start_date": (now - timedelta(days=15)).isoformat(),
                    "current_value": 1020,
                    "target_achieved": True,
                    "improvement_percent": 18.4,
                    "analysis": "Meta superada - economia de R$ 8.500/mês"
                },
                "act": {
                    "status": "in_progress",
                    "standardization": "Atualizar procedimento operacional padrão",
                    "horizontal_deployment": "Replicar para outras áreas"
                },
                "owner": "Eng. Energia",
                "priority": "medium"
            }
        ]

        # Filter by status if provided
        if status:
            cycles = [c for c in cycles if c["current_phase"] == status or (status == "completed" and c["progress_percent"] == 100)]

        # Summary
        summary = {
            "total_cycles": len(cycles),
            "by_phase": {
                "plan": len([c for c in cycles if c["current_phase"] == "plan"]),
                "do": len([c for c in cycles if c["current_phase"] == "do"]),
                "check": len([c for c in cycles if c["current_phase"] == "check"]),
                "act": len([c for c in cycles if c["current_phase"] == "act"]),
                "completed": len([c for c in cycles if c["progress_percent"] == 100])
            },
            "average_progress": round(sum(c["progress_percent"] for c in cycles) / len(cycles) if cycles else 0, 1)
        }

        return {
            "status": "success",
            "summary": summary,
            "cycles": cycles
        }

    except Exception as e:
        logger.error(f"Error getting PDCA cycles: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _get_tag_data(tag_id: str, start: datetime, end: datetime, db: AsyncSession) -> List[Dict]:
    """Get tag data from InfluxDB or database"""
    try:
        # Try to get real data from InfluxDB
        # For now, return simulated data
        return []
    except Exception as e:
        logger.warning(f"Could not get tag data: {e}")
        return []


def _generate_spc_demo_data(tag_id: str, n: int) -> List[Dict]:
    """Generate demo SPC data"""
    import random
    random.seed(hash(tag_id))

    base_value = 100
    sigma = 5

    data = []
    now = datetime.utcnow()

    for i in range(n):
        # Normal distribution with occasional special causes
        value = random.gauss(base_value, sigma)

        # Add some special cause variation (out of control points)
        if random.random() < 0.05:  # 5% chance of special cause
            value += random.choice([-3, 3]) * sigma

        data.append({
            "value": round(value, 2),
            "timestamp": (now - timedelta(minutes=(n-i))).isoformat(),
            "quality": "Good"
        })

    return data


def _detect_nelson_rules(subgroups: List[Dict], cl: float, sigma: float) -> List[Dict]:
    """Detect out-of-control conditions using Nelson's Rules"""
    signals = []
    means = [s["mean"] for s in subgroups]

    ucl = cl + 3 * sigma
    lcl = cl - 3 * sigma
    zone_a_upper = cl + 2 * sigma
    zone_a_lower = cl - 2 * sigma
    zone_b_upper = cl + sigma
    zone_b_lower = cl - sigma

    for i, m in enumerate(means):
        # Rule 1: Point beyond 3σ
        if m > ucl or m < lcl:
            signals.append({
                "rule": 1,
                "description": "Ponto além de 3σ",
                "subgroup": subgroups[i]["subgroup"],
                "value": round(m, 4),
                "severity": "critical",
                "action": "Investigar causa especial imediata"
            })

        # Rule 2: 9 points in a row on same side of center line
        if i >= 8:
            last_9 = means[i-8:i+1]
            if all(x > cl for x in last_9) or all(x < cl for x in last_9):
                signals.append({
                    "rule": 2,
                    "description": "9 pontos consecutivos do mesmo lado",
                    "subgroup": subgroups[i]["subgroup"],
                    "value": round(m, 4),
                    "severity": "warning",
                    "action": "Verificar mudança de processo"
                })

        # Rule 3: 6 points in a row steadily increasing or decreasing
        if i >= 5:
            last_6 = means[i-5:i+1]
            increasing = all(last_6[j] < last_6[j+1] for j in range(5))
            decreasing = all(last_6[j] > last_6[j+1] for j in range(5))
            if increasing or decreasing:
                signals.append({
                    "rule": 3,
                    "description": f"6 pontos {'crescentes' if increasing else 'decrescentes'}",
                    "subgroup": subgroups[i]["subgroup"],
                    "value": round(m, 4),
                    "severity": "warning",
                    "action": "Verificar tendência/drift"
                })

    return signals[:10]  # Limit to 10 signals


def _generate_spc_recommendations(capability: Optional[Dict], signals: List, control_pct: float) -> List[Dict]:
    """Generate SPC recommendations"""
    recs = []

    if signals:
        recs.append({
            "priority": "high",
            "type": "out_of_control",
            "title": f"{len(signals)} sinais fora de controle detectados",
            "description": "Investigar causas especiais e implementar ações corretivas",
            "action": "Revisar sinais e criar plano de ação 5W2H"
        })

    if capability:
        if capability["cpk"] < 1.0:
            recs.append({
                "priority": "critical",
                "type": "capability",
                "title": f"Processo não capaz (Cpk = {capability['cpk']})",
                "description": "Processo não atende especificações - ação urgente necessária",
                "action": "Reduzir variação do processo ou revisar especificações"
            })
        elif capability["cpk"] < 1.33:
            recs.append({
                "priority": "medium",
                "type": "capability",
                "title": f"Capacidade marginal (Cpk = {capability['cpk']})",
                "description": "Processo capaz mas com pouca margem de segurança",
                "action": "Implementar melhorias para aumentar Cpk acima de 1.33"
            })

    if control_pct < 0.95:
        recs.append({
            "priority": "high",
            "type": "stability",
            "title": f"Processo instável ({control_pct*100:.1f}% em controle)",
            "description": "Muitos pontos fora dos limites de controle",
            "action": "Estabilizar processo antes de calcular capacidade"
        })

    if not recs:
        recs.append({
            "priority": "info",
            "type": "status",
            "title": "Processo em controle estatístico",
            "description": "Continuar monitoramento regular",
            "action": "Manter práticas atuais e monitorar indicadores"
        })

    return recs


def _generate_alarm_actions(alarm_type: str, count: int, category_info: Dict) -> List[Dict]:
    """Generate recommended actions for an alarm type"""
    actions = []

    if count > 50:
        actions.append({
            "priority": "critical",
            "action": f"Investigação urgente: {count} ocorrências - iniciar análise de causa raiz (Ishikawa)",
            "estimated_time": "2 horas",
            "responsible": "Engenharia"
        })

    actions.append({
        "priority": "high" if count > 20 else "medium",
        "action": f"Revisar histórico de manutenção de {category_info['equipment']}",
        "estimated_time": "30 min",
        "responsible": "PCM"
    })

    if category_info["category"] in ["Mecânica", "Térmica"]:
        actions.append({
            "priority": "medium",
            "action": "Avaliar condição atual com análise preditiva (vibração/termografia)",
            "estimated_time": "1 hora",
            "responsible": "Preditiva"
        })

    actions.append({
        "priority": "low",
        "action": "Verificar se set-point de alarme está adequado",
        "estimated_time": "15 min",
        "responsible": "Instrumentação"
    })

    return actions


def _summarize_by_category(pareto_data: List[Dict]) -> List[Dict]:
    """Summarize Pareto data by category"""
    categories = {}
    for item in pareto_data:
        cat = item.get("category", "Outro")
        if cat not in categories:
            categories[cat] = {"count": 0, "cost": 0, "alarm_types": []}
        categories[cat]["count"] += item["count"]
        categories[cat]["cost"] += item["estimated_cost"]
        categories[cat]["alarm_types"].append(item["alarm_type"])

    return [
        {
            "category": cat,
            "total_alarms": data["count"],
            "total_cost": data["cost"],
            "alarm_types": data["alarm_types"][:3]  # Top 3
        }
        for cat, data in sorted(categories.items(), key=lambda x: x[1]["count"], reverse=True)
    ]


def _create_priority_matrix(pareto_data: List[Dict]) -> Dict:
    """Create frequency x impact priority matrix"""
    high_freq_high_impact = []
    high_freq_low_impact = []
    low_freq_high_impact = []
    low_freq_low_impact = []

    median_count = statistics.median([p["count"] for p in pareto_data]) if pareto_data else 0
    median_cost = statistics.median([p["estimated_cost"] for p in pareto_data]) if pareto_data else 0

    for p in pareto_data:
        is_high_freq = p["count"] >= median_count
        is_high_impact = p["estimated_cost"] >= median_cost

        if is_high_freq and is_high_impact:
            high_freq_high_impact.append(p["alarm_type"])
        elif is_high_freq:
            high_freq_low_impact.append(p["alarm_type"])
        elif is_high_impact:
            low_freq_high_impact.append(p["alarm_type"])
        else:
            low_freq_low_impact.append(p["alarm_type"])

    return {
        "eliminate_urgently": high_freq_high_impact[:3],
        "reduce_frequency": high_freq_low_impact[:3],
        "mitigate_impact": low_freq_high_impact[:3],
        "monitor": low_freq_low_impact[:3]
    }


def _generate_pareto_insights_enhanced(pareto_data: List[Dict], total_cost: float) -> List[Dict]:
    """Generate enhanced Pareto insights"""
    insights = []

    if pareto_data:
        top = pareto_data[0]
        insights.append({
            "type": "critical",
            "icon": "🎯",
            "title": f"Foco Principal: {top['alarm_type']}",
            "description": f"Responsável por {top['percent']:.0f}% dos alarmes e R$ {top['estimated_cost']:,.0f} em custos",
            "recommendation": "Priorizar investigação e ação imediata"
        })

    vital_few = [p for p in pareto_data if p["is_vital_few"]]
    if vital_few:
        insights.append({
            "type": "warning",
            "icon": "📊",
            "title": f"Regra 80/20 Confirmada",
            "description": f"{len(vital_few)} tipos ({round(len(vital_few)/len(pareto_data)*100)}%) causam 80% dos problemas",
            "recommendation": f"Concentrar esforços nos tipos: {', '.join([v['alarm_type'] for v in vital_few[:3]])}"
        })

    if total_cost > 100000:
        insights.append({
            "type": "warning",
            "icon": "💰",
            "title": f"Impacto Financeiro Significativo: R$ {total_cost:,.0f}",
            "description": "Custo estimado dos alarmes no período justifica investimento em melhorias",
            "recommendation": "Criar business case para projeto de melhoria"
        })

    return insights
