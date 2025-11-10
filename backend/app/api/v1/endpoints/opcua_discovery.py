"""
OPC-UA Discovery API Endpoints
================================

Endpoints para auto-discovery de tags OPC-UA.

Features:
- Trigger discovery on OPC-UA servers
- Save discovered tags to database
- Query tags by equipment/route
- Statistics

Autor: Claude Code
Data: 2025-11-10
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

from app.core.deps import get_current_user
import logging

logger = logging.getLogger(__name__)


router = APIRouter()


# ============================================================
# SCHEMAS
# ============================================================

class OPCUAServerConfig(BaseModel):
    """Configuração de servidor OPC-UA"""
    endpoint: str = Field(..., description="URL do servidor OPC-UA", example="opc.tcp://localhost:4840")
    device_name: str = Field(..., description="Nome do device", example="PLC Terminal TEAG")
    namespace_filter: Optional[List[int]] = Field(None, description="Filtrar apenas esses namespaces")
    equipment_filter: Optional[List[str]] = Field(None, description="Filtrar tipos de equipamento", example=["TRANSPORTADOR", "ELEVADOR"])
    timeout: int = Field(15, description="Timeout em segundos", ge=5, le=60)
    scan_rate_ms: int = Field(1000, description="Taxa de scan padrão (ms)", ge=100, le=60000)


class DiscoveryJobRequest(BaseModel):
    """Request para iniciar job de discovery"""
    server: OPCUAServerConfig
    save_to_database: bool = Field(True, description="Salvar tags no PostgreSQL")


class DiscoveryJobResponse(BaseModel):
    """Response de job de discovery"""
    job_id: str
    status: str  # "started", "running", "completed", "failed"
    message: str


class DiscoveredTagResponse(BaseModel):
    """Tag descoberto"""
    tag_name: str
    display_name: str
    address: str
    data_type: str
    current_value: Optional[str]
    equipment_type: Optional[str]
    equipment_id: Optional[str]
    route: Optional[str]
    category: Optional[str]
    unit: Optional[str]
    description: Optional[str]
    readable: bool
    writable: bool


class DiscoveryResultResponse(BaseModel):
    """Resultado completo de discovery"""
    endpoint: str
    device_name: str
    total_discovered: int
    classified: int
    unclassified: int
    saved_to_database: bool
    timestamp: datetime
    tags: List[DiscoveredTagResponse]
    statistics: dict


class TagQueryResponse(BaseModel):
    """Response de query de tags"""
    total: int
    tags: List[dict]


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/discover", response_model=DiscoveryResultResponse, tags=["OPC-UA Discovery"])
async def discover_opcua_tags(
    request: DiscoveryJobRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Descobre tags de servidor OPC-UA

    Executa auto-discovery completo:
    1. Conecta ao servidor OPC-UA
    2. Descobre todos os tags
    3. Classifica por equipamento e rota
    4. (Opcional) Salva no PostgreSQL

    **Requires**: Autenticação
    """
    try:
        # Import aqui para evitar circular imports
        import sys
        from pathlib import Path

        # Adicionar path do gateway
        gateway_path = Path(__file__).parent.parent.parent.parent.parent / "gateway" / "app"
        if str(gateway_path) not in sys.path:
            sys.path.insert(0, str(gateway_path))

        from services.tag_auto_discovery import TagAutoDiscovery
        from services.tag_persistence import save_discovered_tags

        logger.info(f"🔍 Starting OPC-UA discovery on {request.server.endpoint}")

        # Criar serviço de discovery
        discovery = TagAutoDiscovery(
            opcua_endpoint=request.server.endpoint,
            timeout=request.server.timeout
        )

        # Executar discovery
        tags = await discovery.discover_all(
            namespace_filter=request.server.namespace_filter,
            equipment_filter=request.server.equipment_filter
        )

        if not tags:
            raise HTTPException(
                status_code=404,
                detail="No tags discovered. Check if OPC-UA server is accessible."
            )

        # Estatísticas
        classified = sum(1 for t in tags if t.equipment_type)
        unclassified = len(tags) - classified

        # Salvar no banco se solicitado
        saved = False
        if request.save_to_database:
            try:
                from app.core.config import settings

                db_config = {
                    'host': settings.POSTGRES_SERVER,
                    'port': settings.POSTGRES_PORT,
                    'database': settings.POSTGRES_DB,
                    'user': settings.POSTGRES_USER,
                    'password': settings.POSTGRES_PASSWORD,
                }

                await save_discovered_tags(
                    tags=tags,
                    device_name=request.server.device_name,
                    db_config=db_config
                )

                saved = True
                logger.info(f"✓ Saved {len(tags)} tags to database")

            except Exception as e:
                logger.error(f"❌ Failed to save tags to database: {str(e)}")
                # Não falhar a request, apenas log o erro

        # Preparar response
        tag_responses = [
            DiscoveredTagResponse(
                tag_name=tag.tag_name,
                display_name=tag.display_name,
                address=tag.address,
                data_type=tag.data_type,
                current_value=str(tag.current_value) if tag.current_value is not None else None,
                equipment_type=tag.equipment_type,
                equipment_id=tag.equipment_id,
                route=tag.route,
                category=tag.category,
                unit=tag.unit,
                description=tag.description,
                readable=tag.readable,
                writable=tag.writable
            )
            for tag in tags
        ]

        return DiscoveryResultResponse(
            endpoint=request.server.endpoint,
            device_name=request.server.device_name,
            total_discovered=len(tags),
            classified=classified,
            unclassified=unclassified,
            saved_to_database=saved,
            timestamp=datetime.now(),
            tags=tag_responses,
            statistics=discovery.stats
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Discovery failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Discovery failed: {str(e)}"
        )


@router.get("/tags/by-equipment/{equipment_type}", response_model=TagQueryResponse, tags=["OPC-UA Discovery"])
async def get_tags_by_equipment(
    equipment_type: str,
    equipment_id: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """
    Busca tags por tipo de equipamento

    **Equipments types**:
    - TRANSPORTADOR
    - ELEVADOR
    - BALANCA
    - ATUADOR
    - SHIPLOADER

    **Requires**: Autenticação
    """
    try:
        import sys
        from pathlib import Path

        gateway_path = Path(__file__).parent.parent.parent.parent.parent / "gateway" / "app"
        if str(gateway_path) not in sys.path:
            sys.path.insert(0, str(gateway_path))

        from services.tag_persistence import TagPersistence
        from app.core.config import settings

        db_config = {
            'host': settings.POSTGRES_SERVER,
            'port': settings.POSTGRES_PORT,
            'database': settings.POSTGRES_DB,
            'user': settings.POSTGRES_USER,
            'password': settings.POSTGRES_PASSWORD,
        }

        persistence = TagPersistence(db_config)

        try:
            tags = await persistence.get_tags_by_equipment(
                equipment_type=equipment_type.upper(),
                equipment_id=equipment_id.upper() if equipment_id else None
            )

            return TagQueryResponse(
                total=len(tags),
                tags=tags
            )

        finally:
            await persistence.disconnect()

    except Exception as e:
        logger.error(f"❌ Query failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


@router.get("/tags/by-route/{route}", response_model=TagQueryResponse, tags=["OPC-UA Discovery"])
async def get_tags_by_route(
    route: str,
    current_user = Depends(get_current_user)
):
    """
    Busca tags por rota do terminal

    **Routes**:
    - IMPAR_A (Rota Ímpar - Linha A)
    - PAR_B (Rota Par - Linha B)
    - TRANSFER (Rota de Transferência)
    - SHIPLOADER_1
    - SHIPLOADER_2

    **Requires**: Autenticação
    """
    try:
        import sys
        from pathlib import Path

        gateway_path = Path(__file__).parent.parent.parent.parent.parent / "gateway" / "app"
        if str(gateway_path) not in sys.path:
            sys.path.insert(0, str(gateway_path))

        from services.tag_persistence import TagPersistence
        from app.core.config import settings

        db_config = {
            'host': settings.POSTGRES_SERVER,
            'port': settings.POSTGRES_PORT,
            'database': settings.POSTGRES_DB,
            'user': settings.POSTGRES_USER,
            'password': settings.POSTGRES_PASSWORD,
        }

        persistence = TagPersistence(db_config)

        try:
            tags = await persistence.get_tags_by_route(route=route.upper())

            return TagQueryResponse(
                total=len(tags),
                tags=tags
            )

        finally:
            await persistence.disconnect()

    except Exception as e:
        logger.error(f"❌ Query failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


@router.get("/statistics", tags=["OPC-UA Discovery"])
async def get_discovery_statistics(
    current_user = Depends(get_current_user)
):
    """
    Retorna estatísticas de tags descobertos

    **Requires**: Autenticação
    """
    try:
        import sys
        from pathlib import Path

        gateway_path = Path(__file__).parent.parent.parent.parent.parent / "gateway" / "app"
        if str(gateway_path) not in sys.path:
            sys.path.insert(0, str(gateway_path))

        from services.tag_persistence import TagPersistence
        from app.core.config import settings

        db_config = {
            'host': settings.POSTGRES_SERVER,
            'port': settings.POSTGRES_PORT,
            'database': settings.POSTGRES_DB,
            'user': settings.POSTGRES_USER,
            'password': settings.POSTGRES_PASSWORD,
        }

        persistence = TagPersistence(db_config)

        try:
            stats = await persistence.get_statistics()
            return stats

        finally:
            await persistence.disconnect()

    except Exception as e:
        logger.error(f"❌ Query failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )
