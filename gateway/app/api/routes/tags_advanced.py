"""
Advanced Tag Management API - Enterprise Features
KEPServerEX and Aveva PI inspired tag configuration
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Response
from pydantic import BaseModel
from datetime import datetime
import csv
import io
import json

from app.core.logger import logger
from app.models.tag_config import (
    TagConfig, TagGroup, TagTemplate, DataType, QualityCode,
    ScalingConfig, DeadbandConfig, HistorianConfig, AlarmConfig,
    TagMetadata, PREDEFINED_TEMPLATES
)
from app.services.tag_manager import get_tag_manager


router = APIRouter()


#====================Tag Request/Response Models====================

class TagCreateRequest(BaseModel):
    tag_name: str
    address: str
    data_type: DataType
    adapter_id: str
    enabled: bool = True
    scaling: Optional[ScalingConfig] = None
    deadband: Optional[DeadbandConfig] = None
    historian: Optional[HistorianConfig] = None
    alarm: Optional[AlarmConfig] = None
    metadata: Optional[TagMetadata] = None
    group_path: Optional[str] = None


class TagUpdateRequest(BaseModel):
    tag_name: Optional[str] = None
    enabled: Optional[bool] = None
    scaling: Optional[ScalingConfig] = None
    deadband: Optional[DeadbandConfig] = None
    historian: Optional[HistorianConfig] = None
    alarm: Optional[AlarmConfig] = None
    metadata: Optional[TagMetadata] = None


class TagResponse(BaseModel):
    tag_id: str
    tag_name: str
    address: str
    data_type: DataType
    adapter_id: str
    enabled: bool
    quality: QualityCode
    current_value: Optional[Any] = None
    current_value_timestamp: Optional[str] = None
    scaling: Optional[ScalingConfig] = None
    deadband: Optional[DeadbandConfig] = None
    historian: Optional[HistorianConfig] = None
    alarm: Optional[AlarmConfig] = None
    metadata: Optional[TagMetadata] = None
    group_path: Optional[str] = None
    read_count: int
    error_count: int


# ==================== TAG CRUD ====================

@router.get("/", response_model=List[TagResponse])
async def list_tags(
    adapter_id: Optional[str] = Query(None),
    group_id: Optional[str] = Query(None),
    enabled_only: bool = Query(False),
    historized_only: bool = Query(False),
    search: Optional[str] = Query(None),
    limit: int = Query(1000),
    offset: int = Query(0)
):
    """
    List all enterprise tags with advanced filtering

    Features similar to KEPServerEX tag browser
    """
    tm = get_tag_manager()
    tags = list(tm.tags.values())

    # Apply filters
    if adapter_id:
        tags = [t for t in tags if t.adapter_id == adapter_id]
    if group_id:
        group_tags = await tm.get_tags_by_group(group_id)
        group_tag_ids = {t.tag_id for t in group_tags}
        tags = [t for t in tags if t.tag_id in group_tag_ids]
    if enabled_only:
        tags = [t for t in tags if t.enabled]
    if historized_only:
        tags = [t for t in tags if t.historian.enabled]
    if search:
        search_lower = search.lower()
        tags = [t for t in tags if search_lower in t.tag_name.lower() or search_lower in t.address.lower()]

    total = len(tags)
    tags = tags[offset:offset + limit]

    response = []
    for tag in tags:
        response.append(TagResponse(
            tag_id=tag.tag_id,
            tag_name=tag.tag_name,
            address=tag.address,
            data_type=tag.data_type,
            adapter_id=tag.adapter_id,
            enabled=tag.enabled,
            quality=tag.quality,
            current_value=tag.current_value,
            current_value_timestamp=tag.current_value_timestamp.isoformat() if tag.current_value_timestamp else None,
            scaling=tag.scaling,
            deadband=tag.deadband,
            historian=tag.historian,
            alarm=tag.alarm,
            metadata=tag.metadata,
            group_path=tag.group_path,
            read_count=tag.read_count,
            error_count=tag.error_count
        ))

    return response


@router.post("/", response_model=TagResponse)
async def create_tag(request: TagCreateRequest):
    """
    Create new enterprise tag with full configuration

    Supports: scaling, deadband, historization, alarms
    """
    tm = get_tag_manager()

    import uuid
    tag_id = f"tag_{uuid.uuid4().hex[:8]}"

    tag = TagConfig(
        tag_id=tag_id,
        tag_name=request.tag_name,
        address=request.address,
        data_type=request.data_type,
        protocol_type="",
        adapter_id=request.adapter_id,
        enabled=request.enabled,
        scaling=request.scaling,
        deadband=request.deadband,
        historian=request.historian or HistorianConfig(),
        alarm=request.alarm,
        metadata=request.metadata or TagMetadata(),
        group_path=request.group_path
    )

    try:
        created_tag = await tm.create_tag(tag)

        return TagResponse(
            tag_id=created_tag.tag_id,
            tag_name=created_tag.tag_name,
            address=created_tag.address,
            data_type=created_tag.data_type,
            adapter_id=created_tag.adapter_id,
            enabled=created_tag.enabled,
            quality=created_tag.quality,
            current_value=created_tag.current_value,
            current_value_timestamp=created_tag.current_value_timestamp.isoformat() if created_tag.current_value_timestamp else None,
            scaling=created_tag.scaling,
            deadband=created_tag.deadband,
            historian=created_tag.historian,
            alarm=created_tag.alarm,
            metadata=created_tag.metadata,
            group_path=created_tag.group_path,
            read_count=created_tag.read_count,
            error_count=created_tag.error_count
        )

    except Exception as e:
        logger.error(f"Failed to create tag: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to create tag: {str(e)}")


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: str):
    """Get tag by ID with current value"""
    tm = get_tag_manager()
    tag = await tm.get_tag(tag_id)
    if not tag:
        raise HTTPException(404, f"Tag {tag_id} not found")

    return TagResponse(
        tag_id=tag.tag_id,
        tag_name=tag.tag_name,
        address=tag.address,
        data_type=tag.data_type,
        adapter_id=tag.adapter_id,
        enabled=tag.enabled,
        quality=tag.quality,
        current_value=tag.current_value,
        current_value_timestamp=tag.current_value_timestamp.isoformat() if tag.current_value_timestamp else None,
        scaling=tag.scaling,
        deadband=tag.deadband,
        historian=tag.historian,
        alarm=tag.alarm,
        metadata=tag.metadata,
        group_path=tag.group_path,
        read_count=tag.read_count,
        error_count=tag.error_count
    )


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(tag_id: str, request: TagUpdateRequest):
    """Update tag configuration"""
    tm = get_tag_manager()
    updates = request.dict(exclude_unset=True)

    try:
        updated_tag = await tm.update_tag(tag_id, updates)

        return TagResponse(
            tag_id=updated_tag.tag_id,
            tag_name=updated_tag.tag_name,
            address=updated_tag.address,
            data_type=updated_tag.data_type,
            adapter_id=updated_tag.adapter_id,
            enabled=updated_tag.enabled,
            quality=updated_tag.quality,
            current_value=updated_tag.current_value,
            current_value_timestamp=updated_tag.current_value_timestamp.isoformat() if updated_tag.current_value_timestamp else None,
            scaling=updated_tag.scaling,
            deadband=updated_tag.deadband,
            historian=updated_tag.historian,
            alarm=updated_tag.alarm,
            metadata=updated_tag.metadata,
            group_path=updated_tag.group_path,
            read_count=updated_tag.read_count,
            error_count=updated_tag.error_count
        )

    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Failed to update tag: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to update tag: {str(e)}")


@router.delete("/{tag_id}")
async def delete_tag(tag_id: str):
    """Delete tag"""
    tm = get_tag_manager()

    try:
        await tm.delete_tag(tag_id)
        return {"success": True, "tag_id": tag_id, "message": f"Tag {tag_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Failed to delete tag: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to delete tag: {str(e)}")


# ==================== TEMPLATES ====================

@router.get("/templates/", response_model=List[TagTemplate])
async def list_templates():
    """List all tag templates (predefined + custom)"""
    tm = get_tag_manager()
    return list(tm.templates.values())


@router.get("/templates/predefined")
async def list_predefined_templates():
    """List predefined templates (Temperature, Pressure, Flow, etc)"""
    return {
        "templates": list(PREDEFINED_TEMPLATES.keys()),
        "details": [
            {
                "id": t.template_id,
                "name": t.template_name,
                "description": t.description,
                "data_type": t.data_type
            }
            for t in PREDEFINED_TEMPLATES.values()
        ]
    }


@router.post("/{tag_id}/apply-template/{template_id}")
async def apply_template_to_tag(tag_id: str, template_id: str):
    """Apply template configuration to tag"""
    tm = get_tag_manager()

    try:
        updated_tag = await tm.apply_template(tag_id, template_id)

        return {
            "success": True,
            "tag_id": tag_id,
            "template_id": template_id,
            "message": f"Template {template_id} applied to tag {tag_id}"
        }

    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Failed to apply template: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to apply template: {str(e)}")


# ==================== IMPORT/EXPORT ====================

# TODO: Re-enable after adding python-multipart to requirements
# @router.post("/import/csv")
# async def import_tags_from_csv(
#     file: UploadFile = File(...),
#     adapter_id: str = Query(...),
#     apply_template: Optional[str] = Query(None)
# ):
#     """Import tags from CSV file"""
#     pass


@router.get("/export/csv")
async def export_tags_to_csv(
    adapter_id: Optional[str] = Query(None),
    group_id: Optional[str] = Query(None)
):
    """Export tags to CSV file"""
    tm = get_tag_manager()

    tags = list(tm.tags.values())

    if adapter_id:
        tags = [t for t in tags if t.adapter_id == adapter_id]
    if group_id:
        group_tags = await tm.get_tags_by_group(group_id)
        group_tag_ids = {t.tag_id for t in group_tags}
        tags = [t for t in tags if t.tag_id in group_tag_ids]

    # Create CSV
    output = io.StringIO()
    fieldnames = ['tag_id', 'tag_name', 'address', 'data_type', 'adapter_id', 'enabled',
                  'engineering_units', 'description', 'group_path']
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    for tag in tags:
        writer.writerow({
            'tag_id': tag.tag_id,
            'tag_name': tag.tag_name,
            'address': tag.address,
            'data_type': tag.data_type,
            'adapter_id': tag.adapter_id,
            'enabled': tag.enabled,
            'engineering_units': tag.metadata.engineering_units or '',
            'description': tag.metadata.description or '',
            'group_path': tag.group_path or ''
        })

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=tags_export.csv"}
    )


# ==================== STATISTICS ====================

@router.get("/statistics/overview")
async def get_tag_statistics():
    """Get tag manager statistics"""
    tm = get_tag_manager()
    return tm.get_statistics()


@router.get("/{tag_id}/statistics")
async def get_tag_detailed_statistics(tag_id: str):
    """Get detailed statistics for specific tag"""
    tm = get_tag_manager()
    tag = await tm.get_tag(tag_id)
    if not tag:
        raise HTTPException(404, f"Tag {tag_id} not found")

    return {
        "tag_id": tag_id,
        "tag_name": tag.tag_name,
        "read_count": tag.read_count,
        "error_count": tag.error_count,
        "last_error": tag.last_error,
        "current_value": tag.current_value,
        "current_value_timestamp": tag.current_value_timestamp.isoformat() if tag.current_value_timestamp else None,
        "last_good_value": tag.last_good_value,
        "last_change_timestamp": tag.last_change_timestamp.isoformat() if tag.last_change_timestamp else None,
        "quality": tag.quality,
        "uptime_hours": (datetime.utcnow() - tag.created_at).total_seconds() / 3600 if tag.created_at else 0,
        "error_rate": f"{(tag.error_count / max(tag.read_count, 1)) * 100:.2f}%"
    }
