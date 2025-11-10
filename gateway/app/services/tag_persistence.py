"""
Tag Persistence Service
========================

Persiste tags descobertos no PostgreSQL de forma otimizada.

Features:
- Batch inserts (alta performance)
- Upsert (insert or update)
- Gerenciamento de devices
- Evita duplicatas
- Transações atômicas

Autor: Claude Code
Data: 2025-11-10
"""
from typing import List, Dict, Any, Optional
from uuid import uuid4, UUID
from datetime import datetime
import asyncpg

from app.core.logger import logger
from app.services.tag_auto_discovery import DiscoveredTag


class TagPersistence:
    """
    Serviço de persistência otimizada de tags

    Usa batch inserts e upserts para máxima performance
    """

    def __init__(self, db_config: Dict[str, Any]):
        """
        Inicializa serviço de persistência

        Args:
            db_config: Configuração do PostgreSQL
                {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'optiflow',
                    'user': 'optiflow',
                    'password': 'password'
                }
        """
        self.db_config = db_config
        self.conn: Optional[asyncpg.Connection] = None

    async def connect(self):
        """Conecta ao PostgreSQL"""
        if not self.conn:
            logger.info("🔌 Connecting to PostgreSQL...")
            self.conn = await asyncpg.connect(**self.db_config)
            logger.info("✓ Connected to PostgreSQL")

    async def disconnect(self):
        """Desconecta do PostgreSQL"""
        if self.conn:
            await self.conn.close()
            self.conn = None
            logger.info("🔌 Disconnected from PostgreSQL")

    async def ensure_device(
        self,
        device_name: str,
        protocol: str = 'OPC_UA',
        connection_config: Optional[Dict] = None
    ) -> UUID:
        """
        Garante que device existe, criando se necessário

        Args:
            device_name: Nome do device
            protocol: Protocolo (OPC_UA, MODBUS, etc)
            connection_config: Configuração de conexão

        Returns:
            UUID do device
        """
        await self.connect()

        # Verificar se já existe
        existing = await self.conn.fetchrow(
            "SELECT id FROM devices WHERE name = $1",
            device_name
        )

        if existing:
            logger.info(f"✓ Device '{device_name}' already exists")
            return existing['id']

        # Criar novo device
        device_id = uuid4()

        await self.conn.execute("""
            INSERT INTO devices (
                id, name, protocol, connection_config,
                is_active, status, total_tags, data_points_collected,
                description, settings
            ) VALUES (
                $1, $2, $3, $4::jsonb,
                true, 'CONNECTED', 0, 0,
                $5, '{}'::jsonb
            )
        """,
            device_id,
            device_name,
            protocol,
            connection_config or {},
            f'Auto-discovered {protocol} device'
        )

        logger.info(f"✓ Created device '{device_name}' with id {device_id}")
        return device_id

    async def save_tags_batch(
        self,
        tags: List[DiscoveredTag],
        device_id: UUID,
        scan_rate_ms: int = 1000
    ) -> Dict[str, Any]:
        """
        Salva múltiplos tags em batch (otimizado)

        Args:
            tags: Lista de tags descobertos
            device_id: UUID do device
            scan_rate_ms: Taxa de scan padrão (ms)

        Returns:
            Estatísticas de inserção
        """
        await self.connect()

        stats = {
            'total': len(tags),
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }

        if not tags:
            return stats

        logger.info(f"💾 Saving {len(tags)} tags in batch...")

        # Preparar dados para batch insert
        tag_data = []

        for tag in tags:
            # Gerar UUID para o tag
            tag_id = uuid4()

            # Preparar metadados (context + equipment info)
            metadata = {
                **(tag.context or {}),
                'equipment_type': tag.equipment_type,
                'equipment_id': tag.equipment_id,
                'route': tag.route,
                'category': tag.category,
            }

            tag_data.append((
                tag_id,
                device_id,
                tag.tag_name,
                tag.address,
                tag.data_type,
                tag.description or f'Auto-discovered tag from OPC-UA',
                tag.category or 'PROCESS',
                tag.unit,
                scan_rate_ms,
                True,  # is_active
                metadata
            ))

        # Batch insert com ON CONFLICT DO UPDATE (upsert)
        try:
            # Usar transação para atomicidade
            async with self.conn.transaction():
                result = await self.conn.executemany("""
                    INSERT INTO tags (
                        id, device_id, name, address, data_type,
                        description, category, unit, scan_rate_ms,
                        is_active, settings
                    ) VALUES (
                        $1, $2, $3, $4, $5,
                        $6, $7, $8, $9,
                        $10, $11::jsonb
                    )
                    ON CONFLICT (device_id, address) DO UPDATE SET
                        name = EXCLUDED.name,
                        data_type = EXCLUDED.data_type,
                        description = EXCLUDED.description,
                        category = EXCLUDED.category,
                        unit = EXCLUDED.unit,
                        scan_rate_ms = EXCLUDED.scan_rate_ms,
                        is_active = EXCLUDED.is_active,
                        settings = EXCLUDED.settings,
                        updated_at = NOW()
                """, tag_data)

                # Atualizar total_tags no device
                await self.conn.execute("""
                    UPDATE devices
                    SET total_tags = (
                        SELECT COUNT(*) FROM tags WHERE device_id = $1 AND is_active = true
                    ),
                    updated_at = NOW()
                    WHERE id = $1
                """, device_id)

            stats['inserted'] = len(tags)
            logger.info(f"✓ Saved {len(tags)} tags successfully")

        except Exception as e:
            stats['errors'] = len(tags)
            logger.error(f"❌ Failed to save tags: {str(e)}", exc_info=True)
            raise

        return stats

    async def get_device_tags(
        self,
        device_id: UUID,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Recupera tags de um device

        Args:
            device_id: UUID do device
            active_only: Retornar apenas tags ativos

        Returns:
            Lista de tags
        """
        await self.connect()

        query = """
            SELECT
                id, device_id, name, address, data_type,
                description, category, unit, scan_rate_ms,
                is_active, settings, created_at, updated_at
            FROM tags
            WHERE device_id = $1
        """

        if active_only:
            query += " AND is_active = true"

        query += " ORDER BY name"

        rows = await self.conn.fetch(query, device_id)

        return [dict(row) for row in rows]

    async def get_tags_by_equipment(
        self,
        equipment_type: str,
        equipment_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca tags por tipo de equipamento

        Args:
            equipment_type: Tipo (TRANSPORTADOR, ELEVADOR, etc)
            equipment_id: ID específico (opcional, e.g., TC-4511)

        Returns:
            Lista de tags
        """
        await self.connect()

        # Tags armazenam equipment info em settings->equipment_type
        query = """
            SELECT
                id, device_id, name, address, data_type,
                description, category, unit, settings
            FROM tags
            WHERE
                is_active = true
                AND settings->>'equipment_type' = $1
        """

        params = [equipment_type]

        if equipment_id:
            query += " AND settings->>'equipment_id' = $2"
            params.append(equipment_id)

        query += " ORDER BY name"

        rows = await self.conn.fetch(query, *params)
        return [dict(row) for row in rows]

    async def get_tags_by_route(self, route: str) -> List[Dict[str, Any]]:
        """
        Busca tags por rota do terminal

        Args:
            route: Rota (IMPAR_A, PAR_B, TRANSFER, etc)

        Returns:
            Lista de tags
        """
        await self.connect()

        rows = await self.conn.fetch("""
            SELECT
                id, device_id, name, address, data_type,
                description, category, unit, settings
            FROM tags
            WHERE
                is_active = true
                AND settings->>'route' = $1
            ORDER BY name
        """, route)

        return [dict(row) for row in rows]

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do banco

        Returns:
            Estatísticas gerais
        """
        await self.connect()

        # Total de devices
        total_devices = await self.conn.fetchval(
            "SELECT COUNT(*) FROM devices WHERE is_active = true"
        )

        # Total de tags
        total_tags = await self.conn.fetchval(
            "SELECT COUNT(*) FROM tags WHERE is_active = true"
        )

        # Tags por tipo de equipamento
        by_equipment = await self.conn.fetch("""
            SELECT
                settings->>'equipment_type' as equipment_type,
                COUNT(*) as count
            FROM tags
            WHERE
                is_active = true
                AND settings->>'equipment_type' IS NOT NULL
            GROUP BY settings->>'equipment_type'
            ORDER BY count DESC
        """)

        # Tags por rota
        by_route = await self.conn.fetch("""
            SELECT
                settings->>'route' as route,
                COUNT(*) as count
            FROM tags
            WHERE
                is_active = true
                AND settings->>'route' IS NOT NULL
            GROUP BY settings->>'route'
            ORDER BY count DESC
        """)

        return {
            'total_devices': total_devices,
            'total_tags': total_tags,
            'by_equipment_type': {row['equipment_type']: row['count'] for row in by_equipment},
            'by_route': {row['route']: row['count'] for row in by_route},
        }


async def save_discovered_tags(
    tags: List[DiscoveredTag],
    device_name: str,
    db_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Helper function para salvar tags descobertos

    Args:
        tags: Tags descobertos
        device_name: Nome do device
        db_config: Configuração do banco

    Returns:
        Estatísticas
    """
    persistence = TagPersistence(db_config)

    try:
        # Garantir que device existe
        device_id = await persistence.ensure_device(device_name)

        # Salvar tags
        stats = await persistence.save_tags_batch(tags, device_id)

        # Estatísticas do banco
        db_stats = await persistence.get_statistics()

        return {
            'save_stats': stats,
            'database_stats': db_stats
        }

    finally:
        await persistence.disconnect()
