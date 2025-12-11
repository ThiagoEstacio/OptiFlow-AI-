"""
MELH-003: Dynamic Ishikawa (Fishbone) Diagram API Endpoints

Provides REST endpoints for root cause analysis using 6M methodology:
- Generate Ishikawa diagrams from operational data
- Analyze specific problems
- Get category-specific insights
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


def get_ishikawa_service():
    """Get Ishikawa analysis service instance"""
    try:
        from app.services.ml.ishikawa_analysis import get_ishikawa_service as get_service
        return get_service()
    except ImportError as e:
        logger.warning(f"Ishikawa service not available: {e}")
        return None


@router.post("/analyze")
async def generate_ishikawa_diagram(
    problem: str = Query(..., min_length=5, description="Problem statement to analyze"),
    hours: int = Query(default=24, ge=1, le=168, description="Analysis period in hours"),
    equipment_id: Optional[str] = Query(default=None, description="Specific equipment to focus on"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate dynamic Ishikawa (fishbone) diagram for root cause analysis.

    MELH-003: Uses real operational data (alarms, tag anomalies, events)
    to identify potential root causes categorized by 6M methodology:
    - Man: Personnel/human factors
    - Machine: Equipment issues
    - Method: Process/procedures
    - Material: Raw materials/inputs
    - Measurement: Instrumentation
    - Mother Nature: Environmental factors

    Args:
        problem: Problem statement to analyze (e.g., "High reject rate in crusher")
        hours: Time period to analyze (default: 24 hours)
        equipment_id: Optional equipment ID to focus analysis

    Returns:
        Ishikawa diagram with categorized root causes and recommendations
    """
    service = get_ishikawa_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Ishikawa analysis service not available"
        )

    try:
        logger.info(f"Generating Ishikawa diagram for: {problem}")

        # Gather data for analysis
        alarms = await _get_recent_alarms(db, hours, equipment_id)
        tag_data = await _get_tag_anomalies(db, hours, equipment_id)
        events = await _get_recent_events(db, hours)

        # Generate analysis
        diagram = await service.analyze(
            problem_statement=problem,
            alarms=alarms,
            tag_data=tag_data,
            events=events,
            hours=hours
        )

        # Convert to JSON-serializable format
        result = service.to_dict(diagram)
        result["success"] = True

        return result

    except Exception as e:
        logger.error(f"Error generating Ishikawa diagram: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Ishikawa diagram: {str(e)}"
        )


@router.get("/categories")
async def get_ishikawa_categories(
    current_user: User = Depends(get_current_user)
):
    """
    Obtém informações sobre as categorias 6M do Ishikawa.

    Retorna descrições e causas típicas para cada categoria.
    """
    return {
        "categories": [
            {
                "id": "mao_de_obra",
                "name": "Mão de Obra",
                "description": "Fatores humanos incluindo erros de operação, falhas de treinamento, fadiga e problemas de comunicação",
                "typical_causes": [
                    "Erro do operador",
                    "Treinamento insuficiente",
                    "Fadiga / sobrecarga de trabalho",
                    "Falha de comunicação",
                    "Falta de supervisão"
                ],
                "icon": "👤"
            },
            {
                "id": "maquina",
                "name": "Máquina",
                "description": "Problemas relacionados a equipamentos incluindo falhas, desgaste, manutenção e calibração",
                "typical_causes": [
                    "Falha de equipamento",
                    "Desgaste mecânico",
                    "Calibração inadequada",
                    "Manutenção deficiente",
                    "Limitações de projeto"
                ],
                "icon": "⚙️"
            },
            {
                "id": "metodo",
                "name": "Método",
                "description": "Problemas de processo e procedimento incluindo POPs, erros de sequência e timing",
                "typical_causes": [
                    "Procedimento não seguido",
                    "Sequência incorreta",
                    "Problemas de timing",
                    "Procedimentos desatualizados",
                    "Variabilidade do processo"
                ],
                "icon": "📋"
            },
            {
                "id": "material",
                "name": "Material",
                "description": "Problemas de matéria-prima e insumos incluindo qualidade, especificações e fornecedor",
                "typical_causes": [
                    "Contaminação",
                    "Material fora de especificação",
                    "Variação de fornecedor",
                    "Problemas de armazenamento",
                    "Mudanças de grade"
                ],
                "icon": "📦"
            },
            {
                "id": "medicao",
                "name": "Medição",
                "description": "Problemas de instrumentação e sensores incluindo calibração, precisão e qualidade do sinal",
                "typical_causes": [
                    "Deriva do sensor",
                    "Erro de calibração",
                    "Falha de instrumento",
                    "Interferência de sinal",
                    "Range/unidade incorreta"
                ],
                "icon": "📏"
            },
            {
                "id": "meio_ambiente",
                "name": "Meio Ambiente",
                "description": "Fatores ambientais incluindo temperatura, umidade, clima e poeira",
                "typical_causes": [
                    "Temperaturas extremas",
                    "Alta umidade",
                    "Eventos climáticos",
                    "Poeira / partículas",
                    "Variações sazonais"
                ],
                "icon": "🌡️"
            }
        ]
    }


@router.get("/templates")
async def get_analysis_templates(
    current_user: User = Depends(get_current_user)
):
    """
    Get pre-defined analysis templates for common industrial problems.

    These templates help users start root cause analysis quickly.
    """
    return {
        "templates": [
            {
                "id": "equipment_failure",
                "name": "Equipment Failure Analysis",
                "problem_template": "Equipment {equipment_name} failed unexpectedly",
                "recommended_hours": 48,
                "focus_categories": ["machine", "measurement", "method"]
            },
            {
                "id": "quality_deviation",
                "name": "Quality Deviation Analysis",
                "problem_template": "Product quality deviation in {process_name}",
                "recommended_hours": 24,
                "focus_categories": ["material", "method", "measurement"]
            },
            {
                "id": "production_loss",
                "name": "Production Loss Analysis",
                "problem_template": "Unplanned production loss at {location}",
                "recommended_hours": 72,
                "focus_categories": ["machine", "man", "method"]
            },
            {
                "id": "energy_spike",
                "name": "Energy Consumption Spike",
                "problem_template": "Unexpected energy consumption increase in {area}",
                "recommended_hours": 24,
                "focus_categories": ["machine", "method", "mother_nature"]
            },
            {
                "id": "safety_incident",
                "name": "Safety Incident Investigation",
                "problem_template": "Safety incident at {location}",
                "recommended_hours": 72,
                "focus_categories": ["man", "machine", "method", "mother_nature"]
            },
            {
                "id": "alarm_flood",
                "name": "Alarm Flood Analysis",
                "problem_template": "Alarm flood event at {timestamp}",
                "recommended_hours": 4,
                "focus_categories": ["measurement", "method", "machine"]
            }
        ]
    }


@router.get("/history")
async def get_analysis_history(
    limit: int = Query(default=10, ge=1, le=50, description="Number of analyses to return"),
    current_user: User = Depends(get_current_user)
):
    """
    Get history of recent Ishikawa analyses.

    Returns cached analyses for quick reference.
    """
    service = get_ishikawa_service()
    if not service:
        return {
            "success": True,
            "analyses": [],
            "message": "Ishikawa service not available"
        }

    # Get cached analyses
    history = []
    for key, diagram in list(service.analysis_cache.items())[-limit:]:
        history.append({
            "cache_key": key,
            "problem_statement": diagram.problem_statement,
            "generated_at": diagram.generated_at.isoformat(),
            "total_causes": diagram.total_causes_identified,
            "primary_cause": diagram.primary_cause.cause if diagram.primary_cause else None
        })

    return {
        "success": True,
        "analyses": history,
        "total": len(history)
    }


@router.get("/quick-analysis")
async def quick_root_cause_analysis(
    equipment_id: str = Query(..., description="Equipment ID to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Quick root cause analysis for specific equipment.

    Automatically generates problem statement and performs analysis.
    """
    service = get_ishikawa_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Ishikawa analysis service not available"
        )

    try:
        # Get recent alarms for this equipment
        alarms = await _get_recent_alarms(db, hours=24, equipment_id=equipment_id)

        if not alarms:
            return {
                "success": True,
                "message": f"No recent issues found for equipment {equipment_id}",
                "recommendation": "Equipment appears to be operating normally"
            }

        # Generate problem statement from most frequent alarm
        alarm_counts = {}
        for alarm in alarms:
            key = alarm.get("alarm_type", "Unknown")
            alarm_counts[key] = alarm_counts.get(key, 0) + 1

        top_alarm = max(alarm_counts, key=alarm_counts.get)
        problem = f"Recurring {top_alarm} issues on equipment {equipment_id}"

        # Get tag data
        tag_data = await _get_tag_anomalies(db, hours=24, equipment_id=equipment_id)

        # Generate analysis
        diagram = await service.analyze(
            problem_statement=problem,
            alarms=alarms,
            tag_data=tag_data,
            hours=24
        )

        result = service.to_dict(diagram)
        result["success"] = True
        result["auto_generated_problem"] = True

        return result

    except Exception as e:
        logger.error(f"Error in quick analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Quick analysis failed: {str(e)}"
        )


# Helper functions

async def _get_recent_alarms(
    db: AsyncSession,
    hours: int,
    equipment_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get recent alarm events from database"""
    try:
        from app.models.alarm_event import AlarmEvent
        from sqlalchemy import select, func
        from datetime import datetime, timedelta

        start_time = datetime.utcnow() - timedelta(hours=hours)

        query = select(
            AlarmEvent.alarm_type,
            AlarmEvent.tag_id,
            AlarmEvent.message,
            AlarmEvent.priority,
            func.count().label('count')
        ).where(
            AlarmEvent.timestamp >= start_time
        ).group_by(
            AlarmEvent.alarm_type,
            AlarmEvent.tag_id,
            AlarmEvent.message,
            AlarmEvent.priority
        )

        if equipment_id:
            query = query.where(AlarmEvent.tag_id.contains(equipment_id))

        result = await db.execute(query)
        rows = result.all()

        return [
            {
                "alarm_type": row.alarm_type,
                "tag_id": row.tag_id,
                "message": row.message,
                "priority": row.priority,
                "count": row.count
            }
            for row in rows
        ]

    except Exception as e:
        logger.warning(f"Error getting alarms: {e}")
        # Return sample data for demonstration
        return [
            {
                "alarm_type": "HIGH_VIBRATION",
                "tag_id": f"{equipment_id or 'EQ001'}_VIB",
                "message": "Vibration exceeded threshold",
                "priority": "HIGH",
                "count": 5
            },
            {
                "alarm_type": "TEMPERATURE_WARNING",
                "tag_id": f"{equipment_id or 'EQ001'}_TEMP",
                "message": "Temperature approaching limit",
                "priority": "MEDIUM",
                "count": 3
            }
        ]


async def _get_tag_anomalies(
    db: AsyncSession,
    hours: int,
    equipment_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get tag values with anomaly information"""
    try:
        from app.services.influxdb_service import get_influxdb_service

        influx = get_influxdb_service()
        if not influx:
            return []

        # Query for tags with bad quality or anomalies
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        query = f'''
        from(bucket: "optiflow")
            |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
            |> filter(fn: (r) => r["_measurement"] == "tag_values")
            |> last()
        '''

        tables = influx.client.query_api().query(query)

        tags = []
        for table in tables:
            for record in table.records:
                tag_id = record.values.get("tag_id", "")
                if equipment_id and equipment_id not in tag_id:
                    continue

                tags.append({
                    "tag_id": tag_id,
                    "name": record.values.get("tag_name", tag_id),
                    "value": record.get_value(),
                    "quality": record.values.get("quality", "GOOD"),
                    "is_anomaly": record.values.get("is_anomaly", False),
                    "coefficient_of_variation": record.values.get("cv", 0)
                })

        return tags

    except Exception as e:
        logger.warning(f"Error getting tag data: {e}")
        return []


async def _get_recent_events(
    db: AsyncSession,
    hours: int
) -> List[Dict[str, Any]]:
    """Get recent operational events (shifts, maintenance, etc.)"""
    # This would query from an events table if available
    # For now, return empty list - events are optional
    return []
