"""
Site CRUD endpoint tests
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_create_site(client: AsyncClient, test_organization, auth_headers):
    """Test creating a new site"""
    site_data = {
        "name": "Santos Port",
        "site_type": "smartport",
        "organization_id": str(test_organization.id),
        "latitude": -23.9355,
        "longitude": -46.3219,
        "is_active": True
    }

    response = await client.post(
        "/api/v1/sites/",
        json=site_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Santos Port"
    assert data["site_type"] == "smartport"
    assert data["latitude"] == -23.9355
    assert data["longitude"] == -46.3219
    assert "id" in data


@pytest.mark.asyncio
async def test_list_sites(client: AsyncClient, test_site, auth_headers):
    """Test listing sites"""
    response = await client.get(
        "/api/v1/sites/",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == test_site.name


@pytest.mark.asyncio
async def test_get_site_by_id(client: AsyncClient, test_site, auth_headers):
    """Test getting site by ID"""
    response = await client.get(
        f"/api/v1/sites/{test_site.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_site.id)
    assert data["name"] == test_site.name
    assert data["site_type"] == test_site.site_type


@pytest.mark.asyncio
async def test_get_nonexistent_site(client: AsyncClient, auth_headers):
    """Test getting non-existent site"""
    fake_id = uuid4()
    response = await client.get(
        f"/api/v1/sites/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_site(client: AsyncClient, test_site, auth_headers):
    """Test updating a site"""
    update_data = {
        "name": "Updated Port Name",
        "latitude": -22.5555,
        "longitude": -45.6666
    }

    response = await client.put(
        f"/api/v1/sites/{test_site.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Port Name"
    assert data["latitude"] == -22.5555
    assert data["longitude"] == -45.6666


@pytest.mark.asyncio
async def test_delete_site(client: AsyncClient, test_site, auth_headers):
    """Test deleting a site"""
    response = await client.delete(
        f"/api/v1/sites/{test_site.id}",
        headers=auth_headers
    )

    assert response.status_code == 204

    # Verify site is deleted
    get_response = await client.get(
        f"/api/v1/sites/{test_site.id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_create_site_invalid_type(client: AsyncClient, test_organization, auth_headers):
    """Test creating site with invalid site_type"""
    site_data = {
        "name": "Invalid Site",
        "site_type": "invalid_type",  # Invalid type
        "organization_id": str(test_organization.id),
        "is_active": True
    }

    response = await client.post(
        "/api/v1/sites/",
        json=site_data,
        headers=auth_headers
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_site_invalid_coordinates(client: AsyncClient, test_organization, auth_headers):
    """Test creating site with invalid coordinates"""
    site_data = {
        "name": "Invalid Coords Site",
        "site_type": "smartport",
        "organization_id": str(test_organization.id),
        "latitude": 100.0,  # Invalid (> 90)
        "longitude": -200.0,  # Invalid (< -180)
        "is_active": True
    }

    response = await client.post(
        "/api/v1/sites/",
        json=site_data,
        headers=auth_headers
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_filter_sites_by_organization(
    client: AsyncClient,
    test_site,
    test_organization,
    auth_headers
):
    """Test filtering sites by organization_id"""
    response = await client.get(
        f"/api/v1/sites/?organization_id={test_organization.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(site["organization_id"] == str(test_organization.id) for site in data)
