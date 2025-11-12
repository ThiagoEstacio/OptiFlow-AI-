"""
Alarm schemas for request/response validation
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, validator


class AlarmDefinitionBase(BaseModel):
    """Base schema for Alarm Definition"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    alarm_type: str = Field(..., description="Type: HIGH_LIMIT, LOW_LIMIT, RATE_OF_CHANGE, DEVIATION, etc")
    severity: str = Field(..., description="Severity: CRITICAL, HIGH, MEDIUM, LOW")

    # Thresholds
    high_limit: Optional[float] = None
    low_limit: Optional[float] = None
    deadband: Optional[float] = Field(None, description="Hysteresis")
    delay_seconds: Optional[int] = Field(0, ge=0, description="Delay before triggering")

    # Notifications
    email_enabled: bool = False
    email_recipients: Optional[List[str]] = Field(default_factory=list)
    sms_enabled: bool = False
    sms_recipients: Optional[List[str]] = Field(default_factory=list)

    # Status
    enabled: bool = True

    @validator('alarm_type')
    def validate_alarm_type(cls, v):
        allowed_types = ['HIGH_LIMIT', 'LOW_LIMIT', 'RATE_OF_CHANGE', 'DEVIATION', 'PREDICTIVE', 'CUSTOM']
        if v not in allowed_types:
            raise ValueError(f'alarm_type must be one of: {", ".join(allowed_types)}')
        return v

    @validator('severity')
    def validate_severity(cls, v):
        allowed_severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        if v not in allowed_severities:
            raise ValueError(f'severity must be one of: {", ".join(allowed_severities)}')
        return v


class AlarmDefinitionCreate(AlarmDefinitionBase):
    """Schema for creating a new Alarm Definition"""
    tag_id: UUID


class AlarmDefinitionUpdate(BaseModel):
    """Schema for updating an Alarm Definition"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    alarm_type: Optional[str] = None
    severity: Optional[str] = None

    # Thresholds
    high_limit: Optional[float] = None
    low_limit: Optional[float] = None
    deadband: Optional[float] = None
    delay_seconds: Optional[int] = Field(None, ge=0)

    # Notifications
    email_enabled: Optional[bool] = None
    email_recipients: Optional[List[str]] = None
    sms_enabled: Optional[bool] = None
    sms_recipients: Optional[List[str]] = None

    # Status
    enabled: Optional[bool] = None


class AlarmDefinitionResponse(AlarmDefinitionBase):
    """Schema for Alarm Definition response"""
    id: UUID
    tag_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlarmEventBase(BaseModel):
    """Base schema for Alarm Event"""
    message: str
    severity: str
    value: Optional[float] = None


class AlarmEventResponse(BaseModel):
    """Schema for Alarm Event response"""
    id: UUID
    definition_id: UUID
    state: str  # ACTIVE, ACKNOWLEDGED, CLEARED
    trigger_value: Optional[float] = None
    trigger_timestamp: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[UUID] = None
    acknowledgment_comment: Optional[str] = None
    cleared_at: Optional[datetime] = None
    clear_value: Optional[float] = None
    duration_seconds: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlarmEventEnrichedResponse(AlarmEventResponse):
    """
    ✨ Enriched Alarm Event response with data from AlarmDefinition

    This schema includes additional fields from the alarm definition:
    - severity: The severity level (CRITICAL, HIGH, MEDIUM, LOW)
    - alarm_name: The name of the alarm definition
    - alarm_type: The type of alarm (HIGH_LIMIT, LOW_LIMIT, etc)
    - tag_id: The associated tag ID
    """
    # Fields from AlarmDefinition
    severity: str = Field(..., description="Severity from definition: CRITICAL, HIGH, MEDIUM, LOW")
    alarm_name: str = Field(..., description="Name of the alarm definition")
    alarm_type: str = Field(..., description="Type of alarm from definition")
    tag_id: UUID = Field(..., description="Associated tag ID from definition")

    # Optional definition fields
    description: Optional[str] = Field(None, description="Description from definition")
    high_limit: Optional[float] = Field(None, description="High limit threshold")
    low_limit: Optional[float] = Field(None, description="Low limit threshold")


class AlarmAcknowledgeRequest(BaseModel):
    """Schema for acknowledging an alarm"""
    comment: Optional[str] = Field(None, max_length=500)
