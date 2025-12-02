"""
OEE (Overall Equipment Effectiveness) Dashboard API
====================================================

Endpoints dedicados para análise detalhada de OEE industrial.
Inclui métricas por equipamento, análise de perdas e previsões ML.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import random

from app.db.session import get_db
from app.models.user import User
from app.core.deps import get_current_user
from app.models.alarm import AlarmEvent, AlarmDefinition

router = APIRouter()
logger = logging.getLogger(__name__)


# Equipment definitions for simulation
EQUIPMENT_LIST = [
    {"id": "CORR01", "name": "Correia Transportadora 01", "area": "Recebimento", "type": "conveyor"},
    {"id": "CORR02", "name": "Correia Transportadora 02", "area": "Expedição", "type": "conveyor"},
    {"id": "SILO01", "name": "Silo de Armazenamento 01", "area": "Armazenamento", "type": "silo"},
    {"id": "SILO02", "name": "Silo de Armazenamento 02", "area": "Armazenamento", "type": "silo"},
    {"id": "ELEV01", "name": "Elevador de Grãos 01", "area": "Movimentação", "type": "elevator"},
    {"id": "LOAD01", "name": "Carregador de Navios 01", "area": "Expedição", "type": "shiploader"},
    {"id": "DRYER01", "name": "Secador Industrial 01", "area": "Processamento", "type": "dryer"},
    {"id": "SCALE01", "name": "Balança Rodoviária 01", "area": "Recebimento", "type": "scale"},
]


def _calculate_equipment_oee(equipment_id: str, hours_in_period: float, seed: int = None) -> Dict[str, Any]:
    """
    Calcula métricas OEE para um equipamento específico.
    Em produção, isso viria de dados reais de sensores e alarmes.
    """
    if seed:
        random.seed(seed + hash(equipment_id))

    # Simular dados realistas baseados no tipo de equipamento
    base_availability = random.uniform(0.85, 0.98)
    base_performance = random.uniform(0.80, 0.95)
    base_quality = random.uniform(0.95, 0.995)

    # Calcular horas
    planned_production_time = hours_in_period * 0.9  # 90% é tempo planejado

    # Paradas
    planned_downtime = hours_in_period * random.uniform(0.05, 0.10)  # 5-10% manutenção planejada
    unplanned_downtime = hours_in_period * random.uniform(0.02, 0.08)  # 2-8% paradas não planejadas

    operating_time = planned_production_time - unplanned_downtime

    # Performance
    ideal_cycle_time = 1.0  # segundos por unidade
    actual_cycle_time = ideal_cycle_time * (1 + random.uniform(0.05, 0.20))  # 5-20% mais lento

    total_pieces = int(operating_time * 3600 / actual_cycle_time)  # peças produzidas
    good_pieces = int(total_pieces * base_quality)
    defect_pieces = total_pieces - good_pieces

    # Calcular OEE components
    availability = operating_time / planned_production_time if planned_production_time > 0 else 0
    performance = (ideal_cycle_time / actual_cycle_time) if actual_cycle_time > 0 else 0
    quality = good_pieces / total_pieces if total_pieces > 0 else 0

    oee = availability * performance * quality * 100

    # 6 Grandes Perdas
    losses = {
        "equipment_failure": unplanned_downtime * random.uniform(0.4, 0.6),
        "setup_adjustments": planned_downtime * random.uniform(0.3, 0.5),
        "idling_minor_stops": operating_time * random.uniform(0.02, 0.05),
        "reduced_speed": operating_time * (1 - performance) * random.uniform(0.5, 0.7),
        "process_defects": defect_pieces * ideal_cycle_time / 3600,
        "reduced_yield": operating_time * random.uniform(0.01, 0.03)
    }

    # MTBF e MTTR
    num_failures = random.randint(1, 5)
    mtbf = operating_time / num_failures if num_failures > 0 else operating_time
    mttr = unplanned_downtime / num_failures if num_failures > 0 else 1.0

    return {
        "availability": round(availability * 100, 2),
        "performance": round(performance * 100, 2),
        "quality": round(quality * 100, 2),
        "oee": round(oee, 2),
        "hours": {
            "total_period": round(hours_in_period, 2),
            "planned_production": round(planned_production_time, 2),
            "operating": round(operating_time, 2),
            "planned_downtime": round(planned_downtime, 2),
            "unplanned_downtime": round(unplanned_downtime, 2),
            "idle": round(hours_in_period - planned_production_time - planned_downtime, 2)
        },
        "production": {
            "total_pieces": total_pieces,
            "good_pieces": good_pieces,
            "defect_pieces": defect_pieces,
            "defect_rate": round((defect_pieces / total_pieces * 100) if total_pieces > 0 else 0, 2)
        },
        "losses": {
            "equipment_failure_hours": round(losses["equipment_failure"], 2),
            "setup_adjustments_hours": round(losses["setup_adjustments"], 2),
            "idling_minor_stops_hours": round(losses["idling_minor_stops"], 2),
            "reduced_speed_hours": round(losses["reduced_speed"], 2),
            "process_defects_hours": round(losses["process_defects"], 2),
            "reduced_yield_hours": round(losses["reduced_yield"], 2),
            "total_loss_hours": round(sum(losses.values()), 2)
        },
        "reliability": {
            "mtbf_hours": round(mtbf, 2),
            "mttr_hours": round(mttr, 2),
            "num_failures": num_failures
        }
    }


@router.get("/overview")
async def get_oee_overview(
    time_range: str = Query("24h", description="Time range: 1h, 6h, 24h, 7d, 30d"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Retorna visão geral de OEE da planta.
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
        delta = time_deltas.get(time_range, timedelta(hours=24))
        hours_in_period = delta.total_seconds() / 3600

        # Calcular OEE para todos equipamentos
        equipment_data = []
        total_oee = 0
        total_availability = 0
        total_performance = 0
        total_quality = 0

        seed = int(now.timestamp()) // 3600  # Muda a cada hora para simulação

        for equip in EQUIPMENT_LIST:
            metrics = _calculate_equipment_oee(equip["id"], hours_in_period, seed)
            equipment_data.append({
                **equip,
                **metrics
            })
            total_oee += metrics["oee"]
            total_availability += metrics["availability"]
            total_performance += metrics["performance"]
            total_quality += metrics["quality"]

        n_equip = len(EQUIPMENT_LIST)
        avg_oee = total_oee / n_equip
        avg_availability = total_availability / n_equip
        avg_performance = total_performance / n_equip
        avg_quality = total_quality / n_equip

        # Determinar status
        def get_status(value, thresholds):
            if value >= thresholds[0]:
                return "good"
            elif value >= thresholds[1]:
                return "warning"
            return "critical"

        # Calcular perdas totais
        total_losses = {
            "equipment_failure": sum(e["losses"]["equipment_failure_hours"] for e in equipment_data),
            "setup_adjustments": sum(e["losses"]["setup_adjustments_hours"] for e in equipment_data),
            "idling_minor_stops": sum(e["losses"]["idling_minor_stops_hours"] for e in equipment_data),
            "reduced_speed": sum(e["losses"]["reduced_speed_hours"] for e in equipment_data),
            "process_defects": sum(e["losses"]["process_defects_hours"] for e in equipment_data),
            "reduced_yield": sum(e["losses"]["reduced_yield_hours"] for e in equipment_data),
        }

        # Gerar insights
        insights = []

        # Equipamento com pior OEE
        worst_equip = min(equipment_data, key=lambda x: x["oee"])
        if worst_equip["oee"] < 70:
            insights.append({
                "type": "error",
                "icon": "🔴",
                "title": f"OEE Crítico: {worst_equip['name']}",
                "description": f"OEE de {worst_equip['oee']}% - muito abaixo da meta de 85%",
                "recommendation": "Investigar causas de paradas e perdas de velocidade"
            })

        # Maior fonte de perda
        max_loss = max(total_losses.items(), key=lambda x: x[1])
        loss_names = {
            "equipment_failure": "Falhas de Equipamento",
            "setup_adjustments": "Setup e Ajustes",
            "idling_minor_stops": "Paradas Menores",
            "reduced_speed": "Velocidade Reduzida",
            "process_defects": "Defeitos de Processo",
            "reduced_yield": "Redução de Rendimento"
        }
        insights.append({
            "type": "warning",
            "icon": "⚠️",
            "title": f"Maior Perda: {loss_names[max_loss[0]]}",
            "description": f"{max_loss[1]:.1f} horas perdidas no período",
            "recommendation": "Foco em reduzir esta categoria de perda"
        })

        # Disponibilidade
        if avg_availability < 90:
            insights.append({
                "type": "warning",
                "icon": "⏱️",
                "title": "Disponibilidade Baixa",
                "description": f"Média de {avg_availability:.1f}% - abaixo do ideal de 95%",
                "recommendation": "Revisar plano de manutenção preventiva"
            })

        return {
            "status": "success",
            "generated_at": now.isoformat(),
            "time_range": time_range,
            "hours_in_period": hours_in_period,

            "summary": {
                "oee": {
                    "value": round(avg_oee, 1),
                    "target": 85.0,
                    "status": get_status(avg_oee, [85, 70]),
                    "world_class": 85.0,
                    "gap_to_target": round(85.0 - avg_oee, 1)
                },
                "availability": {
                    "value": round(avg_availability, 1),
                    "target": 95.0,
                    "status": get_status(avg_availability, [95, 85])
                },
                "performance": {
                    "value": round(avg_performance, 1),
                    "target": 90.0,
                    "status": get_status(avg_performance, [90, 80])
                },
                "quality": {
                    "value": round(avg_quality, 1),
                    "target": 99.0,
                    "status": get_status(avg_quality, [99, 95])
                }
            },

            "losses": {
                "equipment_failure_hours": round(total_losses["equipment_failure"], 1),
                "setup_adjustments_hours": round(total_losses["setup_adjustments"], 1),
                "idling_minor_stops_hours": round(total_losses["idling_minor_stops"], 1),
                "reduced_speed_hours": round(total_losses["reduced_speed"], 1),
                "process_defects_hours": round(total_losses["process_defects"], 1),
                "reduced_yield_hours": round(total_losses["reduced_yield"], 1),
                "total_loss_hours": round(sum(total_losses.values()), 1)
            },

            "equipment_count": n_equip,
            "insights": insights
        }

    except Exception as e:
        logger.error(f"Error getting OEE overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/equipment")
async def get_oee_by_equipment(
    time_range: str = Query("24h", description="Time range: 1h, 6h, 24h, 7d, 30d"),
    area: Optional[str] = Query(None, description="Filter by area"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Retorna OEE detalhado por equipamento com horas produzidas, quebrado, etc.
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
        delta = time_deltas.get(time_range, timedelta(hours=24))
        hours_in_period = delta.total_seconds() / 3600

        seed = int(now.timestamp()) // 3600

        equipment_list = EQUIPMENT_LIST
        if area:
            equipment_list = [e for e in EQUIPMENT_LIST if e["area"].lower() == area.lower()]

        equipment_data = []
        for equip in equipment_list:
            metrics = _calculate_equipment_oee(equip["id"], hours_in_period, seed)

            # Adicionar dados detalhados
            equipment_data.append({
                "id": equip["id"],
                "name": equip["name"],
                "area": equip["area"],
                "type": equip["type"],

                # OEE Components
                "oee": metrics["oee"],
                "availability": metrics["availability"],
                "performance": metrics["performance"],
                "quality": metrics["quality"],

                # Status
                "status": "good" if metrics["oee"] >= 85 else "warning" if metrics["oee"] >= 70 else "critical",

                # Horas detalhadas
                "hours_total": metrics["hours"]["total_period"],
                "hours_planned_production": metrics["hours"]["planned_production"],
                "hours_operating": metrics["hours"]["operating"],
                "hours_planned_downtime": metrics["hours"]["planned_downtime"],
                "hours_unplanned_downtime": metrics["hours"]["unplanned_downtime"],
                "hours_idle": metrics["hours"]["idle"],

                # Utilização
                "utilization_percent": round(metrics["hours"]["operating"] / metrics["hours"]["total_period"] * 100, 1) if metrics["hours"]["total_period"] > 0 else 0,

                # Produção
                "total_pieces": metrics["production"]["total_pieces"],
                "good_pieces": metrics["production"]["good_pieces"],
                "defect_pieces": metrics["production"]["defect_pieces"],
                "defect_rate": metrics["production"]["defect_rate"],

                # Confiabilidade
                "mtbf_hours": metrics["reliability"]["mtbf_hours"],
                "mttr_hours": metrics["reliability"]["mttr_hours"],
                "num_failures": metrics["reliability"]["num_failures"],

                # Perdas
                "total_loss_hours": metrics["losses"]["total_loss_hours"],
                "losses_breakdown": metrics["losses"]
            })

        # Ordenar por OEE (pior primeiro para ação)
        equipment_data.sort(key=lambda x: x["oee"])

        # Estatísticas agregadas
        total_operating = sum(e["hours_operating"] for e in equipment_data)
        total_downtime = sum(e["hours_unplanned_downtime"] for e in equipment_data)
        total_pieces = sum(e["total_pieces"] for e in equipment_data)
        total_defects = sum(e["defect_pieces"] for e in equipment_data)

        return {
            "status": "success",
            "generated_at": now.isoformat(),
            "time_range": time_range,
            "hours_in_period": hours_in_period,
            "area_filter": area,

            "aggregated": {
                "total_equipment": len(equipment_data),
                "total_operating_hours": round(total_operating, 1),
                "total_downtime_hours": round(total_downtime, 1),
                "total_production": total_pieces,
                "total_defects": total_defects,
                "overall_defect_rate": round(total_defects / total_pieces * 100, 2) if total_pieces > 0 else 0,
                "equipment_above_target": len([e for e in equipment_data if e["oee"] >= 85]),
                "equipment_critical": len([e for e in equipment_data if e["oee"] < 70])
            },

            "equipment": equipment_data
        }

    except Exception as e:
        logger.error(f"Error getting OEE by equipment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/equipment/{equipment_id}")
async def get_equipment_detail(
    equipment_id: str,
    time_range: str = Query("24h", description="Time range: 1h, 6h, 24h, 7d, 30d"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Retorna detalhes completos de OEE para um equipamento específico.
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
        delta = time_deltas.get(time_range, timedelta(hours=24))
        hours_in_period = delta.total_seconds() / 3600

        # Encontrar equipamento
        equip = next((e for e in EQUIPMENT_LIST if e["id"] == equipment_id), None)
        if not equip:
            raise HTTPException(status_code=404, detail=f"Equipment {equipment_id} not found")

        seed = int(now.timestamp()) // 3600
        metrics = _calculate_equipment_oee(equipment_id, hours_in_period, seed)

        # Gerar histórico (últimas 24 amostras)
        history = []
        for i in range(24):
            hist_seed = seed - i
            hist_metrics = _calculate_equipment_oee(equipment_id, 1, hist_seed)
            history.append({
                "timestamp": (now - timedelta(hours=i)).isoformat(),
                "oee": hist_metrics["oee"],
                "availability": hist_metrics["availability"],
                "performance": hist_metrics["performance"],
                "quality": hist_metrics["quality"]
            })
        history.reverse()

        # Gerar eventos recentes (paradas)
        events = []
        for i in range(metrics["reliability"]["num_failures"]):
            event_time = now - timedelta(hours=random.uniform(0, hours_in_period))
            duration = random.uniform(0.5, metrics["reliability"]["mttr_hours"] * 2)
            events.append({
                "timestamp": event_time.isoformat(),
                "type": random.choice(["falha_mecanica", "falha_eletrica", "falta_material", "ajuste_processo"]),
                "duration_hours": round(duration, 2),
                "resolved": True,
                "description": f"Parada não planejada - {random.choice(['Sensor', 'Motor', 'Correia', 'Válvula'])}"
            })
        events.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "status": "success",
            "generated_at": now.isoformat(),
            "time_range": time_range,

            "equipment": {
                "id": equip["id"],
                "name": equip["name"],
                "area": equip["area"],
                "type": equip["type"]
            },

            "current": {
                "oee": metrics["oee"],
                "availability": metrics["availability"],
                "performance": metrics["performance"],
                "quality": metrics["quality"],
                "status": "good" if metrics["oee"] >= 85 else "warning" if metrics["oee"] >= 70 else "critical"
            },

            "hours": metrics["hours"],
            "production": metrics["production"],
            "losses": metrics["losses"],
            "reliability": metrics["reliability"],

            "history": history,
            "recent_events": events[:10]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting equipment detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/losses")
async def get_oee_losses_analysis(
    time_range: str = Query("24h", description="Time range: 1h, 6h, 24h, 7d, 30d"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Análise detalhada das 6 grandes perdas de OEE.
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
        delta = time_deltas.get(time_range, timedelta(hours=24))
        hours_in_period = delta.total_seconds() / 3600

        seed = int(now.timestamp()) // 3600

        # Calcular perdas por equipamento
        losses_by_equipment = []
        total_losses = {
            "equipment_failure": 0,
            "setup_adjustments": 0,
            "idling_minor_stops": 0,
            "reduced_speed": 0,
            "process_defects": 0,
            "reduced_yield": 0
        }

        for equip in EQUIPMENT_LIST:
            metrics = _calculate_equipment_oee(equip["id"], hours_in_period, seed)
            losses_by_equipment.append({
                "equipment_id": equip["id"],
                "equipment_name": equip["name"],
                "area": equip["area"],
                **metrics["losses"]
            })
            for key in total_losses:
                total_losses[key] += metrics["losses"][f"{key}_hours"]

        # Calcular percentuais
        total_loss_hours = sum(total_losses.values())
        losses_percentage = {
            k: round(v / total_loss_hours * 100, 1) if total_loss_hours > 0 else 0
            for k, v in total_losses.items()
        }

        # Categorias de perda
        loss_categories = [
            {
                "id": "equipment_failure",
                "name": "Falhas de Equipamento",
                "category": "Disponibilidade",
                "hours": round(total_losses["equipment_failure"], 1),
                "percentage": losses_percentage["equipment_failure"],
                "icon": "🔧",
                "description": "Paradas não planejadas por falhas mecânicas ou elétricas"
            },
            {
                "id": "setup_adjustments",
                "name": "Setup e Ajustes",
                "category": "Disponibilidade",
                "hours": round(total_losses["setup_adjustments"], 1),
                "percentage": losses_percentage["setup_adjustments"],
                "icon": "⚙️",
                "description": "Tempo gasto em trocas de produto e ajustes de máquina"
            },
            {
                "id": "idling_minor_stops",
                "name": "Paradas Menores",
                "category": "Performance",
                "hours": round(total_losses["idling_minor_stops"], 1),
                "percentage": losses_percentage["idling_minor_stops"],
                "icon": "⏸️",
                "description": "Pequenas paradas e tempo ocioso"
            },
            {
                "id": "reduced_speed",
                "name": "Velocidade Reduzida",
                "category": "Performance",
                "hours": round(total_losses["reduced_speed"], 1),
                "percentage": losses_percentage["reduced_speed"],
                "icon": "🐢",
                "description": "Operação abaixo da velocidade nominal"
            },
            {
                "id": "process_defects",
                "name": "Defeitos de Processo",
                "category": "Qualidade",
                "hours": round(total_losses["process_defects"], 1),
                "percentage": losses_percentage["process_defects"],
                "icon": "❌",
                "description": "Retrabalho e sucata em produção estável"
            },
            {
                "id": "reduced_yield",
                "name": "Redução de Rendimento",
                "category": "Qualidade",
                "hours": round(total_losses["reduced_yield"], 1),
                "percentage": losses_percentage["reduced_yield"],
                "icon": "📉",
                "description": "Perdas durante startup e transições"
            }
        ]

        # Ordenar por impacto
        loss_categories.sort(key=lambda x: x["hours"], reverse=True)

        # Pareto (80/20)
        cumulative = 0
        pareto_80 = []
        for loss in loss_categories:
            cumulative += loss["percentage"]
            if cumulative <= 80 or len(pareto_80) == 0:
                pareto_80.append(loss["name"])

        return {
            "status": "success",
            "generated_at": now.isoformat(),
            "time_range": time_range,

            "summary": {
                "total_loss_hours": round(total_loss_hours, 1),
                "availability_losses": round(total_losses["equipment_failure"] + total_losses["setup_adjustments"], 1),
                "performance_losses": round(total_losses["idling_minor_stops"] + total_losses["reduced_speed"], 1),
                "quality_losses": round(total_losses["process_defects"] + total_losses["reduced_yield"], 1)
            },

            "pareto_focus": pareto_80,
            "loss_categories": loss_categories,
            "losses_by_equipment": sorted(losses_by_equipment, key=lambda x: x["total_loss_hours"], reverse=True)
        }

    except Exception as e:
        logger.error(f"Error getting OEE losses analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def get_oee_trends(
    period: str = Query("7d", description="Trend period: 7d, 30d, 90d"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Retorna tendências históricas de OEE.
    """
    try:
        now = datetime.utcnow()
        periods = {"7d": 7, "30d": 30, "90d": 90}
        days = periods.get(period, 7)

        trends = []
        for i in range(days):
            day = now - timedelta(days=i)
            seed = int(day.timestamp()) // 86400

            # Calcular média do dia
            daily_oee = 0
            daily_avail = 0
            daily_perf = 0
            daily_qual = 0

            for equip in EQUIPMENT_LIST:
                metrics = _calculate_equipment_oee(equip["id"], 24, seed)
                daily_oee += metrics["oee"]
                daily_avail += metrics["availability"]
                daily_perf += metrics["performance"]
                daily_qual += metrics["quality"]

            n = len(EQUIPMENT_LIST)
            trends.append({
                "date": day.strftime("%Y-%m-%d"),
                "oee": round(daily_oee / n, 1),
                "availability": round(daily_avail / n, 1),
                "performance": round(daily_perf / n, 1),
                "quality": round(daily_qual / n, 1)
            })

        trends.reverse()

        # Calcular tendência
        if len(trends) >= 2:
            first_half = sum(t["oee"] for t in trends[:len(trends)//2]) / (len(trends)//2)
            second_half = sum(t["oee"] for t in trends[len(trends)//2:]) / (len(trends) - len(trends)//2)
            trend_direction = "up" if second_half > first_half else "down" if second_half < first_half else "stable"
            trend_change = round(second_half - first_half, 1)
        else:
            trend_direction = "stable"
            trend_change = 0

        return {
            "status": "success",
            "generated_at": now.isoformat(),
            "period": period,
            "days": days,

            "trend": {
                "direction": trend_direction,
                "change": trend_change,
                "current_avg": round(sum(t["oee"] for t in trends[-7:]) / min(7, len(trends)), 1) if trends else 0
            },

            "history": trends
        }

    except Exception as e:
        logger.error(f"Error getting OEE trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shifts")
async def get_oee_by_shift(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Retorna OEE por turno para comparação.
    """
    try:
        now = datetime.utcnow()
        target_date = datetime.strptime(date, "%Y-%m-%d") if date else now
        seed = int(target_date.timestamp()) // 86400

        shifts = [
            {"name": "Turno A", "start": "06:00", "end": "14:00", "hours": 8},
            {"name": "Turno B", "start": "14:00", "end": "22:00", "hours": 8},
            {"name": "Turno C", "start": "22:00", "end": "06:00", "hours": 8}
        ]

        shift_data = []
        for idx, shift in enumerate(shifts):
            shift_seed = seed + idx * 1000

            shift_oee = 0
            shift_avail = 0
            shift_perf = 0
            shift_qual = 0

            for equip in EQUIPMENT_LIST:
                metrics = _calculate_equipment_oee(equip["id"], shift["hours"], shift_seed + hash(equip["id"]))
                shift_oee += metrics["oee"]
                shift_avail += metrics["availability"]
                shift_perf += metrics["performance"]
                shift_qual += metrics["quality"]

            n = len(EQUIPMENT_LIST)
            shift_data.append({
                "shift": shift["name"],
                "start_time": shift["start"],
                "end_time": shift["end"],
                "oee": round(shift_oee / n, 1),
                "availability": round(shift_avail / n, 1),
                "performance": round(shift_perf / n, 1),
                "quality": round(shift_qual / n, 1),
                "status": "good" if shift_oee / n >= 85 else "warning" if shift_oee / n >= 70 else "critical"
            })

        # Melhor e pior turno
        best_shift = max(shift_data, key=lambda x: x["oee"])
        worst_shift = min(shift_data, key=lambda x: x["oee"])

        return {
            "status": "success",
            "generated_at": now.isoformat(),
            "date": target_date.strftime("%Y-%m-%d"),

            "summary": {
                "best_shift": best_shift["shift"],
                "best_oee": best_shift["oee"],
                "worst_shift": worst_shift["shift"],
                "worst_oee": worst_shift["oee"],
                "gap": round(best_shift["oee"] - worst_shift["oee"], 1)
            },

            "shifts": shift_data
        }

    except Exception as e:
        logger.error(f"Error getting OEE by shift: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
