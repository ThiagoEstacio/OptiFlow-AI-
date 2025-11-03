"""
Device CRUD endpoint tests
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_create_device(client: AsyncClient, test_site, auth_headers):
    """Test creating a new device"""
    device_data = {
        "name": "PLC Main",
        "protocol": "modbus_tcp",
        "ip_address": "192.168.1.50",
        "port": 502,
        "site_id": str(test_site.id),
        "enabled": True,
        "scan_rate": 1000
    }

    response = await client.post(
        "/api/v1/devices/",
        json=device_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "PLC Main"
    assert data["protocol"] == "modbus_tcp"
    assert data["ip_address"] == "192.168.1.50"
    assert data["port"] == 502
    assert "id" in data


@pytest.mark.asyncio
async def test_list_devices(client: AsyncClient, test_device, auth_headers):
    """Test listing devices"""
    response = await client.get(
        "/api/v1/devices/",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == test_device.name


@pytest.mark.asyncio
async def test_get_device_by_id(client: AsyncClient, test_device, auth_headers):
    """Test getting device by ID"""
    response = await client.get(
        f"/api/v1/devices/{test_device.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_device.id)
    assert data["name"] == test_device.name
    assert data["protocol"] == test_device.protocol


@pytest.mark.asyncio
async def test_get_nonexistent_device(client: AsyncClient, auth_headers):
    """Test getting non-existent device"""
    fake_id = uuid4()
    response = await client.get(
        f"/api/v1/devices/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_device(client: AsyncClient, test_device, auth_headers):
    """Test updating a device"""
    update_data = {
        "name": "PLC Updated",
        "ip_address": "192.168.1.60",
        "port": 503
    }

    response = await client.put(
        f"/api/v1/devices/{test_device.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "PLC Updated"
    assert data["ip_address"] == "192.168.1.60"
    assert data["port"] == 503


@pytest.mark.asyncio
async def test_delete_device(client: AsyncClient, test_device, auth_headers):
    """Test deleting a device"""
    response = await client.delete(
        f"/api/v1/devices/{test_device.id}",
        headers=auth_headers
    )

    assert response.status_code == 204

    # Verify device is deleted
    get_response = await client.get(
        f"/api/v1/devices/{test_device.id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_create_device_invalid_protocol(client: AsyncClient, test_site, auth_headers):
    """Test creating device with invalid protocol"""
    device_data = {
        "name": "Invalid Device",
        "protocol": "invalid_protocol",  # Invalid
        "ip_address": "192.168.1.50",
        "port": 502,
        "site_id": str(test_site.id),
        "enabled": True
    }

    response = await client.post(
        "/api/v1/devices/",
        json=device_data,
        headers=auth_headers
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_device_invalid_port(client: AsyncClient, test_site, auth_headers):
    """Test creating device with invalid port"""
    device_data = {
        "name": "Invalid Port Device",
        "protocol": "modbus_tcp",
        "ip_address": "192.168.1.50",
        "port": 70000,  # Invalid (> 65535)
        "site_id": str(test_site.id),
        "enabled": True
    }

    response = await client.post(
        "/api/v1/devices/",
        json=device_data,
        headers=auth_headers
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_device_s7_protocol(client: AsyncClient, test_site, auth_headers):
    """Test creating device with Siemens S7 protocol"""
    device_data = {
        "name": "S7-1200",
        "protocol": "s7",
        "ip_address": "192.168.1.70",
        "port": 102,
        "site_id": str(test_site.id),
        "config": {
            "rack": 0,
            "slot": 1
        },
        "enabled": True,
        "scan_rate": 500
    }

    response = await client.post(
        "/api/v1/devices/",
        json=device_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["protocol"] == "s7"
    assert data["config"]["rack"] == 0
    assert data["config"]["slot"] == 1


@pytest.mark.asyncio
async def test_create_device_ethernetip_protocol(client: AsyncClient, test_site, auth_headers):
    """Test creating device with Ethernet/IP protocol"""
    device_data = {
        "name": "CompactLogix",
        "protocol": "ethernetip",
        "ip_address": "192.168.1.80",
        "port": 44818,
        "site_id": str(test_site.id),
        "config": {
            "processor_slot": 0
        },
        "enabled": True,
        "scan_rate": 500
    }

    response = await client.post(
        "/api/v1/devices/",
        json=device_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["protocol"] == "ethernetip"
    assert data["config"]["processor_slot"] == 0


@pytest.mark.asyncio
async def test_filter_devices_by_site(
    client: AsyncClient,
    test_device,
    test_site,
    auth_headers
):
    """Test filtering devices by site_id"""
    response = await client.get(
        f"/api/v1/devices/?site_id={test_site.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(device["site_id"] == str(test_site.id) for device in data)
