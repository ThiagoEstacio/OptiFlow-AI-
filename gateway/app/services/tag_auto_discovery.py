"""
OPC-UA Tag Auto-Discovery Service
==================================

Serviço responsável por:
1. Descobrir automaticamente tags OPC-UA
2. Classificar tags por tipo de equipamento
3. Mapear para rotas do terminal (Ímpar/Par/Transfer)
4. Preparar para persistência otimizada

Autor: Claude Code
Data: 2025-11-10
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re
import asyncio

from app.core.logger import logger
from app.services.opcua_browser import OPCUABrowser


# ============================================================
# PATTERNS DE CLASSIFICAÇÃO
# ============================================================

EQUIPMENT_PATTERNS = {
    'TRANSPORTADOR': r'^TC-\d{4}',          # TC-4511, TC-4512, etc
    'ELEVADOR': r'^EL-\d{4}',               # EL-4511, EL-4512, etc
    'BALANCA': r'^BL-\d{2}',                # BL-01, BL-02
    'ATUADOR': r'^AP-TT\d{5}',              # AP-TT77003-01A, etc
    'SHIPLOADER': r'^SHIPLOADER[_-]?\d{2}', # SHIPLOADER_01, SHIPLOADER-02
}

# Mapeamento de equipamentos para rotas
ROUTE_MAPPING = {
    # Rota Ímpar (A)
    'TC-4511': 'IMPAR_A',
    'TC-4513': 'IMPAR_A',
    'EL-4511': 'IMPAR_A',

    # Rota Par (B)
    'TC-4512': 'PAR_B',
    'TC-4514': 'PAR_B',
    'EL-4512': 'PAR_B',

    # Rota de Transferência
    'TC-1521': 'TRANSFER',
    'TC-4515': 'TRANSFER',
    'TC-1511': 'TRANSFER',

    # Balanças (comuns)
    'BL-01': 'IMPAR_A',
    'BL-02': 'PAR_B',

    # Shiploaders (destinos finais)
    'SHIPLOADER_01': 'SHIPLOADER_1',
    'SHIPLOADER-01': 'SHIPLOADER_1',
    'SHIPLOADER_02': 'SHIPLOADER_2',
    'SHIPLOADER-02': 'SHIPLOADER_2',
}

# Categorias de tags
TAG_CATEGORIES = {
    'Speed': 'SPEED',
    'Current': 'CURRENT',
    'Running': 'STATUS',
    'Stop': 'STATUS',
    'Alarm': 'ALARM',
    'Fault': 'FAULT',
    'Power_kW': 'POWER',
    'Power': 'POWER',
    'Flow_tph': 'FLOW',
    'Flow': 'FLOW',
    'Load_pct': 'LOAD',
    'Load': 'LOAD',
    'Temp_C': 'TEMPERATURE',
    'Temperature': 'TEMPERATURE',
    'Vibration': 'VIBRATION',
    'Misalignment': 'ALIGNMENT',
    'Weight_t': 'WEIGHT',
    'Weight': 'WEIGHT',
    'Total_t': 'TOTAL',
    'Total': 'TOTAL',
    'Position': 'POSITION',
    'Command': 'COMMAND',
    'Setpoint': 'SETPOINT',
}

# Mapeamento de data types OPC-UA para tipos simplificados
DATATYPE_MAPPING = {
    'Double': 'FLOAT',
    'Float': 'FLOAT',
    'Int32': 'INTEGER',
    'Int64': 'INTEGER',
    'UInt32': 'INTEGER',
    'UInt64': 'INTEGER',
    'Boolean': 'BOOLEAN',
    'String': 'STRING',
}


@dataclass
class DiscoveredTag:
    """Representa um tag descoberto e classificado"""

    # Informações básicas do OPC-UA
    tag_name: str
    display_name: str
    address: str  # NodeID OPC-UA
    data_type: str
    current_value: Any

    # Classificação automática
    equipment_type: Optional[str] = None
    equipment_id: Optional[str] = None
    route: Optional[str] = None
    category: Optional[str] = None

    # Metadados
    description: Optional[str] = None
    unit: Optional[str] = None
    readable: bool = True
    writable: bool = False

    # Contexto para IA
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'tag_name': self.tag_name,
            'display_name': self.display_name,
            'address': self.address,
            'data_type': self.data_type,
            'current_value': self.current_value,
            'equipment_type': self.equipment_type,
            'equipment_id': self.equipment_id,
            'route': self.route,
            'category': self.category,
            'description': self.description,
            'unit': self.unit,
            'readable': self.readable,
            'writable': self.writable,
            'context': self.context or {},
        }


class TagAutoDiscovery:
    """
    Serviço de auto-discovery de tags OPC-UA

    Otimizado para:
    - Descoberta rápida
    - Classificação automática
    - Batch processing
    - Minimizar consultas ao servidor
    """

    def __init__(self, opcua_endpoint: str, timeout: int = 10):
        """
        Inicializa serviço de auto-discovery

        Args:
            opcua_endpoint: URL do servidor OPC-UA (e.g., opc.tcp://localhost:4840)
            timeout: Timeout de conexão em segundos
        """
        self.endpoint = opcua_endpoint
        self.browser = OPCUABrowser(endpoint=opcua_endpoint, timeout=timeout)

        # Estatísticas
        self.stats = {
            'total_discovered': 0,
            'classified': 0,
            'unclassified': 0,
            'by_type': {},
            'by_route': {},
        }

    async def discover_all(
        self,
        namespace_filter: Optional[List[int]] = None,
        equipment_filter: Optional[List[str]] = None
    ) -> List[DiscoveredTag]:
        """
        Descobre e classifica todos os tags

        Args:
            namespace_filter: Filtrar apenas esses namespaces (e.g., [2, 3])
            equipment_filter: Filtrar apenas esses tipos (e.g., ['TRANSPORTADOR', 'ELEVADOR'])

        Returns:
            Lista de tags descobertos e classificados
        """
        logger.info(f"🔍 Starting auto-discovery on {self.endpoint}")

        try:
            # Conectar ao servidor
            connected = await self.browser.connect()
            if not connected:
                logger.error("❌ Failed to connect to OPC-UA server")
                return []

            # Descobrir todos os tags
            logger.info("📡 Discovering tags...")
            raw_tags = await self.browser.discover_all_tags(namespace_filter=namespace_filter)

            self.stats['total_discovered'] = len(raw_tags)
            logger.info(f"✓ Discovered {len(raw_tags)} raw tags")

            # Classificar tags
            logger.info("🏷️  Classifying tags...")
            classified_tags = []

            for raw_tag in raw_tags:
                discovered_tag = self._classify_tag(raw_tag)

                # Aplicar filtro de equipamento se especificado
                if equipment_filter:
                    if discovered_tag.equipment_type not in equipment_filter:
                        continue

                classified_tags.append(discovered_tag)

            # Atualizar estatísticas
            self._update_stats(classified_tags)

            logger.info(f"✓ Classified {len(classified_tags)} tags")
            self._log_stats()

            return classified_tags

        except Exception as e:
            logger.error(f"❌ Auto-discovery failed: {str(e)}", exc_info=True)
            return []

        finally:
            await self.browser.disconnect()

    def _classify_tag(self, raw_tag: Dict[str, Any]) -> DiscoveredTag:
        """
        Classifica um tag individual

        Args:
            raw_tag: Tag bruto do OPC-UA browser

        Returns:
            Tag classificado
        """
        tag_name = raw_tag.get('tag_name', '')
        display_name = raw_tag.get('display_name', tag_name)

        # Classificar tipo de equipamento e extrair ID
        equipment_type, equipment_id = self._classify_equipment(tag_name)

        # Determinar rota
        route = self._determine_route(equipment_id) if equipment_id else None

        # Determinar categoria do tag
        category = self._classify_category(tag_name)

        # Inferir unidade de medida
        unit = self._infer_unit(tag_name, category)

        # Mapear data type
        data_type = self._map_datatype(raw_tag.get('data_type', 'String'))

        # Gerar contexto para IA
        context = self._generate_context(
            equipment_type=equipment_type,
            equipment_id=equipment_id,
            route=route,
            category=category,
            tag_name=tag_name
        )

        return DiscoveredTag(
            tag_name=tag_name,
            display_name=display_name,
            address=raw_tag.get('address', ''),
            data_type=data_type,
            current_value=raw_tag.get('current_value'),
            equipment_type=equipment_type,
            equipment_id=equipment_id,
            route=route,
            category=category,
            description=raw_tag.get('description'),
            unit=unit,
            readable=raw_tag.get('readable', True),
            writable=raw_tag.get('writable', False),
            context=context,
        )

    def _classify_equipment(self, tag_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Classifica tipo de equipamento e extrai ID

        Returns:
            (tipo, equipment_id) ou (None, None)
        """
        for eq_type, pattern in EQUIPMENT_PATTERNS.items():
            match = re.match(pattern, tag_name, re.IGNORECASE)
            if match:
                # Extrair equipment ID (parte antes do primeiro ponto)
                parts = tag_name.split('.')
                equipment_id = parts[0] if parts else tag_name
                return eq_type, equipment_id

        return None, None

    def _determine_route(self, equipment_id: str) -> Optional[str]:
        """Determina rota do terminal baseado no equipment ID"""
        return ROUTE_MAPPING.get(equipment_id.upper())

    def _classify_category(self, tag_name: str) -> Optional[str]:
        """Classifica categoria do tag (Speed, Current, etc)"""
        # Extrai a parte após o ponto (e.g., "TC-4511.Speed" -> "Speed")
        parts = tag_name.split('.')
        if len(parts) > 1:
            suffix = parts[-1]
            for key, category in TAG_CATEGORIES.items():
                if key.lower() in suffix.lower():
                    return category

        return None

    def _infer_unit(self, tag_name: str, category: Optional[str]) -> Optional[str]:
        """Infere unidade de medida baseado no nome e categoria"""
        tag_lower = tag_name.lower()

        # Unidades explícitas no nome
        if '_kw' in tag_lower or 'power_kw' in tag_lower:
            return 'kW'
        if '_tph' in tag_lower or 'flow_tph' in tag_lower:
            return 't/h'
        if '_t' in tag_lower or 'weight_t' in tag_lower or 'total_t' in tag_lower:
            return 't'
        if '_c' in tag_lower or 'temp_c' in tag_lower:
            return '°C'
        if '_pct' in tag_lower or 'load_pct' in tag_lower:
            return '%'
        if 'current' in tag_lower:
            return 'A'
        if 'speed' in tag_lower:
            return 'm/s'
        if 'vibration' in tag_lower:
            return 'mm/s'

        # Baseado na categoria
        if category == 'POWER':
            return 'kW'
        elif category == 'FLOW':
            return 't/h'
        elif category == 'CURRENT':
            return 'A'
        elif category == 'SPEED':
            return 'm/s'
        elif category == 'TEMPERATURE':
            return '°C'
        elif category == 'VIBRATION':
            return 'mm/s'
        elif category == 'LOAD':
            return '%'

        return None

    def _map_datatype(self, opcua_datatype: str) -> str:
        """Mapeia data type OPC-UA para tipo simplificado"""
        for opcua_type, simple_type in DATATYPE_MAPPING.items():
            if opcua_type.lower() in opcua_datatype.lower():
                return simple_type

        return 'STRING'  # Default

    def _generate_context(
        self,
        equipment_type: Optional[str],
        equipment_id: Optional[str],
        route: Optional[str],
        category: Optional[str],
        tag_name: str
    ) -> Dict[str, Any]:
        """
        Gera contexto rico para uso do agente IA

        Este contexto ajuda o agente a entender:
        - Onde o equipamento está localizado
        - Qual sua função no processo
        - Relacionamento com outros equipamentos
        """
        context = {
            'discovered_at': datetime.now().isoformat(),
            'discovery_method': 'opcua_auto_discovery',
        }

        if equipment_type:
            context['equipment_type'] = equipment_type

            # Descrições em linguagem natural para IA
            if equipment_type == 'TRANSPORTADOR':
                context['description_pt'] = 'Transportador de correia'
                context['function'] = 'Transporte de material graneleiro'
            elif equipment_type == 'ELEVADOR':
                context['description_pt'] = 'Elevador de canecas'
                context['function'] = 'Elevação vertical de grãos'
            elif equipment_type == 'BALANCA':
                context['description_pt'] = 'Balança de fluxo'
                context['function'] = 'Pesagem e medição de vazão'
            elif equipment_type == 'ATUADOR':
                context['description_pt'] = 'Atuador pneumático'
                context['function'] = 'Controle de fluxo (válvula/comporta)'
            elif equipment_type == 'SHIPLOADER':
                context['description_pt'] = 'Carregador de navios'
                context['function'] = 'Carregamento de grãos em navio'

        if equipment_id:
            context['equipment_id'] = equipment_id

        if route:
            context['route'] = route

            # Contexto de processo
            if route == 'IMPAR_A':
                context['route_description'] = 'Rota Ímpar - Linha A de embarque'
            elif route == 'PAR_B':
                context['route_description'] = 'Rota Par - Linha B de embarque'
            elif route == 'TRANSFER':
                context['route_description'] = 'Rota de transferência entre silos'

        if category:
            context['measurement_category'] = category

        return context

    def _update_stats(self, tags: List[DiscoveredTag]):
        """Atualiza estatísticas de descoberta"""
        self.stats['classified'] = sum(1 for t in tags if t.equipment_type)
        self.stats['unclassified'] = len(tags) - self.stats['classified']

        # Por tipo
        for tag in tags:
            if tag.equipment_type:
                self.stats['by_type'][tag.equipment_type] = \
                    self.stats['by_type'].get(tag.equipment_type, 0) + 1

            if tag.route:
                self.stats['by_route'][tag.route] = \
                    self.stats['by_route'].get(tag.route, 0) + 1

    def _log_stats(self):
        """Log de estatísticas"""
        logger.info("📊 Discovery Statistics:")
        logger.info(f"  Total discovered: {self.stats['total_discovered']}")
        logger.info(f"  Classified: {self.stats['classified']}")
        logger.info(f"  Unclassified: {self.stats['unclassified']}")

        if self.stats['by_type']:
            logger.info("  By equipment type:")
            for eq_type, count in self.stats['by_type'].items():
                logger.info(f"    {eq_type}: {count}")

        if self.stats['by_route']:
            logger.info("  By route:")
            for route, count in self.stats['by_route'].items():
                logger.info(f"    {route}: {count}")


async def quick_discovery(endpoint: str) -> List[DiscoveredTag]:
    """
    Função helper para descoberta rápida

    Args:
        endpoint: URL do servidor OPC-UA

    Returns:
        Lista de tags descobertos
    """
    discovery = TagAutoDiscovery(endpoint)
    return await discovery.discover_all()
