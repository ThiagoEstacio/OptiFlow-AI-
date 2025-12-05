"""
Asset Framework API Routes
===========================

REST API for managing the Asset Framework - hierarchical organization
of industrial assets with templates and attributes.

Endpoints:
- GET /api/assets/hierarchy - Get asset hierarchy tree
- GET /api/assets/elements - List elements with filters
- GET /api/assets/elements/{id} - Get element details
- POST /api/assets/elements - Create new element
- PUT /api/assets/elements/{id} - Update element
- DELETE /api/assets/elements/{id} - Delete element
- GET /api/assets/templates - List templates
- GET /api/assets/templates/{id} - Get template details
- POST /api/assets/templates - Create template
- GET /api/assets/statistics - Get framework statistics
- POST /api/assets/build - Build hierarchy from tags
- POST /api/assets/save - Save configuration to file
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
import logging

from ...services.asset_framework import (
    get_asset_framework,
    AssetFramework,
    Element,
    ElementTemplate,
    Attribute,
    AttributeTemplate,
    ElementType,
    AttributeType
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Asset Framework"])


# === Pydantic Models for API ===

class AttributeCreate(BaseModel):
    name: str
    description: str = ""
    data_type: str = "double"
    uom: str = ""
    tag_id: Optional[str] = None
    tag_address: Optional[str] = None
    categories: List[str] = []
    hi_hi: Optional[float] = None
    hi: Optional[float] = None
    lo: Optional[float] = None
    lo_lo: Optional[float] = None


class ElementCreate(BaseModel):
    name: str
    description: str = ""
    element_type: str = "equipment"
    template_id: Optional[str] = None
    parent_id: Optional[str] = None
    icon: str = ""
    color: str = ""
    attributes: List[AttributeCreate] = []
    metadata: Dict[str, Any] = {}


class ElementUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    template_id: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AttributeTemplateCreate(BaseModel):
    name: str
    description: str = ""
    data_type: str = "double"
    default_uom: str = ""
    attribute_type: str = "tag"
    tag_pattern: str = ""
    formula: str = ""
    categories: List[str] = []
    hi_hi: Optional[float] = None
    hi: Optional[float] = None
    lo: Optional[float] = None
    lo_lo: Optional[float] = None


class TemplateCreate(BaseModel):
    name: str
    description: str = ""
    element_type: str = "equipment"
    base_template_id: Optional[str] = None
    icon: str = ""
    color: str = ""
    attributes: List[AttributeTemplateCreate] = []
    metadata: Dict[str, Any] = {}


# === Dependency ===

def get_af() -> AssetFramework:
    """Get asset framework instance"""
    return get_asset_framework()


# === Hierarchy Endpoints ===

@router.get("/hierarchy")
async def get_hierarchy(
    root_id: Optional[str] = Query(None, description="Optional root element ID"),
    af: AssetFramework = Depends(get_af)
):
    """
    Get the asset hierarchy as a nested tree structure.

    Returns the complete hierarchy starting from root elements,
    or from a specific element if root_id is provided.
    """
    try:
        hierarchy = af.get_hierarchy(root_id)
        return {
            "success": True,
            "hierarchy": hierarchy,
            "root_count": len(hierarchy)
        }
    except Exception as e:
        logger.error(f"Error getting hierarchy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(af: AssetFramework = Depends(get_af)):
    """
    Get asset framework statistics.

    Returns counts of elements, templates, attributes, etc.
    """
    try:
        stats = af.get_statistics()
        return {
            "success": True,
            **stats
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Element Endpoints ===

@router.get("/elements")
async def list_elements(
    element_type: Optional[str] = Query(None, description="Filter by element type"),
    template_id: Optional[str] = Query(None, description="Filter by template"),
    parent_id: Optional[str] = Query(None, description="Filter by parent"),
    search: Optional[str] = Query(None, description="Search by name/path"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    af: AssetFramework = Depends(get_af)
):
    """
    List elements with optional filters.
    """
    try:
        elements = list(af.elements.values())

        # Apply filters
        if element_type:
            try:
                elem_type = ElementType(element_type)
                elements = [e for e in elements if e.element_type == elem_type]
            except ValueError:
                pass

        if template_id:
            elements = [e for e in elements if e.template_id == template_id]

        if parent_id:
            elements = [e for e in elements if e.parent_id == parent_id]

        if search:
            elements = af.search_elements(search)

        total = len(elements)
        elements = elements[offset:offset + limit]

        return {
            "success": True,
            "total": total,
            "limit": limit,
            "offset": offset,
            "elements": [e.to_dict() for e in elements]
        }
    except Exception as e:
        logger.error(f"Error listing elements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/elements/{element_id}")
async def get_element(
    element_id: str,
    include_children: bool = Query(False, description="Include child elements"),
    af: AssetFramework = Depends(get_af)
):
    """
    Get a specific element by ID.
    """
    try:
        element = af.get_element(element_id)

        if not element:
            raise HTTPException(status_code=404, detail=f"Element not found: {element_id}")

        result = element.to_dict()

        if include_children:
            children = af.get_children(element_id)
            result["children_elements"] = [c.to_dict() for c in children]

        return {
            "success": True,
            "element": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting element: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/elements/by-path/{path:path}")
async def get_element_by_path(
    path: str,
    af: AssetFramework = Depends(get_af)
):
    """
    Get element by its path (e.g., /Eletrocentro/CCM01/CORR01).
    """
    try:
        # Ensure path starts with /
        if not path.startswith('/'):
            path = '/' + path

        element = af.get_element_by_path(path)

        if not element:
            raise HTTPException(status_code=404, detail=f"Element not found at path: {path}")

        return {
            "success": True,
            "element": element.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting element by path: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/elements")
async def create_element(
    element_data: ElementCreate,
    af: AssetFramework = Depends(get_af)
):
    """
    Create a new element.
    """
    try:
        # Convert attributes
        attributes = []
        for attr_data in element_data.attributes:
            import uuid
            attr = Attribute(
                id=f"attr_{uuid.uuid4().hex[:8]}",
                name=attr_data.name,
                description=attr_data.description,
                data_type=attr_data.data_type,
                uom=attr_data.uom,
                tag_id=attr_data.tag_id,
                tag_address=attr_data.tag_address,
                categories=attr_data.categories,
                hi_hi=attr_data.hi_hi,
                hi=attr_data.hi,
                lo=attr_data.lo,
                lo_lo=attr_data.lo_lo
            )
            attributes.append(attr)

        # Create element
        element = Element(
            id="",  # Will be generated
            name=element_data.name,
            description=element_data.description,
            element_type=ElementType(element_data.element_type),
            template_id=element_data.template_id,
            parent_id=element_data.parent_id,
            icon=element_data.icon,
            color=element_data.color,
            attributes=attributes,
            metadata=element_data.metadata
        )

        created = af.create_element(element)

        return {
            "success": True,
            "message": "Element created successfully",
            "element": created.to_dict()
        }
    except Exception as e:
        logger.error(f"Error creating element: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/elements/{element_id}")
async def update_element(
    element_id: str,
    updates: ElementUpdate,
    af: AssetFramework = Depends(get_af)
):
    """
    Update an existing element.
    """
    try:
        # Convert to dict, excluding None values
        update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}

        updated = af.update_element(element_id, update_dict)

        if not updated:
            raise HTTPException(status_code=404, detail=f"Element not found: {element_id}")

        return {
            "success": True,
            "message": "Element updated successfully",
            "element": updated.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating element: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/elements/{element_id}")
async def delete_element(
    element_id: str,
    recursive: bool = Query(False, description="Delete child elements recursively"),
    af: AssetFramework = Depends(get_af)
):
    """
    Delete an element.
    """
    try:
        success = af.delete_element(element_id, recursive=recursive)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Element not found or has children (use recursive=true to delete with children)"
            )

        return {
            "success": True,
            "message": f"Element {element_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting element: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Attribute Endpoints ===

@router.post("/elements/{element_id}/attributes")
async def add_attribute(
    element_id: str,
    attribute_data: AttributeCreate,
    af: AssetFramework = Depends(get_af)
):
    """
    Add an attribute (tag link) to an element.
    """
    try:
        element = af.get_element(element_id)
        if not element:
            raise HTTPException(status_code=404, detail=f"Element not found: {element_id}")

        import uuid
        attr = Attribute(
            id=f"attr_{uuid.uuid4().hex[:8]}",
            name=attribute_data.name,
            description=attribute_data.description,
            data_type=attribute_data.data_type,
            uom=attribute_data.uom,
            tag_id=attribute_data.tag_id,
            tag_address=attribute_data.tag_address,
            categories=attribute_data.categories,
            hi_hi=attribute_data.hi_hi,
            hi=attribute_data.hi,
            lo=attribute_data.lo,
            lo_lo=attribute_data.lo_lo
        )

        element.attributes.append(attr)

        # Update tag-to-attribute mapping
        if attr.tag_id:
            af.tag_to_attribute[attr.tag_id] = (element_id, attr.id)

        # Update timestamp
        from datetime import datetime
        element.updated_at = datetime.now()

        return {
            "success": True,
            "message": "Attribute added successfully",
            "attribute": attr.to_dict(),
            "element": element.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding attribute: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/elements/{element_id}/attributes/{attribute_id}")
async def update_attribute(
    element_id: str,
    attribute_id: str,
    attribute_data: AttributeCreate,
    af: AssetFramework = Depends(get_af)
):
    """
    Update an existing attribute.
    """
    try:
        element = af.get_element(element_id)
        if not element:
            raise HTTPException(status_code=404, detail=f"Element not found: {element_id}")

        # Find attribute
        attr = None
        for a in element.attributes:
            if a.id == attribute_id:
                attr = a
                break

        if not attr:
            raise HTTPException(status_code=404, detail=f"Attribute not found: {attribute_id}")

        # Remove old tag mapping
        if attr.tag_id and attr.tag_id in af.tag_to_attribute:
            del af.tag_to_attribute[attr.tag_id]

        # Update attribute
        attr.name = attribute_data.name
        attr.description = attribute_data.description
        attr.data_type = attribute_data.data_type
        attr.uom = attribute_data.uom
        attr.tag_id = attribute_data.tag_id
        attr.tag_address = attribute_data.tag_address
        attr.categories = attribute_data.categories
        attr.hi_hi = attribute_data.hi_hi
        attr.hi = attribute_data.hi
        attr.lo = attribute_data.lo
        attr.lo_lo = attribute_data.lo_lo

        # Add new tag mapping
        if attr.tag_id:
            af.tag_to_attribute[attr.tag_id] = (element_id, attr.id)

        # Update timestamp
        from datetime import datetime
        element.updated_at = datetime.now()

        return {
            "success": True,
            "message": "Attribute updated successfully",
            "attribute": attr.to_dict(),
            "element": element.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating attribute: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/elements/{element_id}/attributes/{attribute_id}")
async def delete_attribute(
    element_id: str,
    attribute_id: str,
    af: AssetFramework = Depends(get_af)
):
    """
    Remove an attribute from an element.
    """
    try:
        element = af.get_element(element_id)
        if not element:
            raise HTTPException(status_code=404, detail=f"Element not found: {element_id}")

        # Find and remove attribute
        attr_to_remove = None
        for i, attr in enumerate(element.attributes):
            if attr.id == attribute_id:
                attr_to_remove = element.attributes.pop(i)
                break

        if not attr_to_remove:
            raise HTTPException(status_code=404, detail=f"Attribute not found: {attribute_id}")

        # Remove tag mapping
        if attr_to_remove.tag_id and attr_to_remove.tag_id in af.tag_to_attribute:
            del af.tag_to_attribute[attr_to_remove.tag_id]

        # Update timestamp
        from datetime import datetime
        element.updated_at = datetime.now()

        return {
            "success": True,
            "message": f"Attribute {attribute_id} removed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting attribute: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-tags")
async def get_available_tags(
    adapter_id: Optional[str] = Query(None, description="Filter by adapter"),
    search: Optional[str] = Query(None, description="Search tags by name"),
    af: AssetFramework = Depends(get_af)
):
    """
    Get list of available tags that can be linked to attributes.
    Reads from tags_config.json.
    """
    try:
        import json
        from pathlib import Path

        config_dir = Path(__file__).parent.parent.parent.parent / "config"
        tags_file = config_dir / "tags_config.json"

        if not tags_file.exists():
            return {"success": True, "tags": [], "total": 0}

        with open(tags_file, 'r') as f:
            config = json.load(f)

        tags = config.get("tags", [])

        # Filter by adapter
        if adapter_id:
            tags = [t for t in tags if t.get("adapter_id") == adapter_id]

        # Search by name
        if search:
            search_lower = search.lower()
            tags = [t for t in tags if search_lower in t.get("name", "").lower() or
                    search_lower in t.get("tag_id", "").lower()]

        # Get unique adapters for filtering
        all_adapters = list(set(t.get("adapter_id", "") for t in config.get("tags", [])))

        return {
            "success": True,
            "tags": tags,
            "total": len(tags),
            "adapters": sorted(all_adapters)
        }
    except Exception as e:
        logger.error(f"Error getting available tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Template Endpoints ===

@router.get("/templates")
async def list_templates(
    element_type: Optional[str] = Query(None, description="Filter by element type"),
    af: AssetFramework = Depends(get_af)
):
    """
    List all element templates.
    """
    try:
        templates = af.list_templates()

        if element_type:
            try:
                elem_type = ElementType(element_type)
                templates = [t for t in templates if t.element_type == elem_type]
            except ValueError:
                pass

        return {
            "success": True,
            "total": len(templates),
            "templates": [t.to_dict() for t in templates]
        }
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}")
async def get_template(
    template_id: str,
    af: AssetFramework = Depends(get_af)
):
    """
    Get a specific template by ID.
    """
    try:
        template = af.get_template(template_id)

        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

        # Count elements using this template
        elements_using = len(af.get_elements_by_template(template_id))

        result = template.to_dict()
        result["elements_count"] = elements_using

        return {
            "success": True,
            "template": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates")
async def create_template(
    template_data: TemplateCreate,
    af: AssetFramework = Depends(get_af)
):
    """
    Create a new element template.
    """
    try:
        # Convert attribute templates
        attributes = []
        for attr_data in template_data.attributes:
            attr = AttributeTemplate(
                name=attr_data.name,
                description=attr_data.description,
                data_type=attr_data.data_type,
                default_uom=attr_data.default_uom,
                attribute_type=AttributeType(attr_data.attribute_type),
                tag_pattern=attr_data.tag_pattern,
                formula=attr_data.formula,
                categories=attr_data.categories,
                hi_hi=attr_data.hi_hi,
                hi=attr_data.hi,
                lo=attr_data.lo,
                lo_lo=attr_data.lo_lo
            )
            attributes.append(attr)

        template = ElementTemplate(
            id="",  # Will be generated
            name=template_data.name,
            description=template_data.description,
            element_type=ElementType(template_data.element_type),
            base_template_id=template_data.base_template_id,
            icon=template_data.icon,
            color=template_data.color,
            attributes=attributes,
            metadata=template_data.metadata
        )

        created = af.create_template(template)

        return {
            "success": True,
            "message": "Template created successfully",
            "template": created.to_dict()
        }
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    af: AssetFramework = Depends(get_af)
):
    """
    Delete a template (only if not in use by any elements).
    """
    try:
        success = af.delete_template(template_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Template not found or is in use by elements"
            )

        return {
            "success": True,
            "message": f"Template {template_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Management Endpoints ===

@router.post("/build")
async def build_from_tags(
    af: AssetFramework = Depends(get_af)
):
    """
    Build/rebuild asset hierarchy from tags_config.json.

    This will automatically create elements and attributes
    based on the configured tags.
    """
    try:
        # Clear existing elements (keep templates)
        af.elements.clear()
        af.root_elements.clear()
        af.path_index.clear()
        af.tag_to_attribute.clear()

        # Rebuild from tags
        created_count = af.build_from_tags()

        # Save to file
        af.save_to_file()

        stats = af.get_statistics()

        return {
            "success": True,
            "message": f"Built hierarchy with {created_count} elements",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error building from tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save")
async def save_configuration(
    af: AssetFramework = Depends(get_af)
):
    """
    Save current asset framework configuration to file.
    """
    try:
        success = af.save_to_file()

        if not success:
            raise HTTPException(status_code=500, detail="Failed to save configuration")

        return {
            "success": True,
            "message": "Configuration saved successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload")
async def reload_configuration(
    af: AssetFramework = Depends(get_af)
):
    """
    Reload asset framework configuration from file.
    """
    try:
        success = af.load_from_file()

        if not success:
            # If no file exists, build from tags
            created = af.build_from_tags()
            return {
                "success": True,
                "message": f"No saved config found. Built from tags: {created} elements created",
                "statistics": af.get_statistics()
            }

        return {
            "success": True,
            "message": "Configuration reloaded successfully",
            "statistics": af.get_statistics()
        }
    except Exception as e:
        logger.error(f"Error reloading configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))
