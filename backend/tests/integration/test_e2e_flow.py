"""
End-to-End Integration Tests
Tests complete user flows through the SmartPort application
"""
import pytest
import asyncio
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_complete_user_flow(client: AsyncClient, test_db):
    """
    Test complete flow:
    1. Create organization
    2. Create user
    3. Login
    4. Create site
    5. Create device
    6. Create tag
    7. Read tag data
    """

    # Step 1: Create organization
    org_data = {
        "name": "E2E Test Organization",
        "is_active": True
    }

    response = await client.post("/api/v1/organizations/", json=org_data)
    assert response.status_code == 201
    org = response.json()
    org_id = org["id"]

    # Step 2: Create user
    user_data = {
        "username": "e2e_user",
        "email": "e2e@test.com",
        "password": "testpass123",
        "full_name": "E2E Test User",
        "organization_id": org_id
    }

    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    user = response.json()

    # Step 3: Login
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "e2e_user",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    token_data = response.json()
    token = token_data["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Step 4: Create site
    site_data = {
        "name": "E2E Test Port",
        "site_type": "smartport",
        "organization_id": org_id,
        "latitude": -23.5505,
        "longitude": -46.6333,
        "is_active": True
    }

    response = await client.post("/api/v1/sites/", json=site_data, headers=headers)
    assert response.status_code == 201
    site = response.json()
    site_id = site["id"]

    # Step 5: Create device
    device_data = {
        "name": "E2E Test PLC",
        "protocol": "modbus_tcp",
        "ip_address": "192.168.1.100",
        "port": 502,
        "site_id": site_id,
        "enabled": True,
        "scan_rate": 1000
    }

    response = await client.post("/api/v1/devices/", json=device_data, headers=headers)
    assert response.status_code == 201
    device = response.json()
    device_id = device["id"]

    # Step 6: Create tag
    tag_data = {
        "name": "Temperature_Tank1",
        "address": "40001",
        "data_type": "FLOAT",
        "device_id": device_id,
        "unit": "°C",
        "scale_factor": 0.1,
        "enabled": True,
        "log_enabled": True
    }

    response = await client.post("/api/v1/tags/", json=tag_data, headers=headers)
    assert response.status_code == 201
    tag = response.json()
    tag_id = tag["id"]

    # Step 7: Read tag latest value
    response = await client.get(f"/api/v1/tags/{tag_id}/latest", headers=headers)
    assert response.status_code == 200
    tag_value = response.json()
    assert "tag_id" in tag_value
    assert "value" in tag_value
    assert "timestamp" in tag_value

    # Verify all created resources exist
    response = await client.get(f"/api/v1/organizations/{org_id}", headers=headers)
    assert response.status_code == 200

    response = await client.get(f"/api/v1/sites/{site_id}", headers=headers)
    assert response.status_code == 200

    response = await client.get(f"/api/v1/devices/{device_id}", headers=headers)
    assert response.status_code == 200

    response = await client.get(f"/api/v1/tags/{tag_id}", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_alarm_workflow(client: AsyncClient, test_tag, test_db, auth_headers):
    """
    Test alarm creation and acknowledgment workflow
    """
    from app.models.alarm import AlarmEvent
    from datetime import datetime

    # Step 1: Create alarm definition
    alarm_def_data = {
        "name": "High Temperature Alert",
        "alarm_type": "HIGH_LIMIT",
        "severity": "HIGH",
        "tag_id": str(test_tag.id),
        "high_limit": 80.0,
        "enabled": True,
        "message": "Temperature exceeded 80°C"
    }

    response = await client.post(
        "/api/v1/alarms/definitions",
        json=alarm_def_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    alarm_def = response.json()

    # Step 2: Simulate alarm trigger (create alarm event)
    alarm_event = AlarmEvent(
        id=uuid4(),
        tag_id=test_tag.id,
        alarm_type="HIGH_LIMIT",
        severity="HIGH",
        message="Temperature exceeded limit",
        value=85.0,
        limit=80.0,
        status="ACTIVE",
        triggered_at=datetime.utcnow()
    )
    test_db.add(alarm_event)
    await test_db.commit()
    await test_db.refresh(alarm_event)

    # Step 3: List active alarms
    response = await client.get("/api/v1/alarms/", headers=auth_headers)
    assert response.status_code == 200
    alarms = response.json()
    assert len(alarms) >= 1

    # Step 4: Acknowledge alarm
    ack_data = {
        "comment": "Temperature normalized, acknowledged by operator"
    }

    response = await client.post(
        f"/api/v1/alarms/{alarm_event.id}/acknowledge",
        json=ack_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    ack_alarm = response.json()
    assert ack_alarm["status"] == "ACKNOWLEDGED"
    assert ack_alarm["acknowledgment_comment"] == ack_data["comment"]

    # Step 5: Verify alarm is acknowledged
    response = await client.get(f"/api/v1/alarms/{alarm_event.id}", headers=auth_headers)
    assert response.status_code == 200
    alarm = response.json()
    assert alarm["status"] == "ACKNOWLEDGED"


@pytest.mark.asyncio
async def test_data_collection_flow(client: AsyncClient, test_device, test_tag, auth_headers):
    """
    Test data collection simulation flow
    """

    # Step 1: Verify device exists and is enabled
    response = await client.get(f"/api/v1/devices/{test_device.id}", headers=auth_headers)
    assert response.status_code == 200
    device = response.json()
    assert device["enabled"] == True

    # Step 2: Verify tag exists and is enabled
    response = await client.get(f"/api/v1/tags/{test_tag.id}", headers=auth_headers)
    assert response.status_code == 200
    tag = response.json()
    assert tag["enabled"] == True
    assert tag["log_enabled"] == True

    # Step 3: Simulate data write (would normally come from Gateway)
    # In production, Gateway would write to InfluxDB
    # Here we just verify the tag configuration is correct
    assert tag["data_type"] in ["BOOL", "INT", "FLOAT", "DOUBLE"]
    assert tag["address"] is not None

    # Step 4: Read latest value
    response = await client.get(f"/api/v1/tags/{test_tag.id}/latest", headers=auth_headers)
    assert response.status_code == 200
    latest = response.json()
    assert latest["tag_id"] == str(test_tag.id)


@pytest.mark.asyncio
async def test_user_permissions_flow(client: AsyncClient, test_organization, test_db):
    """
    Test user creation with different permissions
    """

    # Step 1: Create admin user
    admin_data = {
        "username": "admin_user",
        "email": "admin@test.com",
        "password": "adminpass123",
        "full_name": "Admin User",
        "organization_id": str(test_organization.id),
        "is_superuser": True
    }

    response = await client.post("/api/v1/users/", json=admin_data)
    assert response.status_code == 201

    # Step 2: Login as admin
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin_user",
            "password": "adminpass123"
        }
    )
    assert response.status_code == 200
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Step 3: Create regular user
    user_data = {
        "username": "regular_user",
        "email": "regular@test.com",
        "password": "userpass123",
        "full_name": "Regular User",
        "organization_id": str(test_organization.id),
        "is_superuser": False
    }

    response = await client.post("/api/v1/users/", json=user_data, headers=admin_headers)
    assert response.status_code == 201

    # Step 4: Login as regular user
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "regular_user",
            "password": "userpass123"
        }
    )
    assert response.status_code == 200
    user_token = response.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Step 5: Verify both users can access their organization
    response = await client.get(f"/api/v1/organizations/{test_organization.id}", headers=admin_headers)
    assert response.status_code == 200

    response = await client.get(f"/api/v1/organizations/{test_organization.id}", headers=user_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_multi_site_setup(client: AsyncClient, test_organization, auth_headers):
    """
    Test setting up multiple sites with devices
    """

    sites = []
    devices = []

    # Create 3 sites
    for i in range(3):
        site_data = {
            "name": f"Port {i+1}",
            "site_type": "smartport",
            "organization_id": str(test_organization.id),
            "latitude": -23.5505 + i * 0.1,
            "longitude": -46.6333 + i * 0.1,
            "is_active": True
        }

        response = await client.post("/api/v1/sites/", json=site_data, headers=auth_headers)
        assert response.status_code == 201
        sites.append(response.json())

    # Create 2 devices per site
    for site in sites:
        for j in range(2):
            device_data = {
                "name": f"{site['name']} - PLC {j+1}",
                "protocol": "modbus_tcp",
                "ip_address": f"192.168.{sites.index(site)+1}.{j+10}",
                "port": 502,
                "site_id": site["id"],
                "enabled": True,
                "scan_rate": 1000
            }

            response = await client.post("/api/v1/devices/", json=device_data, headers=auth_headers)
            assert response.status_code == 201
            devices.append(response.json())

    # Verify total counts
    assert len(sites) == 3
    assert len(devices) == 6

    # Verify filtering by site
    for site in sites:
        response = await client.get(
            f"/api/v1/devices/?site_id={site['id']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        site_devices = response.json()
        assert len(site_devices) == 2


@pytest.mark.asyncio
async def test_concurrent_requests(client: AsyncClient, test_organization, auth_headers):
    """
    Test handling concurrent requests
    """

    # Create 10 sites concurrently
    async def create_site(index):
        site_data = {
            "name": f"Concurrent Site {index}",
            "site_type": "smartport",
            "organization_id": str(test_organization.id),
            "is_active": True
        }

        response = await client.post("/api/v1/sites/", json=site_data, headers=auth_headers)
        return response.status_code

    # Run 10 concurrent requests
    results = await asyncio.gather(*[create_site(i) for i in range(10)])

    # All should succeed
    assert all(status == 201 for status in results)

    # Verify all were created
    response = await client.get(
        f"/api/v1/sites/?organization_id={test_organization.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    sites = response.json()
    assert len(sites) >= 10
