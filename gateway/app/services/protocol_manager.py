"""
Protocol Manager
================

Unified manager for all protocol adapters.

Responsibilities:
- Load adapter configurations from file/database
- Start/stop all adapters
- Monitor adapter health
- Provide unified API for adapter management
- Aggregate statistics from all adapters

This is the main entry point for the event-driven data acquisition system.
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging
import json
from pathlib import Path

from .protocols.base_adapter import BaseProtocolAdapter, ProtocolConfig

logger = logging.getLogger(__name__)


class ProtocolManager:
    """
    Central manager for all protocol adapters

    Features:
    - Dynamic adapter loading from configuration
    - Concurrent startup of multiple adapters
    - Health monitoring with automatic restart
    - Unified statistics API
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize protocol manager

        Args:
            config_path: Path to JSON configuration file (optional)
        """
        self.config_path = config_path
        self.adapters: Dict[str, BaseProtocolAdapter] = {}
        self.running = False

        # Health monitoring
        self._health_task: Optional[asyncio.Task] = None
        self._health_check_interval = 30  # seconds

        logger.info("🔧 Protocol Manager initialized")

    def register_adapter(self, adapter_id: str, adapter: BaseProtocolAdapter):
        """
        Register a protocol adapter

        Args:
            adapter_id: Unique adapter identifier
            adapter: Adapter instance
        """
        if adapter_id in self.adapters:
            logger.warning(f"⚠️  Adapter {adapter_id} already registered - replacing")

        self.adapters[adapter_id] = adapter
        logger.info(f"✅ Registered adapter: {adapter_id} ({adapter.protocol_type})")

    def unregister_adapter(self, adapter_id: str):
        """Remove adapter from manager"""
        if adapter_id in self.adapters:
            del self.adapters[adapter_id]
            logger.info(f"🗑️  Unregistered adapter: {adapter_id}")

    async def load_config(self, config_path: Optional[str] = None) -> int:
        """
        Load adapter configurations from JSON file

        Args:
            config_path: Path to configuration file (uses constructor path if not provided)

        Returns:
            Number of adapters loaded

        Configuration file format:
        {
            "adapters": [
                {
                    "adapter_id": "plc1_modbus",
                    "protocol_type": "modbus",
                    "enabled": true,
                    "host": "192.168.1.10",
                    "port": 502,
                    "scan_rate_ms": 1000,
                    "tags": [
                        {
                            "name": "Temperature",
                            "address": "40001",
                            "type": "float32"
                        }
                    ],
                    "extra_config": {
                        "slave_id": 1
                    }
                }
            ]
        }
        """
        path = config_path or self.config_path

        if not path:
            logger.warning("⚠️  No configuration path provided")
            return 0

        config_file = Path(path)

        if not config_file.exists():
            logger.warning(f"⚠️  Configuration file not found: {path}")
            return 0

        try:
            logger.info(f"📖 Loading adapter configuration from: {path}")

            with open(config_file, 'r') as f:
                config_data = json.load(f)

            adapters_config = config_data.get('adapters', [])

            # Load tags from tags_config.json and distribute to adapters
            tags_by_adapter = self._load_tags_by_adapter(config_file.parent)

            loaded_count = 0

            for adapter_config in adapters_config:
                try:
                    # Skip disabled adapters
                    if not adapter_config.get('enabled', True):
                        logger.info(f"⏭️  Skipping disabled adapter: {adapter_config.get('adapter_id')}")
                        continue

                    adapter_id = adapter_config.get('adapter_id')

                    # Merge tags from tags_config.json if adapter doesn't have embedded tags
                    if not adapter_config.get('tags') and adapter_id in tags_by_adapter:
                        adapter_config['tags'] = tags_by_adapter[adapter_id]
                        logger.info(f"📋 Loaded {len(adapter_config['tags'])} tags for {adapter_id} from tags_config.json")

                    # Create adapter from configuration
                    adapter = await self._create_adapter_from_config(adapter_config)

                    if adapter:
                        self.register_adapter(adapter.adapter_id, adapter)
                        loaded_count += 1

                except Exception as e:
                    logger.error(f"❌ Failed to load adapter {adapter_config.get('adapter_id')}: {e}")
                    continue

            logger.info(f"✅ Loaded {loaded_count} adapters from configuration")
            return loaded_count

        except Exception as e:
            logger.error(f"❌ Failed to load configuration file: {e}", exc_info=True)
            return 0

    def _load_tags_by_adapter(self, config_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load tags from tags_config.json and group by adapter_id

        Args:
            config_dir: Directory containing tags_config.json

        Returns:
            Dict mapping adapter_id to list of tag configurations
        """
        tags_file = config_dir / "tags_config.json"

        if not tags_file.exists():
            logger.warning(f"⚠️  Tags config file not found: {tags_file}")
            return {}

        try:
            with open(tags_file, 'r') as f:
                tags_data = json.load(f)

            tags_list = tags_data.get('tags', tags_data) if isinstance(tags_data, dict) else tags_data

            tags_by_adapter: Dict[str, List[Dict[str, Any]]] = {}

            for tag in tags_list:
                adapter_id = tag.get('adapter_id')
                if not adapter_id:
                    continue

                if adapter_id not in tags_by_adapter:
                    tags_by_adapter[adapter_id] = []

                # Convert tag config to format expected by adapters
                tag_config = {
                    'name': tag.get('tag_name', tag.get('name')),
                    'address': tag.get('address'),
                    'type': tag.get('data_type', 'float32'),
                    'tag_id': tag.get('tag_id'),
                    'unit': tag.get('metadata', {}).get('engineering_units', ''),
                }

                # Add protocol-specific fields
                protocol = tag.get('protocol_type', '')

                if protocol == 'modbus':
                    # Parse Modbus-specific fields from address
                    address = tag.get('address', '')
                    tag_config['function'] = 'holding'  # Default to holding registers
                    if address.startswith('30'):
                        tag_config['function'] = 'input'
                    elif address.startswith('00') or address.startswith('0'):
                        tag_config['function'] = 'coil'
                    elif address.startswith('10'):
                        tag_config['function'] = 'discrete'

                elif protocol == 'mqtt':
                    # MQTT uses address as topic
                    tag_config['path'] = tag.get('metadata', {}).get('json_path', 'value')

                tags_by_adapter[adapter_id].append(tag_config)

            total_tags = sum(len(tags) for tags in tags_by_adapter.values())
            logger.info(f"📦 Loaded {total_tags} tags from tags_config.json for {len(tags_by_adapter)} adapters")

            return tags_by_adapter

        except Exception as e:
            logger.error(f"❌ Failed to load tags config: {e}", exc_info=True)
            return {}

    async def _create_adapter_from_config(self, config_dict: Dict[str, Any]) -> Optional[BaseProtocolAdapter]:
        """Create adapter instance from configuration dictionary"""
        try:
            protocol_type = config_dict.get('protocol_type', '').lower()

            # Create ProtocolConfig
            protocol_config = ProtocolConfig(
                adapter_id=config_dict['adapter_id'],
                protocol_type=protocol_type,
                enabled=config_dict.get('enabled', True),
                host=config_dict.get('host', 'localhost'),
                port=config_dict.get('port', 502),
                timeout=config_dict.get('timeout', 5.0),
                retry_interval=config_dict.get('retry_interval', 10.0),
                max_retries=config_dict.get('max_retries', 5),
                scan_rate_ms=config_dict.get('scan_rate_ms', 1000),
                batch_size=config_dict.get('batch_size', 100),
                extra_config=config_dict.get('extra_config', {}),
                tags=config_dict.get('tags', [])
            )

            # Create protocol-specific adapter
            if protocol_type == 'opcua':
                from .protocols.opcua_adapter import OPCUAAdapter
                return OPCUAAdapter(protocol_config)

            elif protocol_type == 'modbus':
                from .protocols.modbus_adapter import ModbusAdapter
                return ModbusAdapter(protocol_config)

            elif protocol_type == 'mqtt':
                from .protocols.mqtt_adapter import MQTTAdapter
                return MQTTAdapter(protocol_config)

            elif protocol_type == 'ethernetip':
                from .protocols.ethernetip_adapter import EtherNetIPAdapter
                return EtherNetIPAdapter(protocol_config)

            # Virtual adapters for Node-RED simulation
            elif protocol_type == 'virtual_opcua':
                from .protocols.virtual_adapter import OPCUAVirtualAdapter
                return OPCUAVirtualAdapter(protocol_config)

            elif protocol_type == 'virtual_modbus':
                from .protocols.virtual_adapter import ModbusVirtualAdapter
                return ModbusVirtualAdapter(protocol_config)

            elif protocol_type == 'virtual_profinet':
                from .protocols.virtual_adapter import ProfinetVirtualAdapter
                return ProfinetVirtualAdapter(protocol_config)

            elif protocol_type == 'virtual_ethernetip':
                from .protocols.virtual_adapter import EthernetIPVirtualAdapter
                return EthernetIPVirtualAdapter(protocol_config)

            else:
                logger.error(f"❌ Unknown protocol type: {protocol_type}")
                return None

        except Exception as e:
            logger.error(f"❌ Error creating adapter: {e}", exc_info=True)
            return None

    async def start_all(self):
        """Start all registered adapters concurrently"""
        if self.running:
            logger.warning("⚠️  Protocol Manager already running")
            return

        logger.info(f"🚀 Starting {len(self.adapters)} protocol adapters...")

        # Start all adapters concurrently
        start_tasks = [
            adapter.start()
            for adapter in self.adapters.values()
            if adapter.config.enabled
        ]

        if start_tasks:
            await asyncio.gather(*start_tasks, return_exceptions=True)

        # Start health monitoring
        self.running = True
        self._health_task = asyncio.create_task(self._health_monitor())

        # Count successful starts
        started_count = sum(1 for adapter in self.adapters.values() if adapter.running)

        logger.info(f"✅ Protocol Manager started - {started_count}/{len(self.adapters)} adapters running")

    async def stop_all(self):
        """Stop all adapters"""
        if not self.running:
            return

        logger.info(f"🛑 Stopping {len(self.adapters)} protocol adapters...")

        # Stop health monitoring
        self.running = False
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass

        # Stop all adapters concurrently
        stop_tasks = [
            adapter.stop()
            for adapter in self.adapters.values()
        ]

        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

        logger.info("✅ Protocol Manager stopped")

    async def _health_monitor(self):
        """Monitor adapter health and restart if needed"""
        logger.info(f"🏥 Health monitor started (interval: {self._health_check_interval}s)")

        while self.running:
            try:
                await asyncio.sleep(self._health_check_interval)

                for adapter_id, adapter in self.adapters.items():
                    try:
                        # Skip disabled adapters
                        if not adapter.config.enabled:
                            continue

                        # Check if adapter should be running but isn't
                        if not adapter.running:
                            logger.warning(f"⚠️  Adapter {adapter_id} not running - attempting restart...")
                            await adapter.start()

                    except Exception as e:
                        logger.error(f"❌ Error monitoring adapter {adapter_id}: {e}")

            except asyncio.CancelledError:
                logger.info("Health monitor cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in health monitor: {e}", exc_info=True)

    def get_adapter(self, adapter_id: str) -> Optional[BaseProtocolAdapter]:
        """Get adapter by ID"""
        return self.adapters.get(adapter_id)

    def get_all_adapters(self) -> Dict[str, BaseProtocolAdapter]:
        """Get all adapters"""
        return self.adapters.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics from all adapters"""
        stats = {
            'total_adapters': len(self.adapters),
            'running_adapters': sum(1 for a in self.adapters.values() if a.running),
            'connected_adapters': sum(1 for a in self.adapters.values() if a.connected),
            'adapters': {}
        }

        for adapter_id, adapter in self.adapters.items():
            stats['adapters'][adapter_id] = adapter.get_stats()

        return stats

    def get_status(self) -> Dict[str, Any]:
        """Get overall manager status"""
        return {
            'running': self.running,
            'total_adapters': len(self.adapters),
            'running_adapters': sum(1 for a in self.adapters.values() if a.running),
            'connected_adapters': sum(1 for a in self.adapters.values() if a.connected),
            'health_monitor_active': self._health_task is not None and not self._health_task.done()
        }


# Global singleton instance
_protocol_manager: Optional[ProtocolManager] = None


def get_protocol_manager() -> ProtocolManager:
    """Get global protocol manager instance"""
    global _protocol_manager
    if _protocol_manager is None:
        _protocol_manager = ProtocolManager()
    return _protocol_manager


async def init_protocol_manager(config_path: Optional[str] = None):
    """Initialize protocol manager and load configuration"""
    manager = get_protocol_manager()

    if config_path:
        await manager.load_config(config_path)

    await manager.start_all()

    return manager


async def cleanup_protocol_manager():
    """Cleanup protocol manager"""
    global _protocol_manager
    if _protocol_manager:
        await _protocol_manager.stop_all()
        _protocol_manager = None
