"""
Tag CRUD endpoint tests
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_create_tag(client: AsyncClient, test_device, auth_headers):
    """Test creating a new tag"""
    tag_data = {
        "name": "Pressure_Tank1",
        "address": "40010",
        "data_type": "FLOAT",
        "device_id": str(test_device.id),
        "unit": "Bar",
        "scale_factor": 1.0,
        "offset": 0.0,
        "min_value": 0.0,
        "max_value": 10.0,
        "enabled": True,
        "log_enabled": True
    }

    response = await client.post(
        "/api/v1/tags/",
        json=tag_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Pressure_Tank1"
    assert data["address"] == "40010"
    assert data["data_type"] == "FLOAT"
    assert data["unit"] == "Bar"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_tags(client: AsyncClient, test_tag, auth_headers):
    """Test listing tags"""
    response = await client.get(
        "/api/v1/tags/",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == test_tag.name


@pytest.mark.asyncio
async def test_get_tag_by_id(client: AsyncClient, test_tag, auth_headers):
    """Test getting tag by ID"""
    response = await client.get(
        f"/api/v1/tags/{test_tag.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_tag.id)
    assert data["name"] == test_tag.name
    assert data["data_type"] == test_tag.data_type


@pytest.mark.asyncio
async def test_get_nonexistent_tag(client: AsyncClient, auth_headers):
    """Test getting non-existent tag"""
    fake_id = uuid4()
    response = await client.get(
        f"/api/v1/tags/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_tag(client: AsyncClient, test_tag, auth_headers):
    """Test updating a tag"""
    update_data = {
        "name": "Temperature_Updated",
        "unit": "K",  # Changed from °C to Kelvin
        "scale_factor": 1.5,
        "offset": 273.15
    }

    response = await client.put(
        f"/api/v1/tags/{test_tag.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Temperature_Updated"
    assert data["unit"] == "K"
    assert data["scale_factor"] == 1.5
    assert data["offset"] == 273.15


@pytest.mark.asyncio
async def test_delete_tag(client: AsyncClient, test_tag, auth_headers):
    """Test deleting a tag"""
    response = await client.delete(
        f"/api/v1/tags/{test_tag.id}",
        headers=auth_headers
    )

    assert response.status_code == 204

    # Verify tag is deleted
    get_response = await client.get(
        f"/api/v1/tags/{test_tag.id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_create_tag_invalid_data_type(client: AsyncClient, test_device, auth_headers):
    """Test creating tag with invalid data_type"""
    tag_data = {
        "name": "Invalid_Tag",
        "address": "40020",
        "data_type": "INVALID_TYPE",  # Invalid
        "device_id": str(test_device.id),
        "enabled": True
    }

    response = await client.post(
        "/api/v1/tags/",
        json=tag_data,
        headers=auth_headers
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_tag_bool_type(client: AsyncClient, test_device, auth_headers):
    """Test creating boolean tag"""
    tag_data = {
        "name": "Motor_Running",
        "address": "00001",
        "data_type": "BOOL",
        "device_id": str(test_device.id),
        "enabled": True,
        "log_enabled": True
    }

    response = await client.post(
        "/api/v1/tags/",
        json=tag_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["data_type"] == "BOOL"


@pytest.mark.asyncio
async def test_create_tag_int_type(client: AsyncClient, test_device, auth_headers):
    """Test creating integer tag"""
    tag_data = {
        "name": "Counter_Value",
        "address": "40030",
        "data_type": "INT",
        "device_id": str(test_device.id),
        "min_value": 0,
        "max_value": 65535,
        "enabled": True,
        "log_enabled": True
    }

    response = await client.post(
        "/api/v1/tags/",
        json=tag_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["data_type"] == "INT"
    assert data["min_value"] == 0
    assert data["max_value"] == 65535


@pytest.mark.asyncio
async def test_get_tag_latest_value(client: AsyncClient, test_tag, auth_headers):
    """Test getting latest tag value"""
    response = await client.get(
        f"/api/v1/tags/{test_tag.id}/latest",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "tag_id" in data
    assert "value" in data
    assert "quality" in data
    assert "timestamp" in data
    assert data["tag_id"] == str(test_tag.id)


@pytest.mark.asyncio
async def test_filter_tags_by_device(
    client: AsyncClient,
    test_tag,
    test_device,
    auth_headers
):
    """Test filtering tags by device_id"""
    response = await client.get(
        f"/api/v1/tags/?device_id={test_device.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(tag["device_id"] == str(test_device.id) for tag in data)


@pytest.mark.asyncio
async def test_create_tag_with_category(client: AsyncClient, test_device, auth_headers):
    """Test creating tag with category"""
    tag_data = {
        "name": "Energy_Consumption",
        "address": "40040",
        "data_type": "FLOAT",
        "device_id": str(test_device.id),
        "unit": "kWh",
        "category": "ENERGY",
        "enabled": True,
        "log_enabled": True
    }

    response = await client.post(
        "/api/v1/tags/",
        json=tag_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "ENERGY"
