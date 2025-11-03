"""
Authentication endpoint tests
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Test successful login"""
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["access_token"] is not None


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    """Test login with incorrect password"""
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent user"""
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "nonexistent",
            "password": "password123"
        }
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_missing_credentials(client: AsyncClient):
    """Test login with missing credentials"""
    response = await client.post("/api/v1/auth/login", data={})

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_access_protected_endpoint_without_token(client: AsyncClient):
    """Test accessing protected endpoint without token"""
    response = await client.get("/api/v1/users/")

    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


@pytest.mark.asyncio
async def test_access_protected_endpoint_with_valid_token(
    client: AsyncClient,
    test_user,
    auth_headers
):
    """Test accessing protected endpoint with valid token"""
    response = await client.get(
        "/api/v1/users/",
        headers=auth_headers
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_access_protected_endpoint_with_invalid_token(client: AsyncClient):
    """Test accessing protected endpoint with invalid token"""
    response = await client.get(
        "/api/v1/users/",
        headers={"Authorization": "Bearer invalid_token_12345"}
    )

    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_rate_limiting(client: AsyncClient, test_user):
    """Test rate limiting on login endpoint (5/minute)"""
    # Make 5 failed login attempts
    for i in range(5):
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        # First 5 should be 401 (wrong password)
        assert response.status_code == 401

    # 6th attempt should be rate limited
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 429  # Too Many Requests
    assert "rate limit" in response.json()["detail"].lower()
