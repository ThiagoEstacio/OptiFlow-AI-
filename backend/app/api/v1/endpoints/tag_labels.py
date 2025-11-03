"""
Tag Labels API endpoints
Allows users to create friendly names and organize tags
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, distinct
from sqlalchemy.orm import joinedload
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.models.tag import Tag
from app.models.tag_label import TagLabel
from app.schemas.tag_label import (
    TagLabelCreate,
    TagLabelUpdate,
    TagLabelResponse,
    TagWithLabel,
    TagLabelSearchParams,
    TagLabelBulkCreate,
    TagLabelStats
)

router = APIRouter()


@router.post("/", response_model=TagLabelResponse, status_code=201)
async def create_tag_label(
    label_data: TagLabelCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a user-friendly label for a tag
    
    Example:
        Original tag: ARZ_GATES_GATE01_POSICAO_PV
        Display name: Posição do Portão 1
        Equipment: Portão de Entrada
        Area: Armazém 01
    """
    # Check if tag exists
    result = await db.execute(
        select(Tag).where(Tag.id == label_data.tag_id)
    )
    tag = result.scalar_one_or_none()
    
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag {label_data.tag_id} not found")
    
    # Check if label already exists
    result = await db.execute(
        select(TagLabel).where(TagLabel.tag_id == label_data.tag_id)
    )
    existing_label = result.scalar_one_or_none()
    
    if existing_label:
        raise HTTPException(
            status_code=409, 
            detail=f"Label already exists for tag {label_data.tag_id}. Use PUT to update."
        )
    
    # Create label
    label = TagLabel(**label_data.model_dump())
    db.add(label)
    await db.commit()
    await db.refresh(label)
    
    return label


@router.get("/{label_id}", response_model=TagLabelResponse)
async def get_tag_label(
    label_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a tag label by ID"""
    result = await db.execute(
        select(TagLabel).where(TagLabel.id == label_id)
    )
    label = result.scalar_one_or_none()
    
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    
    return label


@router.get("/tag/{tag_id}", response_model=TagLabelResponse)
async def get_label_by_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get label for a specific tag"""
    result = await db.execute(
        select(TagLabel).where(TagLabel.tag_id == tag_id)
    )
    label = result.scalar_one_or_none()
    
    if not label:
        raise HTTPException(status_code=404, detail=f"No label found for tag {tag_id}")
    
    return label


@router.put("/{label_id}", response_model=TagLabelResponse)
async def update_tag_label(
    label_id: UUID,
    label_update: TagLabelUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a tag label"""
    result = await db.execute(
        select(TagLabel).where(TagLabel.id == label_id)
    )
    label = result.scalar_one_or_none()
    
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    
    # Update fields
    update_data = label_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(label, field, value)
    
    await db.commit()
    await db.refresh(label)
    
    return label


@router.delete("/{label_id}", status_code=204)
async def delete_tag_label(
    label_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a tag label (tag itself remains unchanged)"""
    result = await db.execute(
        select(TagLabel).where(TagLabel.id == label_id)
    )
    label = result.scalar_one_or_none()
    
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    
    await db.delete(label)
    await db.commit()
    
    return None


@router.get("/", response_model=List[TagLabelResponse])
async def list_tag_labels(
    query: Optional[str] = Query(None, description="Search in display name, equipment, area"),
    area_name: Optional[str] = Query(None, description="Filter by area"),
    equipment_name: Optional[str] = Query(None, description="Filter by equipment"),
    system_name: Optional[str] = Query(None, description="Filter by system"),
    is_favorite: Optional[bool] = Query(None, description="Filter favorites"),
    is_visible: Optional[bool] = Query(True, description="Filter visibility"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    List and search tag labels
    
    Supports:
    - Text search (display_name, equipment_name, area_name)
    - Filtering by area, equipment, system
    - Favorites
    - Visibility
    - Pagination
    """
    stmt = select(TagLabel)
    
    # Apply filters
    filters = []
    
    if query:
        search_filter = or_(
            TagLabel.display_name.ilike(f"%{query}%"),
            TagLabel.equipment_name.ilike(f"%{query}%"),
            TagLabel.area_name.ilike(f"%{query}%"),
            TagLabel.system_name.ilike(f"%{query}%"),
            TagLabel.short_name.ilike(f"%{query}%")
        )
        filters.append(search_filter)
    
    if area_name:
        filters.append(TagLabel.area_name.ilike(f"%{area_name}%"))
    
    if equipment_name:
        filters.append(TagLabel.equipment_name.ilike(f"%{equipment_name}%"))
    
    if system_name:
        filters.append(TagLabel.system_name.ilike(f"%{system_name}%"))
    
    if is_favorite is not None:
        filters.append(TagLabel.is_favorite == is_favorite)
    
    if is_visible is not None:
        filters.append(TagLabel.is_visible == is_visible)
    
    if filters:
        stmt = stmt.where(and_(*filters))
    
    # Pagination
    stmt = stmt.order_by(TagLabel.display_name).limit(limit).offset(offset)
    
    result = await db.execute(stmt)
    labels = result.scalars().all()
    
    return labels


@router.get("/tags/with-labels", response_model=List[TagWithLabel])
async def list_tags_with_labels(
    include_unlabeled: bool = Query(True, description="Include tags without labels"),
    area_name: Optional[str] = Query(None),
    equipment_name: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_active: bool = Query(True),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    List all tags with their labels (if they have one)
    
    Returns combined view of original tag + label information
    """
    stmt = select(Tag).options(joinedload(Tag.label))
    
    filters = [Tag.is_active == is_active]
    
    # Join with label for filtering
    if area_name or equipment_name:
        stmt = stmt.join(TagLabel, Tag.id == TagLabel.tag_id, isouter=True)
        
        if area_name:
            filters.append(TagLabel.area_name.ilike(f"%{area_name}%"))
        
        if equipment_name:
            filters.append(TagLabel.equipment_name.ilike(f"%{equipment_name}%"))
    
    if category:
        filters.append(Tag.category == category)
    
    if not include_unlabeled:
        # Only tags with labels
        stmt = stmt.join(TagLabel, Tag.id == TagLabel.tag_id)
    
    stmt = stmt.where(and_(*filters)).limit(limit).offset(offset)
    
    result = await db.execute(stmt)
    tags = result.unique().scalars().all()
    
    # Build response with effective names
    response = []
    for tag in tags:
        # Get label (handle both single object and list)
        label_obj = None
        if hasattr(tag, 'label'):
            if isinstance(tag.label, list):
                label_obj = tag.label[0] if tag.label else None
            else:
                label_obj = tag.label
        
        tag_dict = {
            "id": tag.id,
            "name": tag.name,
            "description": tag.description,
            "unit": tag.unit,
            "data_type": tag.data_type.value,
            "category": tag.category.value,
            "is_active": tag.is_active,
            "label": label_obj.to_dict() if label_obj else None,
            "effective_name": label_obj.display_name if label_obj else tag.name,
            "effective_description": (
                label_obj.custom_description if label_obj and label_obj.custom_description
                else tag.description
            )
        }
        response.append(TagWithLabel(**tag_dict))
    
    return response


@router.post("/bulk", response_model=List[TagLabelResponse], status_code=201)
async def bulk_create_labels(
    bulk_data: TagLabelBulkCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk create tag labels
    
    Useful for initial setup or importing labels from a file
    """
    created_labels = []
    errors = []
    
    for label_data in bulk_data.labels:
        try:
            # Check if tag exists
            result = await db.execute(
                select(Tag).where(Tag.id == label_data.tag_id)
            )
            tag = result.scalar_one_or_none()
            
            if not tag:
                errors.append(f"Tag {label_data.tag_id} not found")
                continue
            
            # Check if label already exists
            result = await db.execute(
                select(TagLabel).where(TagLabel.tag_id == label_data.tag_id)
            )
            existing_label = result.scalar_one_or_none()
            
            if existing_label:
                errors.append(f"Label already exists for tag {label_data.tag_id}")
                continue
            
            # Create label
            label = TagLabel(**label_data.model_dump())
            db.add(label)
            created_labels.append(label)
            
        except Exception as e:
            errors.append(f"Error creating label for {label_data.tag_id}: {str(e)}")
    
    if created_labels:
        await db.commit()
        for label in created_labels:
            await db.refresh(label)
    
    if errors:
        # Return partial success with errors in response headers or body
        # For now, just log them
        import logging
        logger = logging.getLogger(__name__)
        for error in errors:
            logger.warning(f"Bulk create error: {error}")
    
    return created_labels


@router.get("/stats/overview", response_model=TagLabelStats)
async def get_label_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics about tag labels
    
    Useful for dashboard overview
    """
    # Total tags
    total_tags_result = await db.execute(select(func.count(Tag.id)))
    total_tags = total_tags_result.scalar()
    
    # Labeled tags
    labeled_tags_result = await db.execute(select(func.count(TagLabel.id)))
    labeled_tags = labeled_tags_result.scalar()
    
    # Favorites
    favorites_result = await db.execute(
        select(func.count(TagLabel.id)).where(TagLabel.is_favorite == True)
    )
    favorite_tags = favorites_result.scalar()
    
    # Unique areas
    areas_result = await db.execute(
        select(func.count(distinct(TagLabel.area_name))).where(TagLabel.area_name.isnot(None))
    )
    areas_count = areas_result.scalar()
    
    # Unique equipments
    equipments_result = await db.execute(
        select(func.count(distinct(TagLabel.equipment_name))).where(TagLabel.equipment_name.isnot(None))
    )
    equipments_count = equipments_result.scalar()
    
    # Unique systems
    systems_result = await db.execute(
        select(func.count(distinct(TagLabel.system_name))).where(TagLabel.system_name.isnot(None))
    )
    systems_count = systems_result.scalar()
    
    return TagLabelStats(
        total_tags=total_tags,
        labeled_tags=labeled_tags,
        unlabeled_tags=total_tags - labeled_tags,
        favorite_tags=favorite_tags,
        areas_count=areas_count,
        equipments_count=equipments_count,
        systems_count=systems_count
    )


@router.get("/filters/areas", response_model=List[str])
async def get_unique_areas(
    db: AsyncSession = Depends(get_db)
):
    """Get list of unique area names for filtering"""
    result = await db.execute(
        select(distinct(TagLabel.area_name))
        .where(TagLabel.area_name.isnot(None))
        .order_by(TagLabel.area_name)
    )
    areas = [row[0] for row in result.all()]
    return areas


@router.get("/filters/equipments", response_model=List[str])
async def get_unique_equipments(
    area_name: Optional[str] = Query(None, description="Filter equipments by area"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of unique equipment names for filtering"""
    stmt = select(distinct(TagLabel.equipment_name)).where(TagLabel.equipment_name.isnot(None))
    
    if area_name:
        stmt = stmt.where(TagLabel.area_name == area_name)
    
    stmt = stmt.order_by(TagLabel.equipment_name)
    
    result = await db.execute(stmt)
    equipments = [row[0] for row in result.all()]
    return equipments


@router.get("/filters/systems", response_model=List[str])
async def get_unique_systems(
    db: AsyncSession = Depends(get_db)
):
    """Get list of unique system names for filtering"""
    result = await db.execute(
        select(distinct(TagLabel.system_name))
        .where(TagLabel.system_name.isnot(None))
        .order_by(TagLabel.system_name)
    )
    systems = [row[0] for row in result.all()]
    return systems
