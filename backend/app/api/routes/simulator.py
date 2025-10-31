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
sys.path.insert(0, 'backend')

from app.services.grain_terminal_simulator import GrainTerminalSimulator
from app.db.session import get_db
from app.models.tag import Tag

router = APIRouter(prefix="/simulator", tags=["simulator"])

# Global simulator instance (in production, use dependency injection)
_simulator_instance: Optional[GrainTerminalSimulator] = None
_tag_mapping: Optional[Dict[str, str]] = None


def get_simulator() -> GrainTerminalSimulator:
    """Get or create simulator instance"""
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = GrainTerminalSimulator()
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
        _simulator_instance = GrainTerminalSimulator()
        return CommandResponse(success=True, message="Sistema resetado com sucesso")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step", response_model=CommandResponse)
async def step_simulation(dt_s: float = 1.0):
    """Manually step the simulation (for testing)"""
    try:
        sim = get_simulator()
        sim.step(dt_s)
        return CommandResponse(success=True, message=f"Simulação avançada {dt_s}s")
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
        
        # Write to InfluxDB
        sim.write_to_influxdb(_tag_mapping)
        
        return CommandResponse(
            success=True, 
            message=f"✅ Simulação avançada {dt_s}s e {len(_tag_mapping)} tags gravados no InfluxDB"
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

        # Build complete status
        status = {
            "system": {
                "time_s": sim.time_s,
                "running": sim.running,
                "warehouse_inventory_t": sim.warehouse_inventory_t,
                "warehouse_level_pct": sim.warehouse_level_pct,
                "total_kWh": sim.total_kWh,
                "total_mass_t": sim.total_mass_t,
                "cost_BRL": sim.cost_BRL,
                "kWh_per_ton": sim.kWh_per_ton
            },
            "gates": [
                {
                    "id": gate.id,
                    "open_pct": gate.open_pct,
                    "open_pct_sp": gate.open_pct_sp,
                    "flow_tph": gate.flow_tph,
                    "plugged": gate.plugged,
                    "failure": gate.failure
                }
                for gate in sim.gates
            ],
            "belts": {
                belt_id: {
                    "running": belt.running,
                    "rpm": belt.rpm,
                    "speed_mps": belt.speed_mps,
                    "flow_tph": belt.flow_tph,
                    "load_pct": belt.load_pct,
                    "current_A": belt.current_A,
                    "power_kW": belt.power_kW,
                    "temp_bearing_C": belt.temp_bearing_C,
                    "temp_belt_C": belt.temp_belt_C,
                    "underspeed_warn": belt.underspeed_warn,
                    "underspeed_alarm": belt.underspeed_alarm,
                    "chute_level_pct": belt.chute_level_pct,
                    "chute_plugged": belt.chute_plugged
                }
                for belt_id, belt in sim.belts.items()
            },
            "elevator": {
                "running": sim.elevator.running,
                "speed_mps": sim.elevator.speed_mps,
                "flow_tph": sim.elevator.flow_tph,
                "current_A": sim.elevator.current_A,
                "power_kW": sim.elevator.power_kW,
                "temp_motor_C": sim.elevator.temp_motor_C,
                "temp_gearbox_C": sim.elevator.temp_gearbox_C,
                "slip": sim.elevator.slip
            },
            "balance": {
                "running": sim.balance.running,
                "weight_kg": sim.balance.weight_kg,
                "target_kg": sim.balance.target_kg,
                "cycle_count": sim.balance.cycle_count,
                "total_mass_t": sim.balance.total_mass_t,
                "avg_flow_tph": sim.balance.avg_flow_tph,
                "cycle_state": sim.balance.cycle_state.value
            },
            "shiploader": {
                "running": sim.shiploader.running,
                "flow_sp_tph": sim.shiploader.flow_sp_tph,
                "flow_pv_tph": sim.shiploader.flow_pv_tph,
                "power_kW": sim.shiploader.power_kW,
                "dust_level": sim.shiploader.dust_level
            },
            "alarms": [
                {
                    "tag": alarm.tag,
                    "active": alarm.active,
                    "latched": alarm.latched,
                    "timestamp": alarm.timestamp,
                    "count": alarm.count
                }
                for alarm in sim.alarms if alarm.active or alarm.latched
            ],
            "trips": [
                {
                    "tag": trip.tag,
                    "active": trip.active,
                    "latched": trip.latched,
                    "timestamp": trip.timestamp,
                    "count": trip.count
                }
                for trip in sim.trips if trip.active or trip.latched
            ],
            "interlocks": {
                "active_count": len([i for i in sim.interlock_manager.rules if i.active]),
                "active_interlocks": [
                    {
                        "id": rule.id,
                        "cause": rule.cause,
                        "type": rule.type.value,
                        "effects": rule.effects,
                        "active": rule.active,
                        "can_reset": rule.reset.value != "MANUAL" or not rule.active
                    }
                    for rule in sim.interlock_manager.rules
                    if rule.active
                ]
            },
            "maintenance": {
                "avg_health_pct": sum(m.health_pct for m in sim.maintenance_manager.maintenance_states.values()) / len(sim.maintenance_manager.maintenance_states) if sim.maintenance_manager.maintenance_states else 100.0,
                "equipment": {
                    equip_id: {
                        "health_pct": maint.health_pct,
                        "vibration_mm_s": maint.vibration_mm_s,
                        "oil_temp_C": maint.oil_temp_C,
                        "hours_running": maint.hours_running,
                        "alarm_count": maint.alarm_count,
                        "trip_count": maint.trip_count
                    }
                    for equip_id, maint in sim.maintenance_manager.maintenance_states.items()
                }
            },
            "energy": {
                "total_power_kW": sum(e.power_kW for e in sim.energy_manager.electrical_states.values()),
                "avg_power_factor": sum(e.power_factor for e in sim.energy_manager.electrical_states.values()) / len(sim.energy_manager.electrical_states) if sim.energy_manager.electrical_states else 1.0,
                "total_kWh": sum(e.kWh_total for e in sim.energy_manager.electrical_states.values()),
                "cost_peak_BRL": sim.energy_manager.cost_peak_BRL,
                "cost_offpeak_BRL": sim.energy_manager.cost_offpeak_BRL,
                "cost_total_BRL": sim.energy_manager.cost_peak_BRL + sim.energy_manager.cost_offpeak_BRL,
                "equipment": {
                    equip_id: {
                        "voltage_V": elec.voltage_ll,
                        "current_A": elec.current_A,
                        "power_kW": elec.power_kW,
                        "reactive_kvar": elec.reactive_kvar,
                        "apparent_kVA": elec.apparent_kVA,
                        "power_factor": elec.power_factor,
                        "kwh": elec.kWh_total
                    }
                    for equip_id, elec in sim.energy_manager.electrical_states.items()
                }
            }
        }

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
