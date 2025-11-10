"""
Extended Tags API Endpoints - PI Asset Framework style

Provides REST API for:
- Extended gateway tags with formulas and archive configuration
- Tag formulas library
- Integration with existing Asset hierarchy
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from app.db.session import get_db
from app.models.extended_tags import GatewayTagExtended, TagFormula, TagType
from app.models.asset import Asset
from app.schemas import asset_hierarchy as schemas
from uuid import UUID

router = APIRouter()


# ============================================================================
# Extended Gateway Tags Endpoints
# ============================================================================

@router.get("/tags-extended", response_model=List[schemas.GatewayTagExtendedResponse])
async def list_extended_tags(
    gateway_id: Optional[int] = None,
    asset_id: Optional[UUID] = None,
    tag_type: Optional[schemas.TagTypeEnum] = None,
    enabled_only: bool = False,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    List extended tags with filtering

    - **gateway_id**: Filter by gateway
    - **asset_id**: Filter by asset
    - **tag_type**: Filter by type (physical, calculated, logical, aggregated)
    - **enabled_only**: Show only enabled tags
    - **search**: Search in tag name, description
    """
    query = select(GatewayTagExtended)

    if gateway_id:
        query = query.where(GatewayTagExtended.gateway_id == gateway_id)

    if asset_id:
        query = query.where(GatewayTagExtended.asset_id == asset_id)

    if tag_type:
        query = query.where(GatewayTagExtended.tag_type == tag_type.value)

    if enabled_only:
        query = query.where(GatewayTagExtended.enabled == True)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                GatewayTagExtended.tag_name.ilike(search_pattern),
                GatewayTagExtended.description.ilike(search_pattern)
            )
        )

    query = query.offset(skip).limit(limit).order_by(GatewayTagExtended.tag_name)

    result = await db.execute(query)
    tags = result.scalars().all()

    return [tag.to_dict() for tag in tags]


@router.get("/tags-extended/{tag_id}", response_model=schemas.GatewayTagExtendedResponse)
async def get_extended_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get single extended tag by ID"""
    query = select(GatewayTagExtended).where(GatewayTagExtended.id == tag_id)

    result = await db.execute(query)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    return tag.to_dict()


@router.post("/tags-extended", response_model=schemas.GatewayTagExtendedResponse, status_code=201)
async def create_extended_tag(
    tag_data: schemas.GatewayTagExtendedCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new extended tag

    Validates:
    - Calculated/logical tags must have formula or condition
    - Physical tags should have address_config
    """
    # Validate tag type requirements
    if tag_data.tag_type in [schemas.TagTypeEnum.CALCULATED, schemas.TagTypeEnum.LOGICAL]:
        if not tag_data.formula and not tag_data.condition:
            raise HTTPException(
                status_code=400,
                detail="Calculated/logical tags must have formula or condition"
            )

    if tag_data.tag_type == schemas.TagTypeEnum.PHYSICAL:
        if not tag_data.address_config:
            raise HTTPException(
                status_code=400,
                detail="Physical tags must have address_config"
            )

    # Validate asset exists if specified
    if tag_data.asset_id:
        asset_query = select(Asset).where(Asset.id == tag_data.asset_id)
        result = await db.execute(asset_query)
        asset = result.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

    # Create tag
    tag = GatewayTagExtended(**tag_data.model_dump())

    db.add(tag)
    await db.commit()
    await db.refresh(tag)

    return tag.to_dict()


@router.put("/tags-extended/{tag_id}", response_model=schemas.GatewayTagExtendedResponse)
async def update_extended_tag(
    tag_id: int,
    tag_data: schemas.GatewayTagExtendedUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update existing extended tag"""
    query = select(GatewayTagExtended).where(GatewayTagExtended.id == tag_id)
    result = await db.execute(query)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Update fields
    update_data = tag_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)

    # Validate after update
    if tag.tag_type in [TagType.CALCULATED, TagType.LOGICAL]:
        if not tag.formula and not tag.condition:
            raise HTTPException(
                status_code=400,
                detail="Calculated/logical tags must have formula or condition"
            )

    await db.commit()
    await db.refresh(tag)

    return tag.to_dict()


@router.delete("/tags-extended/{tag_id}", status_code=204)
async def delete_extended_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete extended tag"""
    query = select(GatewayTagExtended).where(GatewayTagExtended.id == tag_id)
    result = await db.execute(query)
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    await db.delete(tag)
    await db.commit()


# ============================================================================
# Tag Formulas Endpoints
# ============================================================================

@router.get("/formulas", response_model=List[schemas.TagFormulaResponse])
async def list_formulas(
    formula_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    List tag formulas

    - **formula_type**: Filter by type (expression, script, sql, aggregation)
    - **is_active**: Filter by active status
    - **category**: Filter by category
    """
    query = select(TagFormula)

    if formula_type:
        query = query.where(TagFormula.formula_type == formula_type)

    if is_active is not None:
        query = query.where(TagFormula.is_active == is_active)

    if category:
        query = query.where(TagFormula.category == category)

    query = query.offset(skip).limit(limit).order_by(TagFormula.name)

    result = await db.execute(query)
    formulas = result.scalars().all()

    return [formula.to_dict() for formula in formulas]


@router.get("/formulas/{formula_id}", response_model=schemas.TagFormulaResponse)
async def get_formula(
    formula_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get single formula by ID"""
    query = select(TagFormula).where(TagFormula.id == formula_id)
    result = await db.execute(query)
    formula = result.scalar_one_or_none()

    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")

    return formula.to_dict()


@router.post("/formulas", response_model=schemas.TagFormulaResponse, status_code=201)
async def create_formula(
    formula_data: schemas.TagFormulaCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new tag formula"""
    # Check for duplicate name
    query = select(TagFormula).where(TagFormula.name == formula_data.name)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Formula with this name already exists")

    formula = TagFormula(**formula_data.model_dump())

    db.add(formula)
    await db.commit()
    await db.refresh(formula)

    return formula.to_dict()


@router.put("/formulas/{formula_id}", response_model=schemas.TagFormulaResponse)
async def update_formula(
    formula_id: int,
    formula_data: schemas.TagFormulaUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update existing formula"""
    query = select(TagFormula).where(TagFormula.id == formula_id)
    result = await db.execute(query)
    formula = result.scalar_one_or_none()

    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")

    # Check for duplicate name if changing
    if formula_data.name and formula_data.name != formula.name:
        name_query = select(TagFormula).where(TagFormula.name == formula_data.name)
        result = await db.execute(name_query)
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Formula with this name already exists")

    # Update fields
    update_data = formula_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(formula, field, value)

    await db.commit()
    await db.refresh(formula)

    return formula.to_dict()


@router.delete("/formulas/{formula_id}", status_code=204)
async def delete_formula(
    formula_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete formula"""
    query = select(TagFormula).where(TagFormula.id == formula_id)
    result = await db.execute(query)
    formula = result.scalar_one_or_none()

    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")

    await db.delete(formula)
    await db.commit()


# ============================================================================
# Bulk Operations
# ============================================================================

@router.post("/tags-extended/bulk", status_code=200)
async def bulk_tag_operation(
    operation: schemas.BulkTagOperation,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform bulk operations on tags

    - **enable**: Enable multiple tags
    - **disable**: Disable multiple tags
    - **delete**: Delete multiple tags
    - **move**: Move tags to different asset
    """
    query = select(GatewayTagExtended).where(GatewayTagExtended.id.in_(operation.tag_ids))
    result = await db.execute(query)
    tags = result.scalars().all()

    if len(tags) != len(operation.tag_ids):
        raise HTTPException(status_code=404, detail="Some tags not found")

    if operation.operation == "enable":
        for tag in tags:
            tag.enabled = True
    elif operation.operation == "disable":
        for tag in tags:
            tag.enabled = False
    elif operation.operation == "delete":
        for tag in tags:
            await db.delete(tag)
    elif operation.operation == "move":
        if not operation.target_asset_id:
            raise HTTPException(status_code=400, detail="target_asset_id required for move operation")

        # Validate target asset exists
        asset_query = select(Asset).where(Asset.id == operation.target_asset_id)
        result = await db.execute(asset_query)
        asset = result.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Target asset not found")

        for tag in tags:
            tag.asset_id = operation.target_asset_id

    await db.commit()

    return {"message": f"Operation '{operation.operation}' applied to {len(tags)} tags"}
