"""
Simulator Control API Endpoints
================================

REST API for controlling and monitoring the grain terminal simulator
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import sys
import numpy as np
sys.path.insert(0, 'backend')

from app.services.lightweight_simulator import LightweightGrainTerminalSimulator
from app.db.session import get_db
from app.models.tag import Tag

router = APIRouter(prefix="/simulator", tags=["simulator"])

# Global simulator instance (in production, use dependency injection)
_simulator_instance: Optional[LightweightGrainTerminalSimulator] = None
_tag_mapping: Optional[Dict[str, str]] = None


def get_simulator() -> LightweightGrainTerminalSimulator:
    """Get or create simulator instance"""
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = LightweightGrainTerminalSimulator()
    return _simulator_instance


# Request/Response Models
class SetpointRequest(BaseModel):
    value: float = Field(..., description="Setpoint value")


class CommandResponse(BaseModel):
    success: bool
    message: str


class EquipmentStatus(BaseModel):
    running: bool
    flow_tph: Optional[float] = None
    load_pct: Optional[float] = None
    temp_C: Optional[float] = None


class SystemStatus(BaseModel):
    time_s: float
    running: bool
    warehouse_inventory_t: float
    warehouse_level_pct: float
    total_kWh: float
    total_mass_t: float
    cost_BRL: float


class AlarmInfo(BaseModel):
    tag: str
    active: bool
    latched: bool
    timestamp: float
    count: int


# ============================================================================
# SYSTEM CONTROL
# ============================================================================

@router.post("/start", response_model=CommandResponse)
async def start_system():
    """Start the simulator system"""
    try:
        sim = get_simulator()
        sim.start()
        return CommandResponse(success=True, message="Sistema iniciado com sucesso")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop", response_model=CommandResponse)
async def stop_system():
    """Stop the simulator system"""
    try:
        sim = get_simulator()
        sim.stop()
        return CommandResponse(success=True, message="Sistema parado com sucesso")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset", response_model=CommandResponse)
async def reset_system():
    """Reset the simulator to initial state"""
    try:
        global _simulator_instance
        _simulator_instance = LightweightGrainTerminalSimulator()
        return CommandResponse(success=True, message="Sistema resetado com sucesso")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step", response_model=CommandResponse)
async def step_simulation(dt_s: float = 1.0):
    """
    Manually step the simulation (for testing)

    Now publishes data to Kafka automatically (event-driven architecture)
    """
    try:
        sim = get_simulator()
        await sim.step_async(dt_s)
        return CommandResponse(success=True, message=f"Simulação avançada {dt_s}s → Kafka")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step-and-record", response_model=CommandResponse)
async def step_and_record(dt_s: float = 1.0, db: AsyncSession = Depends(get_db)):
    """
    Step simulation and record values to InfluxDB
    
    This endpoint:
    1. Executes one simulation step
    2. Retrieves tag mapping from database
    3. Writes all values to InfluxDB for real-time persistence
    """
    try:
        global _tag_mapping
        sim = get_simulator()
        
        # Load tag mapping from database (cache it)
        if _tag_mapping is None:
            stmt = select(Tag).where(Tag.is_active == True)
            result = await db.execute(stmt)
            tags = result.scalars().all()
            
            _tag_mapping = {tag.name: str(tag.id) for tag in tags}
            
        # Execute simulation step
        sim.step(dt_s)

        # TODO: Implement write_to_influxdb() for lightweight simulator
        # sim.write_to_influxdb(_tag_mapping)

        return CommandResponse(
            success=True,
            message=f"✅ Simulação avançada {dt_s}s (InfluxDB write disabled for lightweight simulator)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")


# ============================================================================
# STATUS MONITORING
# ============================================================================

@router.get("/status", response_model=Dict)
async def get_system_status():
    """Get complete system status"""
    try:
        sim = get_simulator()

        # Use the simulator's built-in get_status() method
        status = sim.get_status()

        # Add empty alarms and trips for API compatibility
        status["alarms"] = []
        status["trips"] = []

        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GATE CONTROL
# ============================================================================

@router.post("/gates/{gate_id}/setpoint", response_model=CommandResponse)
async def set_gate_setpoint(gate_id: int, request: SetpointRequest):
    """Set gate opening setpoint (0-100%)"""
    try:
        if not 1 <= gate_id <= 10:
            raise HTTPException(status_code=400, detail="Gate ID deve ser entre 1 e 10")

        if not 0 <= request.value <= 100:
            raise HTTPException(status_code=400, detail="Setpoint deve ser entre 0 e 100%")

        sim = get_simulator()
        sim.set_gate_manual(gate_id, request.value)

        return CommandResponse(
            success=True,
            message=f"Comporta {gate_id} setpoint ajustado para {request.value:.1f}%"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gates/all/setpoint", response_model=CommandResponse)
async def set_all_gates_setpoint(request: SetpointRequest):
    """Set all gates to same opening setpoint"""
    try:
        if not 0 <= request.value <= 100:
            raise HTTPException(status_code=400, detail="Setpoint deve ser entre 0 e 100%")

        sim = get_simulator()
        for gate in sim.gates:
            sim.set_gate_manual(gate.id, request.value)

        return CommandResponse(
            success=True,
            message=f"Todas as comportas ajustadas para {request.value:.1f}%"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SHIPLOADER CONTROL
# ============================================================================

@router.post("/shiploader/setpoint", response_model=CommandResponse)
async def set_shiploader_setpoint(request: SetpointRequest):
    """Set shiploader flow setpoint (t/h)"""
    try:
        if not 0 <= request.value <= 1500:
            raise HTTPException(status_code=400, detail="Setpoint deve ser entre 0 e 1500 t/h")

        sim = get_simulator()
        sim.set_shiploader_setpoint(request.value)

        return CommandResponse(
            success=True,
            message=f"Shiploader setpoint ajustado para {request.value:.0f} t/h"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ALARMS
# ============================================================================

@router.get("/alarms", response_model=List[AlarmInfo])
async def get_alarms(active_only: bool = False):
    """Get list of alarms"""
    try:
        sim = get_simulator()
        alarms = sim.alarms

        if active_only:
            alarms = [a for a in alarms if a.active]

        return [
            AlarmInfo(
                tag=alarm.tag,
                active=alarm.active,
                latched=alarm.latched,
                timestamp=alarm.timestamp,
                count=alarm.count
            )
            for alarm in alarms
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trips", response_model=List[AlarmInfo])
async def get_trips(active_only: bool = False):
    """Get list of trips"""
    try:
        sim = get_simulator()
        trips = sim.trips

        if active_only:
            trips = [t for t in trips if t.active]

        return [
            AlarmInfo(
                tag=trip.tag,
                active=trip.active,
                latched=trip.latched,
                timestamp=trip.timestamp,
                count=trip.count
            )
            for trip in trips
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alarms/acknowledge-all", response_model=CommandResponse)
async def acknowledge_all_alarms():
    """Acknowledge all alarms"""
    try:
        sim = get_simulator()

        count = 0
        for alarm in sim.alarms:
            if alarm.latched:
                alarm.latched = False
                count += 1

        for trip in sim.trips:
            if trip.latched:
                trip.latched = False
                count += 1

        return CommandResponse(
            success=True,
            message=f"{count} alarmes reconhecidos"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
