"""
Alarm endpoint tests
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime


@pytest.mark.asyncio
async def test_create_alarm_definition(client: AsyncClient, test_tag, auth_headers):
    """Test creating an alarm definition"""
    alarm_data = {
        "name": "High Temperature Alarm",
        "alarm_type": "HIGH_LIMIT",
        "severity": "HIGH",
        "tag_id": str(test_tag.id),
        "high_limit": 80.0,
        "enabled": True,
        "message": "Temperature exceeded 80°C"
    }

    response = await client.post(
        "/api/v1/alarms/definitions",
        json=alarm_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "High Temperature Alarm"
    assert data["alarm_type"] == "HIGH_LIMIT"
    assert data["severity"] == "HIGH"
    assert data["high_limit"] == 80.0
    assert "id" in data


@pytest.mark.asyncio
async def test_list_alarm_definitions(client: AsyncClient, auth_headers):
    """Test listing alarm definitions"""
    response = await client.get(
        "/api/v1/alarms/definitions",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_alarm_definition_by_id(client: AsyncClient, test_tag, auth_headers):
    """Test getting alarm definition by ID"""
    # First create an alarm definition
    alarm_data = {
        "name": "Low Pressure Alarm",
        "alarm_type": "LOW_LIMIT",
        "severity": "MEDIUM",
        "tag_id": str(test_tag.id),
        "low_limit": 2.0,
        "enabled": True
    }

    create_response = await client.post(
        "/api/v1/alarms/definitions",
        json=alarm_data,
        headers=auth_headers
    )
    assert create_response.status_code == 201
    alarm_id = create_response.json()["id"]

    # Now get it
    response = await client.get(
        f"/api/v1/alarms/definitions/{alarm_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == alarm_id
    assert data["name"] == "Low Pressure Alarm"
    assert data["severity"] == "MEDIUM"


@pytest.mark.asyncio
async def test_update_alarm_definition(client: AsyncClient, test_tag, auth_headers):
    """Test updating an alarm definition"""
    # Create alarm definition
    alarm_data = {
        "name": "Original Alarm",
        "alarm_type": "HIGH_LIMIT",
        "severity": "LOW",
        "tag_id": str(test_tag.id),
        "high_limit": 50.0,
        "enabled": True
    }

    create_response = await client.post(
        "/api/v1/alarms/definitions",
        json=alarm_data,
        headers=auth_headers
    )
    alarm_id = create_response.json()["id"]

    # Update it
    update_data = {
        "name": "Updated Alarm",
        "severity": "CRITICAL",
        "high_limit": 75.0
    }

    response = await client.put(
        f"/api/v1/alarms/definitions/{alarm_id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Alarm"
    assert data["severity"] == "CRITICAL"
    assert data["high_limit"] == 75.0


@pytest.mark.asyncio
async def test_delete_alarm_definition(client: AsyncClient, test_tag, auth_headers):
    """Test deleting an alarm definition"""
    # Create alarm definition
    alarm_data = {
        "name": "To Be Deleted",
        "alarm_type": "HIGH_LIMIT",
        "severity": "LOW",
        "tag_id": str(test_tag.id),
        "high_limit": 60.0,
        "enabled": True
    }

    create_response = await client.post(
        "/api/v1/alarms/definitions",
        json=alarm_data,
        headers=auth_headers
    )
    alarm_id = create_response.json()["id"]

    # Delete it
    response = await client.delete(
        f"/api/v1/alarms/definitions/{alarm_id}",
        headers=auth_headers
    )

    assert response.status_code == 204

    # Verify it's deleted
    get_response = await client.get(
        f"/api/v1/alarms/definitions/{alarm_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_create_alarm_definition_invalid_severity(client: AsyncClient, test_tag, auth_headers):
    """Test creating alarm definition with invalid severity"""
    alarm_data = {
        "name": "Invalid Alarm",
        "alarm_type": "HIGH_LIMIT",
        "severity": "INVALID_SEVERITY",  # Invalid
        "tag_id": str(test_tag.id),
        "high_limit": 50.0,
        "enabled": True
    }

    response = await client.post(
        "/api/v1/alarms/definitions",
        json=alarm_data,
        headers=auth_headers
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_acknowledge_active_alarm(client: AsyncClient, test_db, test_tag, auth_headers):
    """Test acknowledging an active alarm"""
    # First need to create an alarm event in the database
    from app.models.alarm import AlarmEvent

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

    # Now acknowledge it
    ack_data = {
        "comment": "Acknowledged by operator"
    }

    response = await client.post(
        f"/api/v1/alarms/{alarm_event.id}/acknowledge",
        json=ack_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACKNOWLEDGED"
    assert data["acknowledgment_comment"] == "Acknowledged by operator"
    assert data["acknowledged_at"] is not None


@pytest.mark.asyncio
async def test_acknowledge_non_active_alarm(client: AsyncClient, test_db, test_tag, auth_headers):
    """Test acknowledging a non-active alarm (should fail)"""
    from app.models.alarm import AlarmEvent

    # Create an alarm event that's already cleared
    alarm_event = AlarmEvent(
        id=uuid4(),
        tag_id=test_tag.id,
        alarm_type="HIGH_LIMIT",
        severity="HIGH",
        message="Temperature exceeded limit",
        value=85.0,
        limit=80.0,
        status="CLEARED",  # Not active
        triggered_at=datetime.utcnow()
    )
    test_db.add(alarm_event)
    await test_db.commit()
    await test_db.refresh(alarm_event)

    # Try to acknowledge it
    ack_data = {
        "comment": "Should not work"
    }

    response = await client.post(
        f"/api/v1/alarms/{alarm_event.id}/acknowledge",
        json=ack_data,
        headers=auth_headers
    )

    assert response.status_code == 400
    assert "not in ACTIVE state" in response.json()["detail"]


@pytest.mark.asyncio
async def test_acknowledge_nonexistent_alarm(client: AsyncClient, auth_headers):
    """Test acknowledging non-existent alarm"""
    fake_id = uuid4()
    ack_data = {
        "comment": "Test comment"
    }

    response = await client.post(
        f"/api/v1/alarms/{fake_id}/acknowledge",
        json=ack_data,
        headers=auth_headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_alarm_event_by_id(client: AsyncClient, test_db, test_tag, auth_headers):
    """Test getting alarm event by ID"""
    from app.models.alarm import AlarmEvent

    alarm_event = AlarmEvent(
        id=uuid4(),
        tag_id=test_tag.id,
        alarm_type="HIGH_LIMIT",
        severity="CRITICAL",
        message="Critical temperature",
        value=95.0,
        limit=80.0,
        status="ACTIVE",
        triggered_at=datetime.utcnow()
    )
    test_db.add(alarm_event)
    await test_db.commit()
    await test_db.refresh(alarm_event)

    response = await client.get(
        f"/api/v1/alarms/{alarm_event.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(alarm_event.id)
    assert data["severity"] == "CRITICAL"
    assert data["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_filter_alarms_by_severity(client: AsyncClient, auth_headers):
    """Test filtering alarms by severity"""
    response = await client.get(
        "/api/v1/alarms/?severity=CRITICAL",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
