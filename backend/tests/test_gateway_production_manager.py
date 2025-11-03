"""
Tests for Gateway Production Manager Service
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.gateway_production_manager import GatewayProductionManager


@pytest.mark.asyncio
async def test_validate_configuration_success(test_db: AsyncSession):
    """Test successful gateway configuration validation"""
    manager = GatewayProductionManager(test_db)

    config = {
        "name": "Test Gateway",
        "protocol": "opcua",
        "host": "192.168.1.100",
        "port": 4840,
        "tags": [
            {
                "name": "Temperature",
                "node_id": "ns=2;s=Temperature",
                "data_type": "FLOAT"
            }
        ]
    }

    result = await manager.validate_configuration(config)

    assert result["valid"] is True
    assert result["errors"] == []
    assert "warnings" in result


@pytest.mark.asyncio
async def test_validate_configuration_missing_required_fields(test_db: AsyncSession):
    """Test validation with missing required fields"""
    manager = GatewayProductionManager(test_db)

    config = {
        "name": "Test Gateway",
        # Missing protocol, host, port
    }

    result = await manager.validate_configuration(config)

    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert any("protocol" in error.lower() for error in result["errors"])


@pytest.mark.asyncio
async def test_validate_configuration_invalid_protocol(test_db: AsyncSession):
    """Test validation with invalid protocol"""
    manager = GatewayProductionManager(test_db)

    config = {
        "name": "Test Gateway",
        "protocol": "invalid_protocol",
        "host": "192.168.1.100",
        "port": 502,
    }

    result = await manager.validate_configuration(config)

    assert result["valid"] is False
    assert any("protocol" in error.lower() for error in result["errors"])


@pytest.mark.asyncio
async def test_validate_configuration_invalid_port(test_db: AsyncSession):
    """Test validation with invalid port range"""
    manager = GatewayProductionManager(test_db)

    config = {
        "name": "Test Gateway",
        "protocol": "modbus_tcp",
        "host": "192.168.1.100",
        "port": 70000,  # Invalid port
    }

    result = await manager.validate_configuration(config)

    assert result["valid"] is False
    assert any("port" in error.lower() for error in result["errors"])


@pytest.mark.asyncio
async def test_validate_configuration_security_warnings(test_db: AsyncSession):
    """Test validation generates security warnings"""
    manager = GatewayProductionManager(test_db)

    config = {
        "name": "Test Gateway",
        "protocol": "opcua",
        "host": "192.168.1.100",
        "port": 4840,
        # No security configured
    }

    result = await manager.validate_configuration(config)

    assert "warnings" in result
    assert len(result["warnings"]) > 0


@pytest.mark.asyncio
async def test_create_production_config_template_opcua(test_db: AsyncSession):
    """Test creating OPC-UA production config template"""
    manager = GatewayProductionManager(test_db)

    result = await manager.create_production_config_template("opcua")

    assert result["protocol"] == "opcua"
    assert result["port"] == 4840
    assert "security" in result
    assert result["security"]["enabled"] is True
    assert "tags" in result
    assert isinstance(result["tags"], list)


@pytest.mark.asyncio
async def test_create_production_config_template_modbus(test_db: AsyncSession):
    """Test creating Modbus TCP production config template"""
    manager = GatewayProductionManager(test_db)

    result = await manager.create_production_config_template("modbus_tcp")

    assert result["protocol"] == "modbus_tcp"
    assert result["port"] == 502
    assert "tags" in result
    assert len(result["tags"]) > 0


@pytest.mark.asyncio
async def test_create_production_config_template_siemens_s7(test_db: AsyncSession):
    """Test creating Siemens S7 production config template"""
    manager = GatewayProductionManager(test_db)

    result = await manager.create_production_config_template("siemens_s7")

    assert result["protocol"] == "siemens_s7"
    assert result["port"] == 102
    assert "rack" in result
    assert "slot" in result


@pytest.mark.asyncio
async def test_create_production_config_template_rockwell(test_db: AsyncSession):
    """Test creating Rockwell production config template"""
    manager = GatewayProductionManager(test_db)

    result = await manager.create_production_config_template("rockwell")

    assert result["protocol"] == "rockwell"
    assert result["port"] == 44818
    assert "tags" in result


@pytest.mark.asyncio
async def test_create_production_config_template_invalid_type(test_db: AsyncSession):
    """Test creating template with invalid gateway type"""
    manager = GatewayProductionManager(test_db)

    with pytest.raises(ValueError) as exc_info:
        await manager.create_production_config_template("invalid_type")

    assert "unsupported gateway type" in str(exc_info.value).lower()


@pytest.mark.asyncio
@patch('app.services.gateway_production_manager.IndustrialGateway')
async def test_test_gateway_connection_success(mock_gateway_class, test_db: AsyncSession):
    """Test successful gateway connection test"""
    # Mock gateway instance
    mock_gateway = AsyncMock()
    mock_gateway.connect = AsyncMock(return_value=True)
    mock_gateway.disconnect = AsyncMock()
    mock_gateway.read_tag = AsyncMock(return_value={"value": 42.5, "timestamp": "2024-01-01T00:00:00"})
    mock_gateway_class.return_value = mock_gateway

    manager = GatewayProductionManager(test_db)

    config = {
        "name": "Test Gateway",
        "protocol": "opcua",
        "host": "192.168.1.100",
        "port": 4840,
    }

    result = await manager.test_gateway_connection(config)

    assert result["status"] == "success"
    assert result["connection_successful"] is True
    assert "performance" in result
    mock_gateway.connect.assert_called_once()
    mock_gateway.disconnect.assert_called()


@pytest.mark.asyncio
@patch('app.services.gateway_production_manager.IndustrialGateway')
async def test_test_gateway_connection_failure(mock_gateway_class, test_db: AsyncSession):
    """Test failed gateway connection"""
    # Mock gateway that fails to connect
    mock_gateway = AsyncMock()
    mock_gateway.connect = AsyncMock(side_effect=Exception("Connection refused"))
    mock_gateway_class.return_value = mock_gateway

    manager = GatewayProductionManager(test_db)

    config = {
        "name": "Test Gateway",
        "protocol": "opcua",
        "host": "192.168.1.100",
        "port": 4840,
    }

    result = await manager.test_gateway_connection(config)

    assert result["status"] == "error"
    assert result["connection_successful"] is False
    assert "error" in result
    assert "connection refused" in result["error"].lower()


@pytest.mark.asyncio
@patch('app.services.gateway_production_manager.IndustrialGateway')
async def test_benchmark_gateway_performance(mock_gateway_class, test_db: AsyncSession, test_device):
    """Test gateway performance benchmarking"""
    # Mock gateway with consistent read times
    mock_gateway = AsyncMock()
    mock_gateway.connect = AsyncMock(return_value=True)
    mock_gateway.disconnect = AsyncMock()
    mock_gateway.read_tag = AsyncMock(return_value={"value": 42.5, "timestamp": "2024-01-01T00:00:00"})
    mock_gateway_class.return_value = mock_gateway

    manager = GatewayProductionManager(test_db)

    # Run short benchmark (1 second)
    result = await manager.benchmark_gateway(test_device.id, duration_seconds=1)

    assert "read_count" in result
    assert "success_rate" in result
    assert "average_read_time_ms" in result
    assert "reads_per_second" in result
    assert result["read_count"] > 0
    assert 0 <= result["success_rate"] <= 100


@pytest.mark.asyncio
async def test_validate_configuration_with_tags(test_db: AsyncSession):
    """Test configuration validation with tag validation"""
    manager = GatewayProductionManager(test_db)

    config = {
        "name": "Test Gateway",
        "protocol": "modbus_tcp",
        "host": "192.168.1.100",
        "port": 502,
        "tags": [
            {
                "name": "Temperature",
                "address": "40001",
                "data_type": "FLOAT"
            },
            {
                "name": "Pressure",
                "address": "40002",
                "data_type": "FLOAT"
            }
        ]
    }

    result = await manager.validate_configuration(config)

    assert result["valid"] is True
    assert "tag_count" in result
    assert result["tag_count"] == 2


@pytest.mark.asyncio
async def test_validate_configuration_duplicate_tag_names(test_db: AsyncSession):
    """Test validation detects duplicate tag names"""
    manager = GatewayProductionManager(test_db)

    config = {
        "name": "Test Gateway",
        "protocol": "modbus_tcp",
        "host": "192.168.1.100",
        "port": 502,
        "tags": [
            {
                "name": "Temperature",
                "address": "40001",
                "data_type": "FLOAT"
            },
            {
                "name": "Temperature",  # Duplicate
                "address": "40002",
                "data_type": "FLOAT"
            }
        ]
    }

    result = await manager.validate_configuration(config)

    assert "warnings" in result
    assert any("duplicate" in warning.lower() for warning in result["warnings"])
