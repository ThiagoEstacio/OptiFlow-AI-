"""
Annotation API Endpoints

Provides REST API for managing annotations on time-series data.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from app.api.deps import get_db
from app.models.annotation import Annotation, AnnotationType, AnnotationSeverity
from app.models.tag import Tag
from app.models.device import Device
from app.models.organization import Site
from app.schemas.annotation import (
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationResponse,
    AnnotationListResponse,
    AnnotationQuery,
    AnnotationBulkCreate,
    AnnotationStatistics,
)
from loguru import logger

router = APIRouter()


# ==================== Helper Functions ====================

def _build_annotation_query(db: Session, query_params: AnnotationQuery):
    """Build SQLAlchemy query from query parameters"""
    query = db.query(Annotation)

    # Filter by deleted status
    if not query_params.include_deleted:
        query = query.filter(Annotation.is_deleted == False)

    # Filter by tag IDs
    if query_params.tag_ids:
        query = query.filter(Annotation.tag_id.in_(query_params.tag_ids))

    # Filter by device IDs
    if query_params.device_ids:
        query = query.filter(Annotation.device_id.in_(query_params.device_ids))

    # Filter by site IDs
    if query_params.site_ids:
        query = query.filter(Annotation.site_id.in_(query_params.site_ids))

    # Filter by annotation types
    if query_params.annotation_types:
        query = query.filter(Annotation.annotation_type.in_(query_params.annotation_types))

    # Filter by severities
    if query_params.severities:
        query = query.filter(Annotation.severity.in_(query_params.severities))

    # Filter by time range
    if query_params.start_time:
        query = query.filter(Annotation.start_time >= query_params.start_time)
    if query_params.end_time:
        query = query.filter(Annotation.start_time <= query_params.end_time)

    # Filter by creator
    if query_params.created_by:
        query = query.filter(Annotation.created_by == query_params.created_by)

    # Filter by visibility
    if query_params.is_public is not None:
        query = query.filter(Annotation.is_public == query_params.is_public)

    # Filter pinned only
    if query_params.pinned_only:
        query = query.filter(Annotation.pinned == True)

    # Search in title and content
    if query_params.search:
        search_term = f"%{query_params.search}%"
        query = query.filter(
            or_(
                Annotation.title.ilike(search_term),
                Annotation.content.ilike(search_term)
            )
        )

    return query


def _apply_ordering(query, order_by: str, order_direction: str):
    """Apply ordering to query"""
    order_func = desc if order_direction == 'desc' else asc

    if order_by == 'start_time':
        query = query.order_by(order_func(Annotation.start_time))
    elif order_by == 'created_at':
        query = query.order_by(order_func(Annotation.created_at))
    elif order_by == 'updated_at':
        query = query.order_by(order_func(Annotation.updated_at))
    elif order_by == 'title':
        query = query.order_by(order_func(Annotation.title))
    elif order_by == 'severity':
        query = query.order_by(order_func(Annotation.severity))

    return query


# ==================== Create Endpoints ====================

@router.post("/", response_model=AnnotationResponse, status_code=status.HTTP_201_CREATED)
async def create_annotation(
    annotation: AnnotationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new annotation.

    - **annotation_type**: Type of annotation (comment, event, alarm, etc.)
    - **severity**: Severity level (info, warning, error, critical)
    - **title**: Annotation title (required)
    - **content**: Annotation content (optional, supports Markdown)
    - **start_time**: Start timestamp (required)
    - **end_time**: End timestamp (optional, for range annotations)
    - **tag_id**: Associated tag ID (optional)
    - **device_id**: Associated device ID (optional)
    - **site_id**: Associated site ID (optional)
    """
    logger.info(f"Creating annotation: {annotation.title}")

    # Validate references exist
    if annotation.tag_id:
        tag = db.query(Tag).filter(Tag.id == annotation.tag_id).first()
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag {annotation.tag_id} not found"
            )

    if annotation.device_id:
        device = db.query(Device).filter(Device.id == annotation.device_id).first()
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {annotation.device_id} not found"
            )

    if annotation.site_id:
        site = db.query(Site).filter(Site.id == annotation.site_id).first()
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Site {annotation.site_id} not found"
            )

    # Create annotation
    db_annotation = Annotation(**annotation.dict())
    db.add(db_annotation)
    db.commit()
    db.refresh(db_annotation)

    logger.info(f"Annotation created: {db_annotation.id}")
    return db_annotation


@router.post("/bulk", response_model=List[AnnotationResponse], status_code=status.HTTP_201_CREATED)
async def create_annotations_bulk(
    bulk_create: AnnotationBulkCreate,
    db: Session = Depends(get_db)
):
    """
    Create multiple annotations in bulk.

    Maximum 100 annotations per request.
    """
    logger.info(f"Creating {len(bulk_create.annotations)} annotations in bulk")

    created_annotations = []

    for annotation_data in bulk_create.annotations:
        # Validate references (basic check)
        if annotation_data.tag_id:
            tag = db.query(Tag).filter(Tag.id == annotation_data.tag_id).first()
            if not tag:
                logger.warning(f"Tag {annotation_data.tag_id} not found, skipping annotation")
                continue

        db_annotation = Annotation(**annotation_data.dict())
        db.add(db_annotation)
        created_annotations.append(db_annotation)

    db.commit()

    # Refresh all created annotations
    for annotation in created_annotations:
        db.refresh(annotation)

    logger.info(f"Created {len(created_annotations)} annotations")
    return created_annotations


# ==================== Read Endpoints ====================

@router.get("/", response_model=AnnotationListResponse)
async def list_annotations(
    tag_ids: Optional[List[UUID]] = Query(None),
    device_ids: Optional[List[UUID]] = Query(None),
    site_ids: Optional[List[UUID]] = Query(None),
    annotation_types: Optional[List[AnnotationType]] = Query(None),
    severities: Optional[List[AnnotationSeverity]] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    created_by: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    pinned_only: bool = Query(False),
    include_deleted: bool = Query(False),
    search: Optional[str] = Query(None, max_length=255),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("start_time"),
    order_direction: str = Query("desc"),
    db: Session = Depends(get_db)
):
    """
    List annotations with filtering, pagination, and sorting.

    **Filters:**
    - tag_ids: Filter by tag IDs
    - device_ids: Filter by device IDs
    - site_ids: Filter by site IDs
    - annotation_types: Filter by types
    - severities: Filter by severity levels
    - start_time, end_time: Filter by time range
    - created_by: Filter by creator
    - is_public: Filter by visibility
    - pinned_only: Show only pinned annotations
    - search: Search in title and content

    **Pagination:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)

    **Sorting:**
    - order_by: Field to sort by (start_time, created_at, updated_at, title, severity)
    - order_direction: Sort direction (asc, desc)
    """
    query_params = AnnotationQuery(
        tag_ids=tag_ids,
        device_ids=device_ids,
        site_ids=site_ids,
        annotation_types=annotation_types,
        severities=severities,
        start_time=start_time,
        end_time=end_time,
        created_by=created_by,
        is_public=is_public,
        pinned_only=pinned_only,
        include_deleted=include_deleted,
        search=search,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_direction=order_direction
    )

    # Build query
    query = _build_annotation_query(db, query_params)

    # Get total count
    total = query.count()

    # Apply ordering
    query = _apply_ordering(query, order_by, order_direction)

    # Apply pagination
    offset = (page - 1) * page_size
    annotations = query.offset(offset).limit(page_size).all()

    return AnnotationListResponse(
        total=total,
        page=page,
        page_size=page_size,
        annotations=annotations
    )


@router.get("/{annotation_id}", response_model=AnnotationResponse)
async def get_annotation(
    annotation_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific annotation by ID.
    """
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()

    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Annotation {annotation_id} not found"
        )

    return annotation


@router.get("/tag/{tag_id}", response_model=AnnotationListResponse)
async def get_annotations_by_tag(
    tag_id: UUID,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    annotation_types: Optional[List[AnnotationType]] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all annotations for a specific tag.

    Useful for displaying annotations on trend charts.
    """
    # Verify tag exists
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag {tag_id} not found"
        )

    query = db.query(Annotation).filter(
        Annotation.tag_id == tag_id,
        Annotation.is_deleted == False
    )

    # Apply time filter
    if start_time:
        query = query.filter(Annotation.start_time >= start_time)
    if end_time:
        query = query.filter(Annotation.start_time <= end_time)

    # Apply type filter
    if annotation_types:
        query = query.filter(Annotation.annotation_type.in_(annotation_types))

    # Get total
    total = query.count()

    # Order by start time
    query = query.order_by(desc(Annotation.start_time))

    # Paginate
    offset = (page - 1) * page_size
    annotations = query.offset(offset).limit(page_size).all()

    return AnnotationListResponse(
        total=total,
        page=page,
        page_size=page_size,
        annotations=annotations
    )


# ==================== Update Endpoints ====================

@router.put("/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    annotation_id: UUID,
    annotation_update: AnnotationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing annotation.

    Only provided fields will be updated.
    """
    db_annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()

    if not db_annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Annotation {annotation_id} not found"
        )

    # Update fields
    update_data = annotation_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_annotation, field, value)

    db_annotation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_annotation)

    logger.info(f"Annotation updated: {annotation_id}")
    return db_annotation


@router.patch("/{annotation_id}/pin", response_model=AnnotationResponse)
async def toggle_pin_annotation(
    annotation_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Toggle the pinned status of an annotation.
    """
    db_annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()

    if not db_annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Annotation {annotation_id} not found"
        )

    db_annotation.pinned = not db_annotation.pinned
    db_annotation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_annotation)

    logger.info(f"Annotation {annotation_id} pinned status: {db_annotation.pinned}")
    return db_annotation


# ==================== Delete Endpoints ====================

@router.delete("/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_annotation(
    annotation_id: UUID,
    soft_delete: bool = Query(True, description="Soft delete (mark as deleted) or hard delete"),
    db: Session = Depends(get_db)
):
    """
    Delete an annotation.

    - **soft_delete=True**: Mark as deleted (default)
    - **soft_delete=False**: Permanently delete from database
    """
    db_annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()

    if not db_annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Annotation {annotation_id} not found"
        )

    if soft_delete:
        # Soft delete
        db_annotation.is_deleted = True
        db_annotation.deleted_at = datetime.utcnow()
        db.commit()
        logger.info(f"Annotation {annotation_id} soft deleted")
    else:
        # Hard delete
        db.delete(db_annotation)
        db.commit()
        logger.info(f"Annotation {annotation_id} permanently deleted")

    return None


@router.post("/{annotation_id}/restore", response_model=AnnotationResponse)
async def restore_annotation(
    annotation_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Restore a soft-deleted annotation.
    """
    db_annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()

    if not db_annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Annotation {annotation_id} not found"
        )

    if not db_annotation.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Annotation {annotation_id} is not deleted"
        )

    db_annotation.is_deleted = False
    db_annotation.deleted_at = None
    db_annotation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_annotation)

    logger.info(f"Annotation {annotation_id} restored")
    return db_annotation


# ==================== Statistics Endpoints ====================

@router.get("/statistics/summary", response_model=AnnotationStatistics)
async def get_annotation_statistics(
    tag_id: Optional[UUID] = Query(None),
    device_id: Optional[UUID] = Query(None),
    site_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get annotation statistics.

    Can be filtered by tag, device, or site.
    """
    query = db.query(Annotation).filter(Annotation.is_deleted == False)

    # Apply filters
    if tag_id:
        query = query.filter(Annotation.tag_id == tag_id)
    if device_id:
        query = query.filter(Annotation.device_id == device_id)
    if site_id:
        query = query.filter(Annotation.site_id == site_id)

    # Total count
    total_annotations = query.count()

    # Count by type
    by_type = {}
    for annotation_type in AnnotationType:
        count = query.filter(Annotation.annotation_type == annotation_type).count()
        by_type[annotation_type.value] = count

    # Count by severity
    by_severity = {}
    for severity in AnnotationSeverity:
        count = query.filter(Annotation.severity == severity).count()
        by_severity[severity.value] = count

    # Recent counts
    now = datetime.utcnow()
    recent_count_24h = query.filter(Annotation.created_at >= now - timedelta(hours=24)).count()
    recent_count_7d = query.filter(Annotation.created_at >= now - timedelta(days=7)).count()

    # Pinned count
    pinned_count = query.filter(Annotation.pinned == True).count()

    # Range vs point annotations
    range_annotations = query.filter(Annotation.end_time.isnot(None)).count()
    point_annotations = query.filter(Annotation.end_time.is_(None)).count()

    return AnnotationStatistics(
        total_annotations=total_annotations,
        by_type=by_type,
        by_severity=by_severity,
        recent_count_24h=recent_count_24h,
        recent_count_7d=recent_count_7d,
        pinned_count=pinned_count,
        range_annotations=range_annotations,
        point_annotations=point_annotations
    )
