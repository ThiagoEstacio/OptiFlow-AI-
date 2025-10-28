"""
Site schemas for request/response validation
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator


class SiteBase(BaseModel):
    """Base schema for Site"""
    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    site_type: str = Field(..., description="Type of site: smartport, smartmine, smartsteel")

    # Location
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

    # Timezone
    timezone: Optional[str] = Field(None, description="e.g., America/Sao_Paulo")

    # Status
    is_active: bool = True

    @validator('site_type')
    def validate_site_type(cls, v):
        allowed_types = ['smartport', 'smartmine', 'smartsteel']
        if v not in allowed_types:
            raise ValueError(f'site_type must be one of: {", ".join(allowed_types)}')
        return v


class SiteCreate(SiteBase):
    """Schema for creating a new Site"""
    organization_id: UUID


class SiteUpdate(BaseModel):
    """Schema for updating a Site"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    site_type: Optional[str] = None

    # Location
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

    # Timezone
    timezone: Optional[str] = None

    # Status
    is_active: Optional[bool] = None

    @validator('site_type')
    def validate_site_type(cls, v):
        if v is not None:
            allowed_types = ['smartport', 'smartmine', 'smartsteel']
            if v not in allowed_types:
                raise ValueError(f'site_type must be one of: {", ".join(allowed_types)}')
        return v


class SiteResponse(SiteBase):
    """Schema for Site response"""
    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
