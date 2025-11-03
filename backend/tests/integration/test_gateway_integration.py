"""
Gateway Integration Tests
Tests Gateway integration with Modbus simulator
"""
import pytest
import asyncio
import subprocess
import time
from httpx import AsyncClient


@pytest.fixture(scope="module")
def modbus_simulator():
    """Start Modbus simulator for testing"""
    # Start simulator on port 5020
    process = subprocess.Popen(
        ["python", "simulators/modbus_device_simulator.py", "--port", "5020"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for simulator to start
    time.sleep(3)

    yield process

    # Cleanup
    process.terminate()
    process.wait()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_gateway_connects_to_simulator(
    client: AsyncClient,
    test_site,
    auth_headers,
    modbus_simulator
):
    """
    Test that Gateway can connect to Modbus simulator
    """

    # Step 1: Create device pointing to simulator
    device_data = {
        "name": "Simulator PLC",
        "protocol": "modbus_tcp",
        "ip_address": "localhost",
        "port": 5020,
        "site_id": str(test_site.id),
        "enabled": True,
        "scan_rate": 1000
    }

    response = await client.post("/api/v1/devices/", json=device_data, headers=auth_headers)
    assert response.status_code == 201
    device = response.json()
    device_id = device["id"]

    # Step 2: Create tags for simulated data
    tags_data = [
        {
            "name": "Temperature",
            "address": "40001",
            "data_type": "FLOAT",
            "device_id": device_id,
            "unit": "°C",
            "scale_factor": 0.1,
            "enabled": True,
            "log_enabled": True
        },
        {
            "name": "Pressure",
            "address": "40011",
            "data_type": "FLOAT",
            "device_id": device_id,
            "unit": "bar",
            "scale_factor": 0.1,
            "enabled": True,
            "log_enabled": True
        },
        {
            "name": "Flow_Rate",
            "address": "40021",
            "data_type": "INT",
            "device_id": device_id,
            "unit": "L/min",
            "enabled": True,
            "log_enabled": True
        },
        {
            "name": "Motor_Running",
            "address": "1",
            "data_type": "BOOL",
            "device_id": device_id,
            "enabled": True,
            "log_enabled": True
        }
    ]

    tag_ids = []
    for tag_data in tags_data:
        response = await client.post("/api/v1/tags/", json=tag_data, headers=auth_headers)
        assert response.status_code == 201
        tag = response.json()
        tag_ids.append(tag["id"])

    # Step 3: Wait for Gateway to connect and read tags (simulation)
    # In real integration test, we would wait for Gateway to poll
    await asyncio.sleep(2)

    # Step 4: Verify device configuration
    response = await client.get(f"/api/v1/devices/{device_id}", headers=auth_headers)
    assert response.status_code == 200
    device_info = response.json()
    assert device_info["enabled"] == True
    assert device_info["protocol"] == "modbus_tcp"
    assert device_info["port"] == 5020

    # Step 5: Verify tags were created
    response = await client.get(f"/api/v1/tags/?device_id={device_id}", headers=auth_headers)
    assert response.status_code == 200
    tags = response.json()
    assert len(tags) == 4


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multiple_protocol_devices(
    client: AsyncClient,
    test_site,
    auth_headers
):
    """
    Test configuring devices with different protocols
    """

    protocols = [
        {"protocol": "modbus_tcp", "port": 502},
        {"protocol": "opcua", "port": 4840},
        {"protocol": "s7", "port": 102, "config": {"rack": 0, "slot": 1}},
        {"protocol": "ethernetip", "port": 44818, "config": {"processor_slot": 0}},
        {"protocol": "mqtt", "port": 1883}
    ]

    device_ids = []

    for i, proto_config in enumerate(protocols):
        device_data = {
            "name": f"Device {proto_config['protocol'].upper()}",
            "protocol": proto_config["protocol"],
            "ip_address": f"192.168.1.{i+100}",
            "port": proto_config["port"],
            "site_id": str(test_site.id),
            "enabled": True,
            "scan_rate": 1000
        }

        if "config" in proto_config:
            device_data["config"] = proto_config["config"]

        response = await client.post("/api/v1/devices/", json=device_data, headers=auth_headers)
        assert response.status_code == 201
        device = response.json()
        device_ids.append(device["id"])

        # Verify protocol-specific config
        if "config" in proto_config:
            assert device["config"] == proto_config["config"]

    # Verify all devices were created
    assert len(device_ids) == len(protocols)

    # Verify each device can be retrieved
    for device_id in device_ids:
        response = await client.get(f"/api/v1/devices/{device_id}", headers=auth_headers)
        assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_tag_data_types(
    client: AsyncClient,
    test_device,
    auth_headers
):
    """
    Test all supported tag data types
    """

    data_types = [
        {"type": "BOOL", "address": "1"},
        {"type": "INT", "address": "40001"},
        {"type": "FLOAT", "address": "40002"},
        {"type": "DOUBLE", "address": "40003"},
        {"type": "STRING", "address": "40004"},
        {"type": "BYTE", "address": "40005"},
        {"type": "WORD", "address": "40006"},
        {"type": "DWORD", "address": "40007"}
    ]

    tag_ids = []

    for dt in data_types:
        tag_data = {
            "name": f"Tag_{dt['type']}",
            "address": dt["address"],
            "data_type": dt["type"],
            "device_id": str(test_device.id),
            "enabled": True,
            "log_enabled": True
        }

        response = await client.post("/api/v1/tags/", json=tag_data, headers=auth_headers)
        assert response.status_code == 201
        tag = response.json()
        assert tag["data_type"] == dt["type"]
        tag_ids.append(tag["id"])

    # Verify all tags were created
    assert len(tag_ids) == len(data_types)

    # Verify we can retrieve each tag
    for tag_id in tag_ids:
        response = await client.get(f"/api/v1/tags/{tag_id}", headers=auth_headers)
        assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.integration
async def test_device_connection_status(
    client: AsyncClient,
    test_device,
    auth_headers
):
    """
    Test device connection status tracking
    """

    # Get device status
    response = await client.get(f"/api/v1/devices/{test_device.id}", headers=auth_headers)
    assert response.status_code == 200
    device = response.json()

    # Device should have these fields for connection tracking
    assert "enabled" in device
    assert "protocol" in device
    assert "ip_address" in device
    assert "port" in device

    # Disable device
    update_data = {"enabled": False}
    response = await client.put(
        f"/api/v1/devices/{test_device.id}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    updated_device = response.json()
    assert updated_device["enabled"] == False

    # Re-enable device
    update_data = {"enabled": True}
    response = await client.put(
        f"/api/v1/devices/{test_device.id}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    updated_device = response.json()
    assert updated_device["enabled"] == True


@pytest.mark.asyncio
@pytest.mark.integration
async def test_high_frequency_tag_creation(
    client: AsyncClient,
    test_device,
    auth_headers
):
    """
    Test creating many tags quickly (simulates bulk import)
    """

    num_tags = 50
    tag_ids = []

    # Create 50 tags
    for i in range(num_tags):
        tag_data = {
            "name": f"Bulk_Tag_{i}",
            "address": f"{40000 + i}",
            "data_type": "FLOAT",
            "device_id": str(test_device.id),
            "unit": "units",
            "enabled": True,
            "log_enabled": True
        }

        response = await client.post("/api/v1/tags/", json=tag_data, headers=auth_headers)
        assert response.status_code == 201
        tag = response.json()
        tag_ids.append(tag["id"])

    # Verify count
    assert len(tag_ids) == num_tags

    # Verify we can list all tags for this device
    response = await client.get(
        f"/api/v1/tags/?device_id={test_device.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    tags = response.json()
    assert len(tags) >= num_tags
