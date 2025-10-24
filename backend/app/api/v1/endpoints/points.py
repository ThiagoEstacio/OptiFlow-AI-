"""
Point Builder API Endpoints

Endpoints for managing Point Templates and Point Configurations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.api.deps import get_db
from app.models import PointTemplate, PointConfiguration, Tag
from app.schemas.point_config import (
    PointTemplateCreate,
    PointTemplateUpdate,
    PointTemplateResponse,
    PointConfigurationCreate,
    PointConfigurationUpdate,
    PointConfigurationResponse,
    PointConfigurationWithStats,
    ApplyTemplateRequest,
    ApplyTemplateResponse,
    BulkCreatePointConfigRequest,
    BulkCreatePointConfigResponse,
    PointValidationRequest,
    PointValidationResponse,
    PointConfigurationStats,
)
from app.services.point_validation import PointValidator

router = APIRouter()
validator = PointValidator()


# ============================================================================
# Point Template Endpoints
# ============================================================================

@router.post("/templates", response_model=PointTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_point_template(
    template: PointTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new Point Template.

    Point Templates allow you to define reusable configurations for multiple points.
    """
    # Validate template configuration
    db_template = PointTemplate(**template.dict())
    validation_result = validator.validate_point_template(db_template)

    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Template validation failed",
                "errors": [e.to_dict() for e in validation_result.errors]
            }
        )

    # Create template
    db.add(db_template)
    db.commit()
    db.refresh(db_template)

    return db_template


@router.get("/templates", response_model=List[PointTemplateResponse])
def list_point_templates(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    List Point Templates with optional filters.
    """
    query = db.query(PointTemplate)

    # Apply filters
    if organization_id:
        query = query.filter(PointTemplate.organization_id == organization_id)
    if is_active is not None:
        query = query.filter(PointTemplate.is_active == is_active)
    if category:
        query = query.filter(PointTemplate.category == category)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (PointTemplate.name.ilike(search_pattern)) |
            (PointTemplate.description.ilike(search_pattern))
        )

    # Apply pagination
    templates = query.offset(skip).limit(limit).all()

    return templates


@router.get("/templates/{template_id}", response_model=PointTemplateResponse)
def get_point_template(
    template_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a Point Template by ID.
    """
    template = db.query(PointTemplate).filter(PointTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Point Template {template_id} not found"
        )

    return template


@router.put("/templates/{template_id}", response_model=PointTemplateResponse)
def update_point_template(
    template_id: UUID,
    template_update: PointTemplateUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a Point Template.
    """
    # Get existing template
    db_template = db.query(PointTemplate).filter(PointTemplate.id == template_id).first()

    if not db_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Point Template {template_id} not found"
        )

    # Update fields
    update_data = template_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_template, field, value)

    # Validate updated template
    validation_result = validator.validate_point_template(db_template)

    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Template validation failed",
                "errors": [e.to_dict() for e in validation_result.errors]
            }
        )

    db.commit()
    db.refresh(db_template)

    return db_template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_point_template(
    template_id: UUID,
    force: bool = Query(False, description="Force delete even if in use"),
    db: Session = Depends(get_db)
):
    """
    Delete a Point Template.

    By default, templates in use cannot be deleted unless force=true.
    """
    template = db.query(PointTemplate).filter(PointTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Point Template {template_id} not found"
        )

    # Check if template is in use
    if not force and template.usage_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template is in use by {template.usage_count} point(s). Use force=true to delete anyway."
        )

    db.delete(template)
    db.commit()


# ============================================================================
# Point Configuration Endpoints
# ============================================================================

@router.post("/configurations", response_model=PointConfigurationResponse, status_code=status.HTTP_201_CREATED)
def create_point_configuration(
    config: PointConfigurationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a Point Configuration for a Tag.

    Point Configurations extend Tags with compression, historian, and validation settings.
    """
    # Check if tag exists
    tag = db.query(Tag).filter(Tag.id == config.tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag {config.tag_id} not found"
        )

    # Check if configuration already exists
    existing = db.query(PointConfiguration).filter(
        PointConfiguration.tag_id == config.tag_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Point Configuration already exists for tag {config.tag_id}"
        )

    # Create configuration
    db_config = PointConfiguration(**config.dict())

    # Validate configuration
    validation_result = validator.validate_point_configuration(db_config, tag)

    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Configuration validation failed",
                "errors": [e.to_dict() for e in validation_result.errors],
                "warnings": [w.to_dict() for w in validation_result.warnings]
            }
        )

    # Update template usage count if using template
    if config.template_id:
        template = db.query(PointTemplate).filter(PointTemplate.id == config.template_id).first()
        if template:
            template.usage_count += 1

    db.add(db_config)
    db.commit()
    db.refresh(db_config)

    return db_config


@router.get("/configurations", response_model=List[PointConfigurationResponse])
def list_point_configurations(
    tag_id: Optional[UUID] = Query(None, description="Filter by tag ID"),
    template_id: Optional[UUID] = Query(None, description="Filter by template ID"),
    compression_enabled: Optional[bool] = Query(None, description="Filter by compression status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    List Point Configurations with optional filters.
    """
    query = db.query(PointConfiguration)

    # Apply filters
    if tag_id:
        query = query.filter(PointConfiguration.tag_id == tag_id)
    if template_id:
        query = query.filter(PointConfiguration.template_id == template_id)
    if compression_enabled is not None:
        query = query.filter(PointConfiguration.compression_enabled == compression_enabled)

    # Apply pagination
    configurations = query.offset(skip).limit(limit).all()

    return configurations


@router.get("/configurations/{config_id}", response_model=PointConfigurationWithStats)
def get_point_configuration(
    config_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a Point Configuration by ID with statistics.
    """
    config = db.query(PointConfiguration).filter(PointConfiguration.id == config_id).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Point Configuration {config_id} not found"
        )

    # Add calculated statistics
    response = PointConfigurationWithStats.from_orm(config)
    response.compression_ratio_percent = config.get_compression_ratio_percent()
    response.write_success_rate = config.get_write_success_rate()

    return response


@router.get("/configurations/by-tag/{tag_id}", response_model=PointConfigurationWithStats)
def get_point_configuration_by_tag(
    tag_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get Point Configuration for a specific Tag.
    """
    config = db.query(PointConfiguration).filter(PointConfiguration.tag_id == tag_id).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Point Configuration not found for tag {tag_id}"
        )

    # Add calculated statistics
    response = PointConfigurationWithStats.from_orm(config)
    response.compression_ratio_percent = config.get_compression_ratio_percent()
    response.write_success_rate = config.get_write_success_rate()

    return response


@router.put("/configurations/{config_id}", response_model=PointConfigurationResponse)
def update_point_configuration(
    config_id: UUID,
    config_update: PointConfigurationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a Point Configuration.
    """
    # Get existing configuration
    db_config = db.query(PointConfiguration).filter(PointConfiguration.id == config_id).first()

    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Point Configuration {config_id} not found"
        )

    # Get associated tag for validation
    tag = db.query(Tag).filter(Tag.id == db_config.tag_id).first()

    # Handle template change
    old_template_id = db_config.template_id
    new_template_id = config_update.template_id

    # Update fields
    update_data = config_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_config, field, value)

    # Validate updated configuration
    validation_result = validator.validate_point_configuration(db_config, tag)

    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Configuration validation failed",
                "errors": [e.to_dict() for e in validation_result.errors],
                "warnings": [w.to_dict() for w in validation_result.warnings]
            }
        )

    # Update template usage counts
    if old_template_id != new_template_id:
        if old_template_id:
            old_template = db.query(PointTemplate).filter(PointTemplate.id == old_template_id).first()
            if old_template and old_template.usage_count > 0:
                old_template.usage_count -= 1

        if new_template_id:
            new_template = db.query(PointTemplate).filter(PointTemplate.id == new_template_id).first()
            if new_template:
                new_template.usage_count += 1

    db.commit()
    db.refresh(db_config)

    return db_config


@router.delete("/configurations/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_point_configuration(
    config_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a Point Configuration.
    """
    config = db.query(PointConfiguration).filter(PointConfiguration.id == config_id).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Point Configuration {config_id} not found"
        )

    # Update template usage count
    if config.template_id:
        template = db.query(PointTemplate).filter(PointTemplate.id == config.template_id).first()
        if template and template.usage_count > 0:
            template.usage_count -= 1

    db.delete(config)
    db.commit()


# ============================================================================
# Batch Operations
# ============================================================================

@router.post("/templates/{template_id}/apply", response_model=ApplyTemplateResponse)
def apply_template_to_tags(
    template_id: UUID,
    request: ApplyTemplateRequest,
    db: Session = Depends(get_db)
):
    """
    Apply a template to multiple tags.

    Creates or updates Point Configurations for the specified tags.
    """
    # Get template
    template = db.query(PointTemplate).filter(PointTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Point Template {template_id} not found"
        )

    applied_count = 0
    skipped_count = 0
    errors = []

    for tag_id in request.tag_ids:
        try:
            # Check if tag exists
            tag = db.query(Tag).filter(Tag.id == tag_id).first()
            if not tag:
                errors.append({
                    "tag_id": str(tag_id),
                    "error": "Tag not found"
                })
                continue

            # Check if configuration exists
            existing_config = db.query(PointConfiguration).filter(
                PointConfiguration.tag_id == tag_id
            ).first()

            if existing_config and not request.override_existing:
                skipped_count += 1
                continue

            # Create or update configuration from template
            if existing_config:
                # Update existing
                existing_config.template_id = template_id
                existing_config.compression_enabled = template.compression_enabled
                existing_config.compression_type = template.compression_type
                existing_config.compression_config = template.compression_config
                existing_config.historian_enabled = template.historian_enabled
                existing_config.historian_type = template.historian_type
                existing_config.historian_config = template.historian_config
            else:
                # Create new
                new_config = PointConfiguration(
                    tag_id=tag_id,
                    template_id=template_id,
                    compression_enabled=template.compression_enabled,
                    compression_type=template.compression_type,
                    compression_config=template.compression_config,
                    historian_enabled=template.historian_enabled,
                    historian_type=template.historian_type,
                    historian_config=template.historian_config
                )
                db.add(new_config)

            applied_count += 1

        except Exception as e:
            errors.append({
                "tag_id": str(tag_id),
                "error": str(e)
            })

    # Update template usage count
    if applied_count > 0:
        template.usage_count = db.query(PointConfiguration).filter(
            PointConfiguration.template_id == template_id
        ).count()

    db.commit()

    return ApplyTemplateResponse(
        success=len(errors) == 0,
        applied_count=applied_count,
        skipped_count=skipped_count,
        errors=errors
    )


@router.post("/configurations/bulk", response_model=BulkCreatePointConfigResponse)
def bulk_create_point_configurations(
    request: BulkCreatePointConfigRequest,
    db: Session = Depends(get_db)
):
    """
    Create multiple Point Configurations in one request.
    """
    created_count = 0
    failed_count = 0
    created_ids = []
    errors = []

    for config_data in request.configurations:
        try:
            # Check if tag exists
            tag = db.query(Tag).filter(Tag.id == config_data.tag_id).first()
            if not tag:
                raise ValueError(f"Tag {config_data.tag_id} not found")

            # Check if configuration already exists
            existing = db.query(PointConfiguration).filter(
                PointConfiguration.tag_id == config_data.tag_id
            ).first()

            if existing:
                raise ValueError(f"Configuration already exists for tag {config_data.tag_id}")

            # Create configuration
            db_config = PointConfiguration(**config_data.dict())

            # Validate
            validation_result = validator.validate_point_configuration(db_config, tag)

            if not validation_result.is_valid:
                error_messages = [e.message for e in validation_result.errors]
                raise ValueError(f"Validation failed: {'; '.join(error_messages)}")

            # Update template usage
            if config_data.template_id:
                template = db.query(PointTemplate).filter(
                    PointTemplate.id == config_data.template_id
                ).first()
                if template:
                    template.usage_count += 1

            db.add(db_config)
            db.flush()

            created_ids.append(db_config.id)
            created_count += 1

        except Exception as e:
            failed_count += 1
            errors.append({
                "tag_id": str(config_data.tag_id),
                "error": str(e)
            })

    db.commit()

    return BulkCreatePointConfigResponse(
        success=failed_count == 0,
        created_count=created_count,
        failed_count=failed_count,
        created_ids=created_ids,
        errors=errors
    )


# ============================================================================
# Validation Endpoints
# ============================================================================

@router.post("/validate", response_model=PointValidationResponse)
def validate_point_configuration(
    request: PointValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Validate a Point Configuration without saving.

    Useful for pre-validation in UI before creating/updating.
    """
    # Get tag
    tag = db.query(Tag).filter(Tag.id == request.tag_id).first()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag {request.tag_id} not found"
        )

    # Validate tag
    tag_result = validator.validate_tag(tag)

    # Validate configuration if provided
    if request.configuration:
        temp_config = PointConfiguration(
            tag_id=request.tag_id,
            **request.configuration.dict()
        )
        config_result = validator.validate_point_configuration(temp_config, tag)

        # Merge results
        tag_result.errors.extend(config_result.errors)
        tag_result.warnings.extend(config_result.warnings)
        if not config_result.is_valid:
            tag_result.is_valid = False

    return PointValidationResponse(
        is_valid=tag_result.is_valid,
        errors=[e.to_dict() for e in tag_result.errors],
        warnings=[w.to_dict() for w in tag_result.warnings]
    )


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get("/configurations/{config_id}/stats", response_model=PointConfigurationStats)
def get_point_configuration_stats(
    config_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get detailed statistics for a Point Configuration.
    """
    config = db.query(PointConfiguration).filter(PointConfiguration.id == config_id).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Point Configuration {config_id} not found"
        )

    # Build statistics response
    compression_stats = None
    if config.compression_enabled:
        from app.schemas.point_config import CompressionStats
        compression_stats = CompressionStats(
            algorithm=config.compression_type.value,
            samples_received=config.total_samples_received,
            samples_stored=config.total_samples_stored,
            compression_ratio_percent=config.get_compression_ratio_percent(),
            config=config.compression_config
        )

    historian_stats = None
    if config.historian_enabled:
        from app.schemas.point_config import HistorianStats
        historian_stats = HistorianStats(
            historian_type=config.historian_type.value,
            total_writes=config.total_writes,
            write_errors=config.write_errors,
            write_success_rate=config.get_write_success_rate(),
            last_write_timestamp=config.last_write_timestamp
        )

    return PointConfigurationStats(
        point_config_id=config.id,
        tag_id=config.tag_id,
        compression_stats=compression_stats,
        historian_stats=historian_stats,
        avg_processing_time_ms=config.avg_processing_time_ms
    )
