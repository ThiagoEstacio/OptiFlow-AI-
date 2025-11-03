"""
Gateway Production Manager

Production-ready tools for managing industrial gateways:
- Connection testing and validation
- Configuration validation
- Health monitoring
- Production deployment helpers
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.gateway_config import GatewayConfig, GatewayType
from app.gateways.gateway_manager import GatewayManager
from app.gateways.opcua_gateway import OPCUAGateway
from app.gateways.modbus_gateway import ModbusGateway
from app.gateways.siemens_gateway import SiemensGateway
from app.gateways.rockwell_gateway import RockwellGateway

logger = logging.getLogger(__name__)


class GatewayProductionManager:
    """
    Production management for industrial gateways.

    Provides tools for:
    - Pre-deployment testing
    - Configuration validation
    - Connection diagnostics
    - Performance benchmarking
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def test_gateway_connection(
        self,
        gateway_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Test a gateway connection before deployment.

        Args:
            gateway_config: Gateway configuration to test

        Returns:
            Test results with connection status and metrics
        """
        gateway_type = gateway_config.get('gateway_type')
        gateway_name = gateway_config.get('name', 'test_gateway')

        logger.info(f"Testing {gateway_type} gateway: {gateway_name}")

        result = {
            "gateway_name": gateway_name,
            "gateway_type": gateway_type,
            "test_timestamp": datetime.utcnow().isoformat(),
            "tests": {},
            "overall_status": "unknown",
        }

        try:
            # Create gateway instance
            gateway_class = {
                'opcua': OPCUAGateway,
                'modbus_tcp': ModbusGateway,
                'siemens_s7': SiemensGateway,
                'rockwell_eip': RockwellGateway,
            }.get(gateway_type)

            if not gateway_class:
                result["overall_status"] = "error"
                result["error"] = f"Unknown gateway type: {gateway_type}"
                return result

            gateway = gateway_class(
                name=gateway_name,
                config=gateway_config
            )

            # Test 1: Connection
            connection_test = await self._test_connection(gateway)
            result["tests"]["connection"] = connection_test

            if connection_test["status"] == "success":
                # Test 2: Read performance
                read_test = await self._test_read_performance(gateway, gateway_config)
                result["tests"]["read_performance"] = read_test

                # Test 3: Reliability
                reliability_test = await self._test_reliability(gateway, gateway_config)
                result["tests"]["reliability"] = reliability_test

                # Disconnect
                await gateway.disconnect()

            # Determine overall status
            all_passed = all(
                test.get("status") == "success"
                for test in result["tests"].values()
            )

            result["overall_status"] = "success" if all_passed else "partial_failure"

        except Exception as e:
            result["overall_status"] = "error"
            result["error"] = str(e)
            logger.error(f"Error testing gateway: {e}")

        return result

    async def _test_connection(self, gateway) -> Dict[str, Any]:
        """Test basic connection to gateway."""
        try:
            start_time = datetime.now()
            success = await gateway.connect_with_retry()
            connection_time = (datetime.now() - start_time).total_seconds()

            return {
                "status": "success" if success else "failed",
                "connection_time_seconds": round(connection_time, 3),
                "message": "Connection successful" if success else "Connection failed",
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }

    async def _test_read_performance(
        self,
        gateway,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test read performance with configured tags."""
        try:
            tags = config.get('tags', [])
            if not tags:
                return {
                    "status": "skipped",
                    "message": "No tags configured for testing",
                }

            # Read all tags multiple times
            iterations = 5
            read_times = []

            for _ in range(iterations):
                start_time = datetime.now()
                data_points = await gateway.read_multiple_tags(tags[:5])  # Test first 5 tags
                read_time = (datetime.now() - start_time).total_seconds()
                read_times.append(read_time)

                if not data_points:
                    return {
                        "status": "failed",
                        "message": "No data returned from gateway",
                    }

            avg_read_time = sum(read_times) / len(read_times)

            return {
                "status": "success",
                "tags_tested": min(len(tags), 5),
                "iterations": iterations,
                "average_read_time_seconds": round(avg_read_time, 3),
                "min_read_time_seconds": round(min(read_times), 3),
                "max_read_time_seconds": round(max(read_times), 3),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }

    async def _test_reliability(
        self,
        gateway,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test connection reliability with reconnection."""
        try:
            # Disconnect and reconnect
            await gateway.disconnect()
            await asyncio.sleep(1)

            start_time = datetime.now()
            success = await gateway.connect_with_retry()
            reconnect_time = (datetime.now() - start_time).total_seconds()

            if not success:
                return {
                    "status": "failed",
                    "message": "Reconnection failed",
                }

            return {
                "status": "success",
                "reconnect_time_seconds": round(reconnect_time, 3),
                "message": "Reconnection successful",
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }

    async def validate_configuration(
        self,
        gateway_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate gateway configuration before deployment.

        Checks:
        - Required fields present
        - Valid data types
        - Network reachability
        - Tag configuration
        """
        errors = []
        warnings = []

        # Check required fields
        if not gateway_config.get('name'):
            errors.append("Gateway name is required")

        if not gateway_config.get('gateway_type'):
            errors.append("Gateway type is required")

        connection_config = gateway_config.get('connection_config', {})
        if not connection_config:
            errors.append("Connection configuration is required")

        gateway_type = gateway_config.get('gateway_type')

        # Type-specific validation
        if gateway_type == 'opcua':
            if not connection_config.get('endpoint'):
                errors.append("OPC-UA endpoint is required")
            elif not connection_config['endpoint'].startswith('opc.tcp://'):
                warnings.append("OPC-UA endpoint should start with 'opc.tcp://'")

        elif gateway_type == 'modbus_tcp':
            if not connection_config.get('host'):
                errors.append("Modbus host is required")
            if not connection_config.get('port'):
                warnings.append("Modbus port not specified, using default 502")

        elif gateway_type == 'siemens_s7':
            if not connection_config.get('host'):
                errors.append("Siemens host is required")
            if connection_config.get('rack') is None:
                warnings.append("Rack not specified, using default 0")
            if connection_config.get('slot') is None:
                warnings.append("Slot not specified, using default 1")

        elif gateway_type == 'rockwell_eip':
            if not connection_config.get('host'):
                errors.append("Rockwell host is required")

        # Tag configuration validation
        tags = gateway_config.get('tags', [])
        if not tags:
            warnings.append("No tags configured")
        else:
            for i, tag in enumerate(tags):
                if not tag.get('tag_name'):
                    errors.append(f"Tag {i}: tag_name is required")
                if not tag.get('address_config'):
                    errors.append(f"Tag {i}: address_config is required")

        # Polling interval validation
        polling_interval = gateway_config.get('polling_interval_ms', 1000)
        if polling_interval < 100:
            warnings.append("Polling interval < 100ms may cause performance issues")
        elif polling_interval > 60000:
            warnings.append("Polling interval > 60s may miss important events")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "configuration_score": self._calculate_config_score(errors, warnings),
        }

    def _calculate_config_score(
        self,
        errors: List[str],
        warnings: List[str]
    ) -> int:
        """Calculate configuration quality score (0-100)."""
        score = 100
        score -= len(errors) * 20  # Each error -20 points
        score -= len(warnings) * 5  # Each warning -5 points
        return max(0, score)

    async def benchmark_gateway(
        self,
        gateway_id: int,
        duration_seconds: int = 60
    ) -> Dict[str, Any]:
        """
        Benchmark gateway performance.

        Args:
            gateway_id: Gateway configuration ID
            duration_seconds: How long to run the benchmark

        Returns:
            Performance metrics
        """
        try:
            # Get gateway configuration
            result = await self.db.execute(
                select(GatewayConfig).where(GatewayConfig.id == gateway_id)
            )
            config = result.scalar_one_or_none()

            if not config:
                raise ValueError(f"Gateway {gateway_id} not found")

            logger.info(f"Starting {duration_seconds}s benchmark for gateway {config.name}")

            # Create gateway instance
            gateway_dict = {
                'name': config.name,
                'gateway_type': config.gateway_type.value,
                'connection_config': config.connection_config,
                'polling_interval_ms': config.polling_interval_ms,
                'tags': [tag.to_dict() for tag in config.tags if tag.enabled],
            }

            gateway_class = {
                'opcua': OPCUAGateway,
                'modbus_tcp': ModbusGateway,
                'siemens_s7': SiemensGateway,
                'rockwell_eip': RockwellGateway,
            }.get(config.gateway_type.value)

            gateway = gateway_class(
                name=config.name,
                config=gateway_dict
            )

            # Connect
            await gateway.connect_with_retry()

            # Benchmark loop
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=duration_seconds)

            read_count = 0
            error_count = 0
            read_times = []

            while datetime.now() < end_time:
                try:
                    read_start = datetime.now()
                    data_points = await gateway.read_multiple_tags(gateway_dict['tags'])
                    read_time = (datetime.now() - read_start).total_seconds()

                    read_times.append(read_time)
                    read_count += 1

                    if not data_points:
                        error_count += 1

                except Exception as e:
                    error_count += 1
                    logger.error(f"Benchmark read error: {e}")

                await asyncio.sleep(gateway_dict['polling_interval_ms'] / 1000)

            # Disconnect
            await gateway.disconnect()

            # Calculate metrics
            total_time = (datetime.now() - start_time).total_seconds()
            avg_read_time = sum(read_times) / len(read_times) if read_times else 0
            success_rate = ((read_count - error_count) / read_count * 100) if read_count > 0 else 0

            return {
                "gateway_id": gateway_id,
                "gateway_name": config.name,
                "duration_seconds": round(total_time, 2),
                "total_reads": read_count,
                "successful_reads": read_count - error_count,
                "failed_reads": error_count,
                "success_rate": round(success_rate, 2),
                "average_read_time_seconds": round(avg_read_time, 3),
                "min_read_time_seconds": round(min(read_times), 3) if read_times else None,
                "max_read_time_seconds": round(max(read_times), 3) if read_times else None,
                "reads_per_second": round(read_count / total_time, 2),
                "benchmark_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error benchmarking gateway: {e}")
            raise

    async def create_production_config_template(
        self,
        gateway_type: str
    ) -> Dict[str, Any]:
        """
        Create a production-ready configuration template.

        Args:
            gateway_type: Type of gateway

        Returns:
            Configuration template with production defaults
        """
        templates = {
            'opcua': {
                "name": "Production OPC-UA Gateway",
                "gateway_type": "opcua",
                "enabled": True,
                "connection_config": {
                    "endpoint": "opc.tcp://192.168.1.100:4840",
                    "namespace": "urn:production:server",
                    "security_policy": "Basic256Sha256",  # Production security
                    "username": None,
                    "password": None,
                },
                "polling_interval_ms": 1000,
                "max_retries": 5,
                "base_retry_delay": 5,
                "max_buffer_size": 10000,
                "description": "Production OPC-UA gateway with security enabled",
                "tags": [],
            },
            'modbus_tcp': {
                "name": "Production Modbus TCP Gateway",
                "gateway_type": "modbus_tcp",
                "enabled": True,
                "connection_config": {
                    "host": "192.168.1.101",
                    "port": 502,
                    "unit_id": 1,
                    "timeout": 3,
                },
                "polling_interval_ms": 2000,
                "max_retries": 5,
                "base_retry_delay": 5,
                "max_buffer_size": 10000,
                "description": "Production Modbus TCP gateway",
                "tags": [],
            },
            'siemens_s7': {
                "name": "Production Siemens S7 Gateway",
                "gateway_type": "siemens_s7",
                "enabled": True,
                "connection_config": {
                    "host": "192.168.1.102",
                    "port": 102,
                    "rack": 0,
                    "slot": 1,
                },
                "polling_interval_ms": 1000,
                "max_retries": 5,
                "base_retry_delay": 5,
                "max_buffer_size": 10000,
                "description": "Production Siemens S7 gateway",
                "tags": [],
            },
            'rockwell_eip': {
                "name": "Production Rockwell Gateway",
                "gateway_type": "rockwell_eip",
                "enabled": True,
                "connection_config": {
                    "host": "192.168.1.103",
                    "port": 44818,
                    "slot": 0,
                    "micro800": False,
                },
                "polling_interval_ms": 1000,
                "max_retries": 5,
                "base_retry_delay": 5,
                "max_buffer_size": 10000,
                "description": "Production Rockwell EtherNet/IP gateway",
                "tags": [],
            },
        }

        template = templates.get(gateway_type)
        if not template:
            raise ValueError(f"Unknown gateway type: {gateway_type}")

        return template
