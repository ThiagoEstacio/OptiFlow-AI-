"""
🚨 Alarm & Events API Endpoints - Completo e Otimizado
========================================================

Endpoints para gerenciamento de alarmes industriais:
- Definições de alarmes (configuração)
- Eventos de alarmes (histórico)
- Alarmes ativos (tempo real)
- Acknowledge de alarmes
- Estatísticas e análises
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.alarm import AlarmDefinition, AlarmEvent, AlarmSeverity, AlarmType, AlarmState
from app.models.tag import Tag
from app.schemas.alarm import (
    AlarmDefinitionCreate,
    AlarmDefinitionUpdate,
    AlarmDefinitionResponse,
    AlarmEventResponse,
    AlarmEventEnrichedResponse  # ✨ New enriched schema
)
from app.services.cache_service import cached
from pydantic import BaseModel

router = APIRouter()


# ========================================
# 📋 SCHEMAS ADICIONAIS
# ========================================

class AlarmAcknowledgeRequest(BaseModel):
    """Request para acknowledge de alarme"""
    comment: Optional[str] = None
    user_id: Optional[UUID] = None


class AlarmStatistics(BaseModel):
    """Estatísticas de alarmes"""
    total: int
    active: int
    acknowledged: int
    cleared: int
    by_severity: dict
    by_type: dict
    average_duration_minutes: Optional[float] = None


class AlarmEventDetail(AlarmEventResponse):
    """Evento de alarme com detalhes"""
    definition_name: Optional[str] = None
    tag_name: Optional[str] = None
    tag_unit: Optional[str] = None


# ========================================
# 🔧 ALARM DEFINITIONS (Configuração)
# ========================================

@router.post("/definitions", response_model=AlarmDefinitionResponse, status_code=status.HTTP_201_CREATED)
async def create_alarm_definition(
    alarm_def_in: AlarmDefinitionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Cria nova definição de alarme
    
    Exemplo:
    ```json
    {
        "tag_id": "uuid-here",
        "name": "Motor 01 - Corrente Alta",
        "description": "Alarme de sobrecorrente",
        "alarm_type": "HIGH_LIMIT",
        "severity": "HIGH",
        "high_limit": 45.0,
        "deadband": 2.0,
        "delay_seconds": 5
    }
    ```
    """
    # Verificar se tag existe
    tag_result = await db.execute(select(Tag).where(Tag.id == alarm_def_in.tag_id))
    tag = tag_result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag {alarm_def_in.tag_id} not found"
        )
    
    # Criar definição
    try:
        alarm_def = AlarmDefinition(
            tag_id=alarm_def_in.tag_id,
            name=alarm_def_in.name,
            description=alarm_def_in.description,
            alarm_type=AlarmType[alarm_def_in.alarm_type.upper()],
            severity=AlarmSeverity[alarm_def_in.severity.upper()],
            high_limit=alarm_def_in.high_limit,
            low_limit=alarm_def_in.low_limit,
            deadband=alarm_def_in.deadband,
            delay_seconds=alarm_def_in.delay_seconds or 0,
            is_active=True,
            notification_recipients=[],  # Initialize with empty list
            settings={}  # Initialize with empty dict
        )
        
        db.add(alarm_def)
        await db.commit()
        await db.refresh(alarm_def)
        
        return alarm_def
    except Exception as e:
        import traceback
        traceback.print_exc()
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating alarm definition: {str(e)}"
        )


@router.get("/definitions", response_model=List[AlarmDefinitionResponse])
async def list_alarm_definitions(
    tag_id: Optional[UUID] = None,
    severity: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todas as definições de alarmes com filtros opcionais
    
    Filtros:
    - tag_id: Filtrar por tag específica
    - severity: CRITICAL, HIGH, MEDIUM, LOW
    - is_active: true/false (alarmes habilitados/desabilitados)
    """
    stmt = select(AlarmDefinition)
    
    # Aplicar filtros
    if tag_id:
        stmt = stmt.where(AlarmDefinition.tag_id == tag_id)
    
    if severity:
        try:
            stmt = stmt.where(AlarmDefinition.severity == AlarmSeverity[severity.upper()])
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity: {severity}. Must be one of: CRITICAL, HIGH, MEDIUM, LOW"
            )
    
    if is_active is not None:
        stmt = stmt.where(AlarmDefinition.is_active == is_active)
    
    stmt = stmt.offset(skip).limit(limit).order_by(AlarmDefinition.created_at.desc())
    
    result = await db.execute(stmt)
    alarm_defs = result.scalars().all()
    
    return alarm_defs


@router.get("/definitions/{alarm_def_id}", response_model=AlarmDefinitionResponse)
async def get_alarm_definition(
    alarm_def_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Obtém definição de alarme por ID"""
    result = await db.execute(
        select(AlarmDefinition).where(AlarmDefinition.id == alarm_def_id)
    )
    alarm_def = result.scalar_one_or_none()
    
    if not alarm_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alarm definition {alarm_def_id} not found"
        )
    
    return alarm_def


@router.put("/definitions/{alarm_def_id}", response_model=AlarmDefinitionResponse)
async def update_alarm_definition(
    alarm_def_id: UUID,
    alarm_def_in: AlarmDefinitionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Atualiza definição de alarme"""
    result = await db.execute(
        select(AlarmDefinition).where(AlarmDefinition.id == alarm_def_id)
    )
    alarm_def = result.scalar_one_or_none()
    
    if not alarm_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alarm definition {alarm_def_id} not found"
        )
    
    # Atualizar apenas campos fornecidos
    update_data = alarm_def_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(alarm_def, field):
            setattr(alarm_def, field, value)
    
    await db.commit()
    await db.refresh(alarm_def)
    
    return alarm_def


@router.delete("/definitions/{alarm_def_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alarm_definition(
    alarm_def_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Deleta definição de alarme"""
    result = await db.execute(
        select(AlarmDefinition).where(AlarmDefinition.id == alarm_def_id)
    )
    alarm_def = result.scalar_one_or_none()
    
    if not alarm_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alarm definition {alarm_def_id} not found"
        )
    
    await db.delete(alarm_def)
    await db.commit()


# ========================================
# 🚨 ALARM EVENTS (Eventos e Histórico)
# ========================================

@router.get("/active")
@cached(ttl=15, key_prefix="alarms_active")
async def list_active_alarms(
    severity: Optional[str] = None,
    tag_id: Optional[UUID] = None,
    limit: int = 500,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    ✨ Lista alarmes ativos com dados enriquecidos (JOIN com AlarmDefinition)

    Retorna alarmes ativos incluindo:
    - severity, alarm_name, alarm_type da definição
    - tag_id associado
    - Todos os campos do AlarmEvent
    - total: contagem total de alarmes ativos

    Endpoint otimizado para dashboard e real-time views
    """
    # Build base filter conditions
    base_conditions = [AlarmEvent.state == AlarmState.ACTIVE]

    if tag_id:
        base_conditions.append(AlarmDefinition.tag_id == tag_id)

    if severity:
        try:
            base_conditions.append(AlarmDefinition.severity == AlarmSeverity[severity.upper()])
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity: {severity}. Must be one of: CRITICAL, HIGH, MEDIUM, LOW"
            )

    # Count total active alarms (without limit)
    count_stmt = select(func.count(AlarmEvent.id)).join(
        AlarmDefinition, AlarmEvent.definition_id == AlarmDefinition.id
    ).where(and_(*base_conditions))

    total_result = await db.execute(count_stmt)
    total_count = total_result.scalar() or 0

    # ✨ SELECT com JOIN para pegar dados da definição
    stmt = select(
        AlarmEvent,
        AlarmDefinition.severity,
        AlarmDefinition.name.label('alarm_name'),
        AlarmDefinition.alarm_type,
        AlarmDefinition.tag_id,
        AlarmDefinition.description,
        AlarmDefinition.high_limit,
        AlarmDefinition.low_limit
    ).join(
        AlarmDefinition, AlarmEvent.definition_id == AlarmDefinition.id
    ).where(and_(*base_conditions))

    stmt = stmt.order_by(AlarmEvent.trigger_timestamp.desc()).offset(offset).limit(limit)

    result = await db.execute(stmt)
    rows = result.all()

    # ✨ Construir resposta enriquecida
    enriched_alarms = []
    for row in rows:
        alarm_event = row[0]
        enriched_alarm = AlarmEventEnrichedResponse(
            # Campos do AlarmEvent
            id=alarm_event.id,
            definition_id=alarm_event.definition_id,
            state=alarm_event.state.value,
            trigger_value=alarm_event.trigger_value,
            trigger_timestamp=alarm_event.trigger_timestamp,
            acknowledged_at=alarm_event.acknowledged_at,
            acknowledged_by=alarm_event.acknowledged_by,
            acknowledgment_comment=alarm_event.acknowledgment_comment,
            cleared_at=alarm_event.cleared_at,
            clear_value=alarm_event.clear_value,
            duration_seconds=alarm_event.duration_seconds,
            created_at=alarm_event.created_at,
            updated_at=alarm_event.updated_at,
            # ✨ Campos enriquecidos da AlarmDefinition
            severity=row[1].value,  # AlarmSeverity enum
            alarm_name=row[2],
            alarm_type=row[3].value,  # AlarmType enum
            tag_id=row[4],
            description=row[5],
            high_limit=row[6],
            low_limit=row[7]
        )
        enriched_alarms.append(enriched_alarm)

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "items": enriched_alarms
    }


@router.get("/history", response_model=List[AlarmEventEnrichedResponse])
async def get_alarm_history(
    start_date: Optional[datetime] = Query(None, description="Data início (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Data fim (ISO format)"),
    state: Optional[str] = None,
    severity: Optional[str] = None,
    tag_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    ✨ Histórico de eventos de alarmes com dados enriquecidos

    Retorna histórico com JOIN para incluir severity, alarm_name, etc.

    Parâmetros:
    - start_date: Data início (default: 30 dias atrás)
    - end_date: Data fim (default: agora)
    - state: ACTIVE, ACKNOWLEDGED, CLEARED
    - severity: CRITICAL, HIGH, MEDIUM, LOW
    - tag_id: ID da tag
    """
    # Default: últimos 30 dias
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    # ✨ SELECT com JOIN para pegar dados da definição
    stmt = select(
        AlarmEvent,
        AlarmDefinition.severity,
        AlarmDefinition.name.label('alarm_name'),
        AlarmDefinition.alarm_type,
        AlarmDefinition.tag_id,
        AlarmDefinition.description,
        AlarmDefinition.high_limit,
        AlarmDefinition.low_limit
    ).join(
        AlarmDefinition, AlarmEvent.definition_id == AlarmDefinition.id
    ).where(
        and_(
            AlarmEvent.trigger_timestamp >= start_date,
            AlarmEvent.trigger_timestamp <= end_date
        )
    )

    # Filtros
    if state:
        try:
            stmt = stmt.where(AlarmEvent.state == AlarmState[state.upper()])
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state: {state}. Must be: ACTIVE, ACKNOWLEDGED, CLEARED"
            )

    if severity:
        try:
            stmt = stmt.where(AlarmDefinition.severity == AlarmSeverity[severity.upper()])
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity: {severity}. Must be: CRITICAL, HIGH, MEDIUM, LOW"
            )

    if tag_id:
        stmt = stmt.where(AlarmDefinition.tag_id == tag_id)

    stmt = stmt.offset(skip).limit(limit).order_by(AlarmEvent.trigger_timestamp.desc())

    result = await db.execute(stmt)
    rows = result.all()

    # ✨ Construir resposta enriquecida
    enriched_alarms = []
    for row in rows:
        alarm_event = row[0]
        enriched_alarm = AlarmEventEnrichedResponse(
            # Campos do AlarmEvent
            id=alarm_event.id,
            definition_id=alarm_event.definition_id,
            state=alarm_event.state.value,
            trigger_value=alarm_event.trigger_value,
            trigger_timestamp=alarm_event.trigger_timestamp,
            acknowledged_at=alarm_event.acknowledged_at,
            acknowledged_by=alarm_event.acknowledged_by,
            acknowledgment_comment=alarm_event.acknowledgment_comment,
            cleared_at=alarm_event.cleared_at,
            clear_value=alarm_event.clear_value,
            duration_seconds=alarm_event.duration_seconds,
            created_at=alarm_event.created_at,
            updated_at=alarm_event.updated_at,
            # ✨ Campos enriquecidos da AlarmDefinition
            severity=row[1].value,  # AlarmSeverity enum
            alarm_name=row[2],
            alarm_type=row[3].value,  # AlarmType enum
            tag_id=row[4],
            description=row[5],
            high_limit=row[6],
            low_limit=row[7]
        )
        enriched_alarms.append(enriched_alarm)

    return enriched_alarms


@router.get("/events/{alarm_id}", response_model=AlarmEventResponse)
async def get_alarm_event(
    alarm_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Obtém evento de alarme específico por ID"""
    result = await db.execute(
        select(AlarmEvent).where(AlarmEvent.id == alarm_id)
    )
    alarm = result.scalar_one_or_none()
    
    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alarm event {alarm_id} not found"
        )
    
    return alarm


@router.post("/events/{alarm_id}/acknowledge", response_model=AlarmEventResponse)
async def acknowledge_alarm(
    alarm_id: UUID,
    ack_request: AlarmAcknowledgeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Acknowledge (reconhecer) um alarme ativo
    
    Exemplo:
    ```json
    {
        "comment": "Verificado - aguardando correção",
        "user_id": "uuid-do-usuario"
    }
    ```
    """
    result = await db.execute(
        select(AlarmEvent).where(AlarmEvent.id == alarm_id)
    )
    alarm = result.scalar_one_or_none()
    
    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alarm event {alarm_id} not found"
        )
    
    if alarm.state != AlarmState.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Alarm is not active (current state: {alarm.state.value})"
        )
    
    # Atualizar estado
    alarm.state = AlarmState.ACKNOWLEDGED
    alarm.acknowledged_at = datetime.utcnow()
    alarm.acknowledged_by = ack_request.user_id
    alarm.acknowledgment_comment = ack_request.comment
    
    await db.commit()
    await db.refresh(alarm)
    
    return alarm


@router.post("/events/{alarm_id}/clear", response_model=AlarmEventResponse)
async def clear_alarm(
    alarm_id: UUID,
    clear_value: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Clear (limpar) um alarme - indica que condição voltou ao normal
    """
    result = await db.execute(
        select(AlarmEvent).where(AlarmEvent.id == alarm_id)
    )
    alarm = result.scalar_one_or_none()
    
    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alarm event {alarm_id} not found"
        )
    
    if alarm.state == AlarmState.CLEARED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alarm already cleared"
        )
    
    # Atualizar estado
    alarm.state = AlarmState.CLEARED
    alarm.cleared_at = datetime.utcnow()
    alarm.clear_value = clear_value
    
    # Calcular duração
    if alarm.trigger_timestamp:
        duration = (alarm.cleared_at - alarm.trigger_timestamp).total_seconds()
        alarm.duration_seconds = duration
    
    await db.commit()
    await db.refresh(alarm)
    
    return alarm


# ========================================
# 📊 STATISTICS & ANALYTICS
# ========================================

@router.get("/statistics", response_model=AlarmStatistics)
async def get_alarm_statistics(
    start_date: Optional[datetime] = Query(None, description="Data início"),
    end_date: Optional[datetime] = Query(None, description="Data fim"),
    db: AsyncSession = Depends(get_db)
):
    """
    Estatísticas de alarmes
    
    Retorna:
    - Total de alarmes
    - Contadores por estado (active, acknowledged, cleared)
    - Distribuição por severidade
    - Distribuição por tipo
    - Duração média dos alarmes
    """
    # Default: últimos 30 dias
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Total de alarmes
    total_result = await db.execute(
        select(func.count(AlarmEvent.id)).where(
            and_(
                AlarmEvent.trigger_timestamp >= start_date,
                AlarmEvent.trigger_timestamp <= end_date
            )
        )
    )
    total = total_result.scalar() or 0
    
    # Por estado
    state_result = await db.execute(
        select(AlarmEvent.state, func.count(AlarmEvent.id))
        .where(
            and_(
                AlarmEvent.trigger_timestamp >= start_date,
                AlarmEvent.trigger_timestamp <= end_date
            )
        )
        .group_by(AlarmEvent.state)
    )
    states = {state.value: count for state, count in state_result.all()}
    
    # Por severidade (join com definition)
    severity_result = await db.execute(
        select(AlarmDefinition.severity, func.count(AlarmEvent.id))
        .join(AlarmEvent, AlarmDefinition.id == AlarmEvent.definition_id)
        .where(
            and_(
                AlarmEvent.trigger_timestamp >= start_date,
                AlarmEvent.trigger_timestamp <= end_date
            )
        )
        .group_by(AlarmDefinition.severity)
    )
    by_severity = {sev.value: count for sev, count in severity_result.all()}
    
    # Por tipo
    type_result = await db.execute(
        select(AlarmDefinition.alarm_type, func.count(AlarmEvent.id))
        .join(AlarmEvent, AlarmDefinition.id == AlarmEvent.definition_id)
        .where(
            and_(
                AlarmEvent.trigger_timestamp >= start_date,
                AlarmEvent.trigger_timestamp <= end_date
            )
        )
        .group_by(AlarmDefinition.alarm_type)
    )
    by_type = {typ.value: count for typ, count in type_result.all()}
    
    # Duração média (apenas alarmes cleared)
    duration_result = await db.execute(
        select(func.avg(AlarmEvent.duration_seconds))
        .where(
            and_(
                AlarmEvent.trigger_timestamp >= start_date,
                AlarmEvent.trigger_timestamp <= end_date,
                AlarmEvent.duration_seconds.isnot(None)
            )
        )
    )
    avg_duration_seconds = duration_result.scalar()
    avg_duration_minutes = avg_duration_seconds / 60 if avg_duration_seconds else None
    
    return AlarmStatistics(
        total=total,
        active=states.get('active', 0),
        acknowledged=states.get('acknowledged', 0),
        cleared=states.get('cleared', 0),
        by_severity=by_severity,
        by_type=by_type,
        average_duration_minutes=avg_duration_minutes
    )


@router.get("/top-alarms")
async def get_top_alarms(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Top alarmes mais frequentes (por definição)
    
    Retorna lista ordenada por frequência de ocorrência
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    result = await db.execute(
        select(
            AlarmDefinition.id,
            AlarmDefinition.name,
            AlarmDefinition.severity,
            func.count(AlarmEvent.id).label('count')
        )
        .join(AlarmEvent, AlarmDefinition.id == AlarmEvent.definition_id)
        .where(
            and_(
                AlarmEvent.trigger_timestamp >= start_date,
                AlarmEvent.trigger_timestamp <= end_date
            )
        )
        .group_by(AlarmDefinition.id, AlarmDefinition.name, AlarmDefinition.severity)
        .order_by(desc('count'))
        .limit(limit)
    )
    
    top_alarms = [
        {
            "alarm_definition_id": str(alarm_id),
            "name": name,
            "severity": severity.value,
            "count": count
        }
        for alarm_id, name, severity, count in result.all()
    ]
    
    return {"top_alarms": top_alarms, "period_days": (end_date - start_date).days}
