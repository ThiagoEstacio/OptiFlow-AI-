"""
Annotation endpoints for team collaboration
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.db.session import get_db
from app.models.annotation import Annotation, AnnotationComment, AnnotationType, AnnotationPriority
from app.schemas.annotation import (
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationResponse,
    AnnotationCommentCreate,
    AnnotationCommentUpdate,
    AnnotationCommentResponse,
    AnnotationListResponse
)

router = APIRouter()


# ===== Annotation Endpoints =====

@router.post("/", response_model=AnnotationResponse)
async def create_annotation(
    annotation: AnnotationCreate,
    created_by: Optional[UUID] = None,  # TODO: Get from authenticated user
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new annotation

    Annotations can be used for:
    - Team comments on devices, tags, or time ranges
    - Event tracking (maintenance, alarms, observations)
    - Issue tracking and resolution
    """
    try:
        db_annotation = Annotation(
            **annotation.model_dump(),
            created_by=created_by
        )

        db.add(db_annotation)
        await db.commit()
        await db.refresh(db_annotation)

        response = AnnotationResponse.model_validate(db_annotation)
        response.comments_count = 0

        return response

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create annotation: {str(e)}")


@router.get("/{annotation_id}", response_model=AnnotationResponse)
async def get_annotation(
    annotation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get annotation by ID"""
    result = await db.execute(
        select(Annotation).where(Annotation.id == annotation_id)
    )
    annotation = result.scalar_one_or_none()

    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    # Count comments
    comments_result = await db.execute(
        select(func.count(AnnotationComment.id)).where(
            AnnotationComment.annotation_id == annotation_id
        )
    )
    comments_count = comments_result.scalar()

    response = AnnotationResponse.model_validate(annotation)
    response.comments_count = comments_count

    return response


@router.get("/", response_model=AnnotationListResponse)
async def list_annotations(
    type: Optional[AnnotationType] = Query(None),
    priority: Optional[AnnotationPriority] = Query(None),
    device_id: Optional[UUID] = Query(None),
    tag_id: Optional[UUID] = Query(None),
    site_id: Optional[UUID] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    created_by: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    List annotations with filters

    Supports filtering by:
    - Type (comment, event, alarm, maintenance, observation, issue)
    - Priority (low, medium, high, critical)
    - Related resources (device, tag, site)
    - Time range
    - Resolution status
    - Creator
    """
    # Build query filters
    filters = []

    if type:
        filters.append(Annotation.type == type)
    if priority:
        filters.append(Annotation.priority == priority)
    if device_id:
        filters.append(Annotation.device_id == device_id)
    if tag_id:
        filters.append(Annotation.tag_id == tag_id)
    if site_id:
        filters.append(Annotation.site_id == site_id)
    if is_resolved is not None:
        filters.append(Annotation.is_resolved == is_resolved)
    if created_by:
        filters.append(Annotation.created_by == created_by)

    # Time range filters
    if start_time:
        filters.append(
            or_(
                Annotation.end_time >= start_time,
                Annotation.end_time.is_(None)
            )
        )
    if end_time:
        filters.append(Annotation.start_time <= end_time)

    # Get total count
    count_query = select(func.count(Annotation.id))
    if filters:
        count_query = count_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get annotations
    query = select(Annotation).order_by(Annotation.created_at.desc())
    if filters:
        query = query.where(and_(*filters))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    annotations = result.scalars().all()

    # Get comment counts for each annotation
    annotation_responses = []
    for annotation in annotations:
        comments_result = await db.execute(
            select(func.count(AnnotationComment.id)).where(
                AnnotationComment.annotation_id == annotation.id
            )
        )
        comments_count = comments_result.scalar()

        response = AnnotationResponse.model_validate(annotation)
        response.comments_count = comments_count
        annotation_responses.append(response)

    return AnnotationListResponse(
        annotations=annotation_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.put("/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    annotation_id: UUID,
    annotation_update: AnnotationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an annotation"""
    result = await db.execute(
        select(Annotation).where(Annotation.id == annotation_id)
    )
    annotation = result.scalar_one_or_none()

    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    # Update fields
    update_data = annotation_update.model_dump(exclude_unset=True)

    # Handle resolution
    if "is_resolved" in update_data and update_data["is_resolved"]:
        if not annotation.is_resolved:
            annotation.resolved_at = datetime.utcnow()
            # annotation.resolved_by = current_user.id  # TODO: Get from auth

    for field, value in update_data.items():
        setattr(annotation, field, value)

    try:
        await db.commit()
        await db.refresh(annotation)

        # Get comment count
        comments_result = await db.execute(
            select(func.count(AnnotationComment.id)).where(
                AnnotationComment.annotation_id == annotation_id
            )
        )
        comments_count = comments_result.scalar()

        response = AnnotationResponse.model_validate(annotation)
        response.comments_count = comments_count

        return response

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update annotation: {str(e)}")


@router.delete("/{annotation_id}")
async def delete_annotation(
    annotation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete an annotation"""
    result = await db.execute(
        select(Annotation).where(Annotation.id == annotation_id)
    )
    annotation = result.scalar_one_or_none()

    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    try:
        await db.delete(annotation)
        await db.commit()

        return {"status": "success", "message": "Annotation deleted"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete annotation: {str(e)}")


# ===== Annotation Comment Endpoints =====

@router.post("/{annotation_id}/comments", response_model=AnnotationCommentResponse)
async def create_comment(
    annotation_id: UUID,
    comment: AnnotationCommentCreate,
    created_by: Optional[UUID] = None,  # TODO: Get from authenticated user
    db: AsyncSession = Depends(get_db)
):
    """
    Add a comment to an annotation

    Supports threaded replies via parent_comment_id
    """
    # Verify annotation exists
    result = await db.execute(
        select(Annotation).where(Annotation.id == annotation_id)
    )
    annotation = result.scalar_one_or_none()

    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")

    # Create comment
    try:
        db_comment = AnnotationComment(
            annotation_id=annotation_id,
            **comment.model_dump(),
            created_by=created_by
        )

        db.add(db_comment)
        await db.commit()
        await db.refresh(db_comment)

        response = AnnotationCommentResponse.model_validate(db_comment)
        response.replies = []

        return response

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create comment: {str(e)}")


@router.get("/{annotation_id}/comments", response_model=List[AnnotationCommentResponse])
async def list_comments(
    annotation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all comments for an annotation

    Returns comments with threaded replies
    """
    # Get all comments for this annotation
    result = await db.execute(
        select(AnnotationComment)
        .where(AnnotationComment.annotation_id == annotation_id)
        .order_by(AnnotationComment.created_at)
    )
    comments = result.scalars().all()

    # Build comment tree
    comment_map = {}
    root_comments = []

    for comment in comments:
        comment_response = AnnotationCommentResponse.model_validate(comment)
        comment_response.replies = []
        comment_map[comment.id] = comment_response

        if comment.parent_comment_id is None:
            root_comments.append(comment_response)

    # Build reply threads
    for comment in comments:
        if comment.parent_comment_id and comment.parent_comment_id in comment_map:
            parent = comment_map[comment.parent_comment_id]
            parent.replies.append(comment_map[comment.id])

    return root_comments


@router.put("/{annotation_id}/comments/{comment_id}", response_model=AnnotationCommentResponse)
async def update_comment(
    annotation_id: UUID,
    comment_id: UUID,
    comment_update: AnnotationCommentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a comment"""
    result = await db.execute(
        select(AnnotationComment).where(
            and_(
                AnnotationComment.id == comment_id,
                AnnotationComment.annotation_id == annotation_id
            )
        )
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    try:
        comment.comment = comment_update.comment
        comment.is_edited = True

        await db.commit()
        await db.refresh(comment)

        response = AnnotationCommentResponse.model_validate(comment)
        response.replies = []

        return response

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update comment: {str(e)}")


@router.delete("/{annotation_id}/comments/{comment_id}")
async def delete_comment(
    annotation_id: UUID,
    comment_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a comment"""
    result = await db.execute(
        select(AnnotationComment).where(
            and_(
                AnnotationComment.id == comment_id,
                AnnotationComment.annotation_id == annotation_id
            )
        )
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    try:
        await db.delete(comment)
        await db.commit()

        return {"status": "success", "message": "Comment deleted"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete comment: {str(e)}")
