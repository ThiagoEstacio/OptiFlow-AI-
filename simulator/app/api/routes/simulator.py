"""
Simulator Control API
=====================

REST API para controlar o simulador de terminal graneleiro.

**Endpoints**:
- POST /start - Inicia simulação
- POST /stop - Para simulação
- POST /reset - Reset simulador
- GET /status - Status completo
- POST /gates/{gate_id}/setpoint - Define setpoint de gate
- POST /gates/all/setpoint - Define setpoint de todas gates
- POST /step - Avança 1 step manual (quando parado)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional

from app.services.grain_terminal_simulator import get_simulator

router = APIRouter(prefix="/simulator", tags=["simulator"])


# === REQUEST/RESPONSE MODELS ===

class CommandResponse(BaseModel):
    success: bool
    message: str


class SetpointRequest(BaseModel):
    value: float = Field(..., ge=0.0, le=100.0, description="Setpoint percentage (0-100%)")


class StepRequest(BaseModel):
    dt_s: float = Field(1.0, gt=0.0, le=10.0, description="Time step in seconds")


# === SYSTEM CONTROL ===

@router.post("/start", response_model=CommandResponse)
async def start_system():
    """
    Inicia a simulação

    **Comportamento**:
    - Liga todas as correias
    - Define setpoint inicial do shiploader (1500 t/h)
    - Inicia loop automático (1 step/segundo)
    - Tags OPC-UA começam a variar

    **Exemplo**:
    ```bash
    curl -X POST http://localhost:4850/simulator/start
    ```
    """
    try:
        sim = get_simulator()
        sim.start()
        return CommandResponse(
            success=True,
            message="Simulação iniciada com sucesso. Tags OPC-UA sendo atualizadas a cada 1s."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop", response_model=CommandResponse)
async def stop_system():
    """
    Para a simulação

    **Comportamento**:
    - Para loop automático
    - Desliga correias
    - Zera setpoints
    - Tags OPC-UA param de variar

    **Exemplo**:
    ```bash
    curl -X POST http://localhost:4850/simulator/stop
    ```
    """
    try:
        sim = get_simulator()
        sim.stop()
        return CommandResponse(
            success=True,
            message="Simulação parada com sucesso"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset", response_model=CommandResponse)
async def reset_system():
    """
    Reset completo da simulação

    **Comportamento**:
    - Para simulação se estiver rodando
    - Zera tempo, acumuladores, energia
    - Reset warehouse level para 75%
    - Re-agenda falhas programadas

    **Exemplo**:
    ```bash
    curl -X POST http://localhost:4850/simulator/reset
    ```
    """
    try:
        sim = get_simulator()
        sim.reset()
        return CommandResponse(
            success=True,
            message="Simulador resetado com sucesso"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step", response_model=CommandResponse)
async def step_simulation(request: StepRequest):
    """
    Avança simulação manualmente (step único)

    **Uso**:
    - Útil quando simulação está parada
    - Permite controle fino para testes
    - Não afeta loop automático se estiver rodando

    **Exemplo**:
    ```bash
    # Avança 1 segundo
    curl -X POST http://localhost:4850/simulator/step \
      -H "Content-Type: application/json" \
      -d '{"dt_s": 1.0}'
    ```
    """
    try:
        sim = get_simulator()
        sim.step(request.dt_s)
        return CommandResponse(
            success=True,
            message=f"Simulação avançada {request.dt_s}s (tempo total: {sim.time_s:.1f}s)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === STATUS ===

@router.get("/status")
async def get_status():
    """
    Retorna status completo da simulação

    **Retorna**:
    - system: Status geral (running, tempo, energia, massa)
    - gates: Status de cada comporta (abertura, vazão, falhas)
    - belts: Status de cada correia (velocidade, carga, temperatura, falhas)
    - shiploader: Status do carregador (vazão, potência)

    **Exemplo**:
    ```bash
    curl http://localhost:4850/simulator/status
    ```

    **Response**:
    ```json
    {
      "system": {
        "running": true,
        "time_s": 123.4,
        "total_mass_t": 45.2,
        "total_kWh": 12.5,
        "warehouse_level_pct": 72.1,
        "kWh_per_ton": 0.276,
        "cost_BRL": 8.13
      },
      "gates": [...],
      "belts": [...],
      "shiploader": {...}
    }
    ```
    """
    try:
        sim = get_simulator()
        return sim.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === GATE CONTROL ===

@router.post("/gates/{gate_id}/setpoint", response_model=CommandResponse)
async def set_gate_setpoint(gate_id: int, request: SetpointRequest):
    """
    Define setpoint de uma comporta específica

    **Path Parameters**:
    - gate_id: ID da comporta (0-6)

    **Body**:
    - value: Abertura desejada (0-100%)

    **Exemplo**:
    ```bash
    # Abre gate 0 em 50%
    curl -X POST http://localhost:4850/simulator/gates/0/setpoint \
      -H "Content-Type: application/json" \
      -d '{"value": 50.0}'
    ```
    """
    try:
        sim = get_simulator()

        if gate_id < 0 or gate_id >= len(sim.gates):
            raise HTTPException(
                status_code=400,
                detail=f"Gate ID inválido. Use 0-{len(sim.gates)-1}"
            )

        sim.set_gate_setpoint(gate_id, request.value)

        return CommandResponse(
            success=True,
            message=f"Gate {gate_id} setpoint definido para {request.value}%"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gates/all/setpoint", response_model=CommandResponse)
async def set_all_gates_setpoint(request: SetpointRequest):
    """
    Define setpoint de TODAS as comportas

    **Body**:
    - value: Abertura desejada (0-100%)

    **Exemplo**:
    ```bash
    # Abre todas gates em 60%
    curl -X POST http://localhost:4850/simulator/gates/all/setpoint \
      -H "Content-Type: application/json" \
      -d '{"value": 60.0}'
    ```
    """
    try:
        sim = get_simulator()
        sim.set_all_gates_setpoint(request.value)

        return CommandResponse(
            success=True,
            message=f"Todas as {len(sim.gates)} gates definidas para {request.value}%"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === OPC-UA TAGS ===

@router.get("/tags")
async def get_all_tags():
    """
    Retorna todas as tags disponíveis no PLC virtual

    **Uso**:
    - Lista todas as tags disponíveis para o Gateway ler via OPC-UA
    - Útil para debug e descoberta
    - Mostra valores atuais instantâneos

    **Exemplo**:
    ```bash
    curl http://localhost:4850/simulator/tags
    ```

    **Response**:
    ```json
    {
      "SYSTEM_RUNNING_PV": 1.0,
      "CORR01_TEMP_C_PV": 45.2,
      "ARZ_GATES_GATE01_POSICAO_PV": 50.0,
      ...
    }
    ```
    """
    try:
        sim = get_simulator()
        tags = sim.get_all_tags()

        return {
            "count": len(tags),
            "tags": tags
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
