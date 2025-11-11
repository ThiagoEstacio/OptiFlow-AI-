"""
Gateway API Routes
==================

Endpoints para controle e monitoramento do Gateway Service
"""

from fastapi import APIRouter
from typing import Dict, Any

from app.services.gateway_service import get_gateway

router = APIRouter(prefix="/gateway", tags=["gateway"])


@router.get("/status")
async def get_gateway_status() -> Dict[str, Any]:
    """
    Retorna status do Gateway Service
    
    Inclui:
    - Estado (running/stopped)
    - Configuração (poll interval, source name)
    - Estatísticas (tags descobertas, mensagens publicadas, erros)
    - Status do simulador conectado
    """
    gateway = get_gateway()
    return gateway.get_status()


@router.post("/start")
async def start_gateway() -> Dict[str, str]:
    """Inicia o Gateway Service"""
    gateway = get_gateway()
    await gateway.start()
    return {"status": "success", "message": "Gateway started"}


@router.post("/stop")
async def stop_gateway() -> Dict[str, str]:
    """Para o Gateway Service"""
    gateway = get_gateway()
    await gateway.stop()
    return {"status": "success", "message": "Gateway stopped"}
