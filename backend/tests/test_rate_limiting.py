"""
Rate limiting tests
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_rate_limit_5_per_minute(client: AsyncClient, test_user):
    """Test auth endpoint rate limit (5/minute)"""
    # Make 5 requests (should all succeed or fail with 401)
    for i in range(5):
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "wrongpass"}
        )
        # Should be 401 (wrong password), not rate limited yet
        assert response.status_code == 401

    # 6th request should be rate limited
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "wrongpass"}
    )
    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_user_creation_rate_limit_10_per_minute(
    client: AsyncClient,
    test_organization,
    auth_headers
):
    """Test user creation rate limit (10/minute)"""
    # Make 10 requests
    for i in range(10):
        response = await client.post(
            "/api/v1/users/",
            json={
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "password": "testpass123",
                "full_name": f"User {i}",
                "organization_id": str(test_organization.id)
            },
            headers=auth_headers
        )
        # Should be 201 (created) or 400 (already exists)
        assert response.status_code in [201, 400]

    # 11th request should be rate limited
    response = await client.post(
        "/api/v1/users/",
        json={
            "username": "user11",
            "email": "user11@example.com",
            "password": "testpass123",
            "full_name": "User 11",
            "organization_id": str(test_organization.id)
        },
        headers=auth_headers
    )
    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_organization_rate_limit_20_per_minute(client: AsyncClient, auth_headers):
    """Test organization creation rate limit (20/minute)"""
    # Make 20 requests
    for i in range(20):
        response = await client.post(
            "/api/v1/organizations/",
            json={"name": f"Org {i}", "is_active": True},
            headers=auth_headers
        )
        # Should be 201 (created) or 400 (already exists)
        assert response.status_code in [201, 400]

    # 21st request should be rate limited
    response = await client.post(
        "/api/v1/organizations/",
        json={"name": "Org 21", "is_active": True},
        headers=auth_headers
    )
    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_site_rate_limit_30_per_minute(
    client: AsyncClient,
    test_organization,
    auth_headers
):
    """Test site creation rate limit (30/minute)"""
    # Make 30 requests
    for i in range(30):
        response = await client.post(
            "/api/v1/sites/",
            json={
                "name": f"Site {i}",
                "site_type": "smartport",
                "organization_id": str(test_organization.id),
                "is_active": True
            },
            headers=auth_headers
        )
        # Should be 201 (created)
        assert response.status_code == 201

    # 31st request should be rate limited
    response = await client.post(
        "/api/v1/sites/",
        json={
            "name": "Site 31",
            "site_type": "smartport",
            "organization_id": str(test_organization.id),
            "is_active": True
        },
        headers=auth_headers
    )
    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_device_rate_limit_30_per_minute(
    client: AsyncClient,
    test_site,
    auth_headers
):
    """Test device creation rate limit (30/minute)"""
    # Make 30 requests
    for i in range(30):
        response = await client.post(
            "/api/v1/devices/",
            json={
                "name": f"Device {i}",
                "protocol": "modbus_tcp",
                "ip_address": f"192.168.1.{i+1}",
                "port": 502,
                "site_id": str(test_site.id),
                "enabled": True
            },
            headers=auth_headers
        )
        # Should be 201 (created)
        assert response.status_code == 201

    # 31st request should be rate limited
    response = await client.post(
        "/api/v1/devices/",
        json={
            "name": "Device 31",
            "protocol": "modbus_tcp",
            "ip_address": "192.168.1.100",
            "port": 502,
            "site_id": str(test_site.id),
            "enabled": True
        },
        headers=auth_headers
    )
    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_tag_rate_limit_50_per_minute(
    client: AsyncClient,
    test_device,
    auth_headers
):
    """Test tag creation rate limit (50/minute)"""
    # Make 50 requests
    for i in range(50):
        response = await client.post(
            "/api/v1/tags/",
            json={
                "name": f"Tag_{i}",
                "address": f"{40000 + i}",
                "data_type": "FLOAT",
                "device_id": str(test_device.id),
                "enabled": True
            },
            headers=auth_headers
        )
        # Should be 201 (created)
        assert response.status_code == 201

    # 51st request should be rate limited
    response = await client.post(
        "/api/v1/tags/",
        json={
            "name": "Tag_51",
            "address": "40051",
            "data_type": "FLOAT",
            "device_id": str(test_device.id),
            "enabled": True
        },
        headers=auth_headers
    )
    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_rate_limit_headers_present(client: AsyncClient, auth_headers):
    """Test that rate limit headers are present in responses"""
    response = await client.get("/", headers=auth_headers)

    # Check for rate limit headers
    assert "X-RateLimit-Limit" in response.headers or "RateLimit-Limit" in response.headers
    # Note: The exact header names depend on slowapi configuration


@pytest.mark.asyncio
async def test_rate_limit_different_endpoints_independent(
    client: AsyncClient,
    test_organization,
    test_site,
    auth_headers
):
    """Test that rate limits are independent between endpoints"""
    # Hit organization endpoint 20 times (its limit)
    for i in range(20):
        await client.post(
            "/api/v1/organizations/",
            json={"name": f"Independent Org {i}", "is_active": True},
            headers=auth_headers
        )

    # Should still be able to create sites (different endpoint, different limit)
    response = await client.post(
        "/api/v1/sites/",
        json={
            "name": "Independent Site",
            "site_type": "smartport",
            "organization_id": str(test_organization.id),
            "is_active": True
        },
        headers=auth_headers
    )
    # Should NOT be rate limited (different endpoint)
    assert response.status_code == 201
