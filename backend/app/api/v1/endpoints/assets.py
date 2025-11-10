"""
Asset Framework endpoints - Hierarchical asset structure (similar to PI Vision AF)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.session import get_db
from app.models.asset import Asset, AssetAttribute, AssetTemplate, AssetType
from app.schemas.asset import (
    AssetCreate, AssetUpdate, AssetResponse, AssetTreeNode,
    AssetAttributeCreate, AssetAttributeUpdate, AssetAttributeResponse,
    AssetTemplateCreate, AssetTemplateUpdate, AssetTemplateResponse,
    AssetInstantiateRequest
)
from app.services.asset_calculator import AssetAttributeCalculator, FormulaEvaluationError

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# Asset Endpoints
# ============================================================================

@router.get("/", response_model=List[AssetResponse])
async def list_assets(
    skip: int = 0,
    limit: int = 100,
    asset_type: Optional[str] = None,
    parent_id: Optional[UUID] = None,
    is_active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db)
):
    """List all assets with optional filtering"""
    stmt = select(Asset).options(
        selectinload(Asset.children),
        selectinload(Asset.attributes)
    )

    if asset_type:
        stmt = stmt.where(Asset.asset_type == asset_type)

    if parent_id is not None:
        stmt = stmt.where(Asset.parent_id == parent_id)

    if is_active is not None:
        stmt = stmt.where(Asset.is_active == is_active)

    stmt = stmt.offset(skip).limit(limit).order_by(Asset.name)
    result = await db.execute(stmt)
    assets = result.scalars().all()

    # Enrich response with computed properties
    response_assets = []
    for asset in assets:
        asset_dict = {
            'id': asset.id,
            'name': asset.name,
            'description': asset.description,
            'asset_type': asset.asset_type.value if hasattr(asset.asset_type, 'value') else asset.asset_type,
            'is_active': bool(asset.is_active),
            'metadata': asset.asset_metadata or {},
            'parent_id': asset.parent_id,
            'template_id': asset.template_id,
            'created_at': asset.created_at,
            'updated_at': asset.updated_at,
            'level': asset.level,
            'full_path': asset.full_path,
            'children_count': len(asset.children),
            'attributes_count': len(asset.attributes)
        }
        response_assets.append(asset_dict)

    return response_assets


@router.get("/tree", response_model=List[AssetTreeNode])
async def get_asset_tree(
    root_id: Optional[UUID] = None,
    max_depth: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Get hierarchical asset tree structure

    If root_id is provided, returns tree starting from that asset.
    Otherwise, returns all root-level assets (parent_id = NULL) and their descendants.
    """

    async def build_tree_node(asset: Asset, current_depth: int = 0) -> AssetTreeNode:
        """Recursively build tree node with children"""
        node = AssetTreeNode(
            id=asset.id,
            name=asset.name,
            asset_type=asset.asset_type.value if hasattr(asset.asset_type, 'value') else asset.asset_type,
            is_active=bool(asset.is_active),
            parent_id=asset.parent_id,
            level=asset.level,
            full_path=asset.full_path,
            attributes_count=len(asset.attributes),
            metadata=asset.asset_metadata or {},
            children=[]
        )

        # Load children recursively up to max_depth
        if current_depth < max_depth and asset.children:
            for child in asset.children:
                child_node = await build_tree_node(child, current_depth + 1)
                node.children.append(child_node)

        return node

    # Start from specific root or all roots
    if root_id:
        stmt = select(Asset).where(Asset.id == root_id)
    else:
        stmt = select(Asset).where(Asset.parent_id.is_(None))

    stmt = stmt.options(
        selectinload(Asset.children),
        selectinload(Asset.attributes)
    ).order_by(Asset.name)

    result = await db.execute(stmt)
    root_assets = result.scalars().all()

    if not root_assets:
        if root_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset with id {root_id} not found"
            )
        return []

    # Build tree for each root
    tree_nodes = []
    for asset in root_assets:
        tree_node = await build_tree_node(asset)
        tree_nodes.append(tree_node)

    return tree_nodes


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("100/minute")
async def create_asset(
    request: Request,
    asset_in: AssetCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new asset"""

    # Validate parent exists if parent_id provided
    if asset_in.parent_id:
        parent_stmt = select(Asset).where(Asset.id == asset_in.parent_id)
        parent_result = await db.execute(parent_stmt)
        parent = parent_result.scalar_one_or_none()

        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent asset with id {asset_in.parent_id} not found"
            )

    # Validate template exists if template_id provided
    if asset_in.template_id:
        template_stmt = select(AssetTemplate).where(AssetTemplate.id == asset_in.template_id)
        template_result = await db.execute(template_stmt)
        template = template_result.scalar_one_or_none()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with id {asset_in.template_id} not found"
            )

    asset = Asset(**asset_in.model_dump())
    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return asset


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get asset by ID"""
    stmt = select(Asset).where(Asset.id == asset_id).options(
        selectinload(Asset.children),
        selectinload(Asset.attributes)
    )
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    # Enrich with computed properties
    response = AssetResponse.from_orm(asset)
    response.level = asset.level
    response.full_path = asset.full_path
    response.children_count = len(asset.children)
    response.attributes_count = len(asset.attributes)

    return response


@router.put("/{asset_id}", response_model=AssetResponse)
@limiter.limit("100/minute")
async def update_asset(
    request: Request,
    asset_id: UUID,
    asset_in: AssetUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an asset"""
    stmt = select(Asset).where(Asset.id == asset_id)
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    # Validate parent exists if changing parent
    if asset_in.parent_id and asset_in.parent_id != asset.parent_id:
        # Prevent circular references
        if asset_in.parent_id == asset_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Asset cannot be its own parent"
            )

        parent_stmt = select(Asset).where(Asset.id == asset_in.parent_id)
        parent_result = await db.execute(parent_stmt)
        parent = parent_result.scalar_one_or_none()

        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent asset with id {asset_in.parent_id} not found"
            )

        # Check if new parent is a descendant (would create cycle)
        descendants = asset.get_descendants()
        if any(d.id == asset_in.parent_id for d in descendants):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot move asset under its own descendant (would create cycle)"
            )

    # Update only provided fields
    update_data = asset_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    await db.commit()
    await db.refresh(asset)
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("50/minute")
async def delete_asset(
    request: Request,
    asset_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete an asset (cascades to children and attributes)"""
    stmt = select(Asset).where(Asset.id == asset_id)
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    await db.delete(asset)
    await db.commit()
    return None


@router.get("/{asset_id}/ancestors", response_model=List[AssetResponse])
async def get_asset_ancestors(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all ancestors of an asset (parent, grandparent, etc)"""
    stmt = select(Asset).where(Asset.id == asset_id)
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    ancestors = asset.get_ancestors()
    return ancestors


@router.get("/{asset_id}/descendants", response_model=List[AssetResponse])
async def get_asset_descendants(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all descendants of an asset (children, grandchildren, etc)"""
    stmt = select(Asset).where(Asset.id == asset_id)
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    descendants = asset.get_descendants()
    return descendants


# ============================================================================
# Asset Attribute Endpoints
# ============================================================================

@router.get("/{asset_id}/attributes", response_model=List[AssetAttributeResponse])
async def list_asset_attributes(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """List all attributes for an asset"""
    # Verify asset exists
    asset_stmt = select(Asset).where(Asset.id == asset_id)
    asset_result = await db.execute(asset_stmt)
    asset = asset_result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    stmt = select(AssetAttribute).where(
        AssetAttribute.asset_id == asset_id
    ).order_by(AssetAttribute.display_order, AssetAttribute.name)

    result = await db.execute(stmt)
    attributes = result.scalars().all()
    return attributes


@router.post("/{asset_id}/attributes", response_model=AssetAttributeResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("100/minute")
async def create_asset_attribute(
    request: Request,
    asset_id: UUID,
    attribute_in: AssetAttributeCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new asset attribute"""

    # Verify asset exists
    asset_stmt = select(Asset).where(Asset.id == asset_id)
    asset_result = await db.execute(asset_stmt)
    asset = asset_result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    # Ensure asset_id matches
    attribute_data = attribute_in.model_dump()
    attribute_data['asset_id'] = asset_id

    attribute = AssetAttribute(**attribute_data)
    db.add(attribute)
    await db.commit()
    await db.refresh(attribute)
    return attribute


@router.put("/attributes/{attribute_id}", response_model=AssetAttributeResponse)
@limiter.limit("100/minute")
async def update_asset_attribute(
    request: Request,
    attribute_id: UUID,
    attribute_in: AssetAttributeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an asset attribute"""
    stmt = select(AssetAttribute).where(AssetAttribute.id == attribute_id)
    result = await db.execute(stmt)
    attribute = result.scalar_one_or_none()

    if not attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset attribute not found"
        )

    # Update only provided fields
    update_data = attribute_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(attribute, field, value)

    await db.commit()
    await db.refresh(attribute)
    return attribute


@router.delete("/attributes/{attribute_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("50/minute")
async def delete_asset_attribute(
    request: Request,
    attribute_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete an asset attribute"""
    stmt = select(AssetAttribute).where(AssetAttribute.id == attribute_id)
    result = await db.execute(stmt)
    attribute = result.scalar_one_or_none()

    if not attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset attribute not found"
        )

    await db.delete(attribute)
    await db.commit()
    return None


# ============================================================================
# Asset Template Endpoints
# ============================================================================

@router.get("/templates/", response_model=List[AssetTemplateResponse])
async def list_asset_templates(
    skip: int = 0,
    limit: int = 100,
    asset_type: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db)
):
    """List all asset templates"""
    stmt = select(AssetTemplate)

    if asset_type:
        stmt = stmt.where(AssetTemplate.asset_type == asset_type)

    if is_active is not None:
        stmt = stmt.where(AssetTemplate.is_active == is_active)

    stmt = stmt.offset(skip).limit(limit).order_by(AssetTemplate.name)
    result = await db.execute(stmt)
    templates = result.scalars().all()

    # Enrich with instance counts
    response_templates = []
    for template in templates:
        template_dict = AssetTemplateResponse.from_orm(template).model_dump()
        template_dict['instances_count'] = len(template.instances) if template.instances else 0
        response_templates.append(template_dict)

    return response_templates


@router.post("/templates/", response_model=AssetTemplateResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("50/minute")
async def create_asset_template(
    request: Request,
    template_in: AssetTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new asset template"""

    # Check if template name already exists
    existing_stmt = select(AssetTemplate).where(AssetTemplate.name == template_in.name)
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template with name '{template_in.name}' already exists"
        )

    template = AssetTemplate(**template_in.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.get("/templates/{template_id}", response_model=AssetTemplateResponse)
async def get_asset_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get asset template by ID"""
    stmt = select(AssetTemplate).where(AssetTemplate.id == template_id)
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset template not found"
        )

    return template


@router.put("/templates/{template_id}", response_model=AssetTemplateResponse)
@limiter.limit("50/minute")
async def update_asset_template(
    request: Request,
    template_id: UUID,
    template_in: AssetTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an asset template"""
    stmt = select(AssetTemplate).where(AssetTemplate.id == template_id)
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset template not found"
        )

    # Check name uniqueness if changing name
    if template_in.name and template_in.name != template.name:
        existing_stmt = select(AssetTemplate).where(AssetTemplate.name == template_in.name)
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template with name '{template_in.name}' already exists"
            )

    # Update only provided fields
    update_data = template_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    await db.commit()
    await db.refresh(template)
    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_asset_template(
    request: Request,
    template_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete an asset template"""
    stmt = select(AssetTemplate).where(AssetTemplate.id == template_id)
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset template not found"
        )

    await db.delete(template)
    await db.commit()
    return None


@router.post("/templates/{template_id}/instantiate", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("50/minute")
async def instantiate_asset_from_template(
    request: Request,
    template_id: UUID,
    instantiate_req: AssetInstantiateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new asset from a template"""

    # Get template
    template_stmt = select(AssetTemplate).where(AssetTemplate.id == template_id)
    template_result = await db.execute(template_stmt)
    template = template_result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset template not found"
        )

    # Validate parent if provided
    if instantiate_req.parent_id:
        parent_stmt = select(Asset).where(Asset.id == instantiate_req.parent_id)
        parent_result = await db.execute(parent_stmt)
        parent = parent_result.scalar_one_or_none()

        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent asset with id {instantiate_req.parent_id} not found"
            )

    # Use template's instantiate method
    asset = template.instantiate(
        name=instantiate_req.name,
        parent_id=instantiate_req.parent_id,
        metadata=instantiate_req.metadata
    )

    # Apply any attribute overrides
    if instantiate_req.attribute_overrides:
        for attr in asset.attributes:
            if attr.name in instantiate_req.attribute_overrides:
                override_value = instantiate_req.attribute_overrides[attr.name]
                if attr.attribute_type == 'static':
                    attr.static_value = str(override_value)

    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return asset



# ============================================================================
# Calculated Attributes Endpoints
# ============================================================================

@router.post("/attributes/{attribute_id}/calculate")
async def calculate_attribute_value(
    attribute_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate the current value of a calculated attribute

    Returns the evaluated result based on the formula
    """
    # Get attribute
    stmt = select(AssetAttribute).where(AssetAttribute.id == attribute_id)
    result = await db.execute(stmt)
    attribute = result.scalar_one_or_none()

    if not attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found"
        )

    if attribute.attribute_type != "calculated":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attribute is not a calculated type"
        )

    if not attribute.formula:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attribute has no formula"
        )

    # Evaluate formula
    calculator = AssetAttributeCalculator(db)

    try:
        value = await calculator.evaluate_attribute(
            asset_id=str(attribute.asset_id),
            attribute_name=attribute.name
        )

        return {
            "attribute_id": str(attribute.id),
            "attribute_name": attribute.name,
            "formula": attribute.formula,
            "calculated_value": value,
            "unit": attribute.unit,
            "success": True
        }

    except FormulaEvaluationError as e:
        return {
            "attribute_id": str(attribute.id),
            "attribute_name": attribute.name,
            "formula": attribute.formula,
            "calculated_value": None,
            "error": str(e),
            "success": False
        }


@router.get("/{asset_id}/calculate-all")
async def calculate_all_attributes(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate all calculated attributes for an asset

    Returns a dictionary of attribute names to their calculated values
    """
    # Verify asset exists
    asset_stmt = select(Asset).where(Asset.id == asset_id)
    asset_result = await db.execute(asset_stmt)
    asset = asset_result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    # Calculate all
    calculator = AssetAttributeCalculator(db)

    try:
        results = await calculator.evaluate_all_calculated_attributes(str(asset_id))

        # Get attribute details for response
        attributes = []
        for attr_name, value in results.items():
            stmt = select(AssetAttribute).where(
                AssetAttribute.asset_id == asset_id,
                AssetAttribute.name == attr_name
            )
            result = await db.execute(stmt)
            attr = result.scalar_one_or_none()

            if attr:
                attributes.append({
                    "id": str(attr.id),
                    "name": attr.name,
                    "formula": attr.formula,
                    "calculated_value": value,
                    "unit": attr.unit,
                    "success": value is not None
                })

        return {
            "asset_id": str(asset_id),
            "asset_name": asset.name,
            "calculated_attributes": attributes,
            "total_count": len(attributes),
            "success_count": sum(1 for a in attributes if a["success"])
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating attributes: {str(e)}"
        )


@router.post("/evaluate-formula")
async def evaluate_formula_test(
    formula: str,
    asset_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Test endpoint to evaluate a formula

    Useful for testing formulas before creating attributes
    """
    calculator = AssetAttributeCalculator(db)

    try:
        value = await calculator.evaluate_formula(formula, str(asset_id))

        return {
            "formula": formula,
            "asset_id": str(asset_id),
            "result": value,
            "success": True
        }

    except FormulaEvaluationError as e:
        return {
            "formula": formula,
            "asset_id": str(asset_id),
            "result": None,
            "error": str(e),
            "success": False
        }



# ============================================================================
# Asset Health Endpoints
# ============================================================================

@router.get("/{asset_id}/health")
async def get_asset_health(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get health score for an asset

    Returns health score (0-100) based on attribute values and thresholds
    """
    from app.services.asset_health import AssetHealthCalculator

    calculator = AssetHealthCalculator(db)

    try:
        health = await calculator.calculate_asset_health(str(asset_id))
        return health

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating health: {str(e)}"
        )


@router.get("/{asset_id}/health/hierarchy")
async def get_hierarchy_health(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get health score for an asset and all its descendants

    Returns hierarchical health report with rollup scores
    """
    from app.services.asset_health import AssetHealthCalculator

    calculator = AssetHealthCalculator(db)

    try:
        health = await calculator.calculate_hierarchy_health(str(asset_id))
        return health

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating hierarchy health: {str(e)}"
        )


@router.get("/health/overview")
async def get_all_assets_health_overview(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get health overview for all assets

    Query parameters:
    - status_filter: Filter by status (excellent, good, fair, poor, critical)
    """
    from app.services.asset_health import AssetHealthCalculator

    # Get all assets
    stmt = select(Asset).offset(skip).limit(limit)
    result = await db.execute(stmt)
    assets = result.scalars().all()

    calculator = AssetHealthCalculator(db)

    # Calculate health for each
    health_reports = []

    for asset in assets:
        try:
            health = await calculator.calculate_asset_health(str(asset.id))

            # Apply status filter
            if status_filter and health.get("status") != status_filter:
                continue

            health_reports.append(health)

        except Exception as e:
            print(f"Error calculating health for asset {asset.id}: {e}")
            continue

    # Calculate statistics
    if health_reports:
        scores = [h["health_score"] for h in health_reports if h.get("health_score") is not None]
        avg_score = sum(scores) / len(scores) if scores else 0

        status_counts = {}
        for h in health_reports:
            status = h.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

    else:
        avg_score = 0
        status_counts = {}

    return {
        "total_assets": len(health_reports),
        "average_health_score": round(avg_score, 2),
        "status_distribution": status_counts,
        "assets": health_reports,
    }


# ======================
# Health Trends & Analytics Endpoints
# ======================

@router.get("/{asset_id}/health/trend")
async def get_asset_health_trend(
    asset_id: UUID,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get health trend data for an asset

    Returns time-series health score data for trend visualization
    """
    from app.services.asset_health_analytics import AssetHealthAnalytics
    from datetime import datetime

    analytics = AssetHealthAnalytics(db)

    # Parse datetime strings
    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00')) if start_time else None
    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00')) if end_time else None

    trend_data = await analytics.get_health_trend(
        asset_id=str(asset_id),
        start_time=start_dt,
        end_time=end_dt,
        limit=limit
    )

    return {
        "asset_id": str(asset_id),
        "data_points": len(trend_data),
        "trend": trend_data
    }


@router.get("/{asset_id}/health/statistics")
async def get_health_statistics(
    asset_id: UUID,
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistical summary of health trend

    Returns mean, min, max, stddev, overall trend, etc.
    """
    from app.services.asset_health_analytics import AssetHealthAnalytics

    analytics = AssetHealthAnalytics(db)
    stats = await analytics.get_trend_statistics(
        asset_id=str(asset_id),
        days=days
    )

    return {
        "asset_id": str(asset_id),
        "statistics": stats
    }


@router.get("/{asset_id}/health/compare")
async def compare_health_periods(
    asset_id: UUID,
    period1_days: int = 7,
    period2_days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """
    Compare two time periods for health metrics

    Useful for assessing if asset health is improving or degrading
    """
    from app.services.asset_health_analytics import AssetHealthAnalytics

    analytics = AssetHealthAnalytics(db)
    comparison = await analytics.compare_periods(
        asset_id=str(asset_id),
        period1_days=period1_days,
        period2_days=period2_days
    )

    return {
        "asset_id": str(asset_id),
        "comparison": comparison
    }


@router.get("/{asset_id}/health/anomalies")
async def detect_health_anomalies(
    asset_id: UUID,
    days: int = 30,
    sensitivity: float = 2.0,
    db: AsyncSession = Depends(get_db)
):
    """
    Detect anomalies in health score history

    Uses statistical methods to identify unusual health patterns
    """
    from app.services.asset_health_analytics import AssetHealthAnalytics

    analytics = AssetHealthAnalytics(db)
    anomalies = await analytics.detect_anomalies(
        asset_id=str(asset_id),
        days=days,
        sensitivity=sensitivity
    )

    return {
        "asset_id": str(asset_id),
        "anomalies_detected": len(anomalies),
        "anomalies": anomalies
    }


@router.get("/{asset_id}/health/predict")
async def predict_maintenance(
    asset_id: UUID,
    days_history: int = 30,
    forecast_days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """
    Predict if asset will need maintenance

    Uses historical health trends to forecast future health
    """
    from app.services.asset_health_analytics import AssetHealthAnalytics

    analytics = AssetHealthAnalytics(db)
    prediction = await analytics.predict_maintenance_need(
        asset_id=str(asset_id),
        days_history=days_history,
        forecast_days=forecast_days
    )

    return {
        "asset_id": str(asset_id),
        "prediction": prediction
    }


@router.get("/{asset_id}/health/attribute-trends")
async def get_attribute_trends(
    asset_id: UUID,
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """
    Get trend data for individual attributes

    Returns attribute-level trend analysis
    """
    from app.services.asset_health_analytics import AssetHealthAnalytics

    analytics = AssetHealthAnalytics(db)
    trends = await analytics.get_attribute_trends(
        asset_id=str(asset_id),
        days=days
    )

    return {
        "asset_id": str(asset_id),
        "attribute_trends": trends
    }
