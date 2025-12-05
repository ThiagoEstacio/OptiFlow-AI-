"""
Asset Framework Service
========================

PI Asset Framework-style implementation for organizing industrial assets
in a hierarchical structure with templates and attributes.

Key Concepts:
- Element: Physical or logical asset (pump, motor, area, plant)
- ElementTemplate: Reusable template defining common attributes
- Attribute: Data point associated with an element (linked to a tag)
- AttributeTemplate: Template for attributes in an ElementTemplate

This provides:
- Hierarchical organization of assets
- Template-based asset modeling
- Automatic attribute inheritance
- Real-time data contextualization
- Multiple views of the same data

Example hierarchy:
    Terminal Portuário (Plant)
    ├── Eletrocentro (Area)
    │   ├── CCM01 (Equipment Group)
    │   │   ├── CORR01 (Motor) [Template: Motor_LowVoltage]
    │   │   │   ├── Running (Attribute → tag)
    │   │   │   ├── Current_A (Attribute → tag)
    │   │   │   └── Power_kW (Attribute → tag)
    │   │   └── SLD01 (Motor) [Template: Motor_HighPower]
    │   └── TR01 (Transformer) [Template: Transformer_MV]
    └── Shiploader (Area)
        └── SLD01 (Shiploader) [Template: Shiploader]
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json
import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


class ElementType(str, Enum):
    """Types of elements in the asset hierarchy"""
    PLANT = "plant"           # Top-level: entire facility
    AREA = "area"             # Major area: Eletrocentro, Shiploader
    EQUIPMENT_GROUP = "equipment_group"  # Group: CCM01, PM_GERAL
    EQUIPMENT = "equipment"   # Single equipment: Motor, Pump, Transformer
    COMPONENT = "component"   # Sub-component: Bearing, Seal


class AttributeType(str, Enum):
    """Types of attributes"""
    TAG = "tag"               # Linked to a real tag
    FORMULA = "formula"       # Calculated from other attributes
    CONSTANT = "constant"     # Static value
    ROLLUP = "rollup"         # Aggregation from child elements


@dataclass
class AttributeTemplate:
    """Template for an attribute - defines structure, not values"""
    name: str
    description: str = ""
    data_type: str = "double"
    default_uom: str = ""
    attribute_type: AttributeType = AttributeType.TAG
    tag_pattern: str = ""  # Pattern for auto-linking: e.g., "{element}_RUNNING"
    formula: str = ""      # For calculated attributes
    categories: List[str] = field(default_factory=list)  # e.g., ["electrical", "status"]

    # Alarm limits (optional)
    hi_hi: Optional[float] = None
    hi: Optional[float] = None
    lo: Optional[float] = None
    lo_lo: Optional[float] = None


@dataclass
class ElementTemplate:
    """Template for creating similar elements"""
    id: str
    name: str
    description: str = ""
    element_type: ElementType = ElementType.EQUIPMENT
    base_template_id: Optional[str] = None  # For inheritance
    attributes: List[AttributeTemplate] = field(default_factory=list)
    icon: str = ""  # Icon name for UI
    color: str = ""  # Color code for UI
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "element_type": self.element_type.value,
            "base_template_id": self.base_template_id,
            "attributes": [asdict(a) for a in self.attributes],
            "icon": self.icon,
            "color": self.color,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


@dataclass
class Attribute:
    """Actual attribute instance on an element"""
    id: str
    name: str
    description: str = ""
    data_type: str = "double"
    uom: str = ""
    attribute_type: AttributeType = AttributeType.TAG

    # Link to actual data
    tag_id: Optional[str] = None      # Link to tags_config tag
    tag_address: Optional[str] = None  # Direct address
    formula: Optional[str] = None      # For calculated attributes
    constant_value: Optional[Any] = None  # For constants

    # Current value (cached)
    current_value: Optional[Any] = None
    current_quality: str = "Unknown"
    current_timestamp: Optional[str] = None

    # Alarm configuration
    hi_hi: Optional[float] = None
    hi: Optional[float] = None
    lo: Optional[float] = None
    lo_lo: Optional[float] = None

    # Metadata
    categories: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "data_type": self.data_type,
            "uom": self.uom,
            "attribute_type": self.attribute_type.value,
            "tag_id": self.tag_id,
            "tag_address": self.tag_address,
            "formula": self.formula,
            "constant_value": self.constant_value,
            "current_value": self.current_value,
            "current_quality": self.current_quality,
            "current_timestamp": self.current_timestamp,
            "hi_hi": self.hi_hi,
            "hi": self.hi,
            "lo": self.lo,
            "lo_lo": self.lo_lo,
            "categories": self.categories,
            "metadata": self.metadata
        }


@dataclass
class Element:
    """An element in the asset hierarchy"""
    id: str
    name: str
    description: str = ""
    element_type: ElementType = ElementType.EQUIPMENT
    template_id: Optional[str] = None  # Reference to ElementTemplate
    parent_id: Optional[str] = None    # Parent element (for hierarchy)
    path: str = ""                      # Full path: /Plant/Area/Equipment

    # Attributes (data points)
    attributes: List[Attribute] = field(default_factory=list)

    # Child elements
    children: List[str] = field(default_factory=list)  # List of child element IDs

    # UI properties
    icon: str = ""
    color: str = ""
    position: Dict[str, int] = field(default_factory=dict)  # For visual layout

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)  # Search tags

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self, include_children: bool = False) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "element_type": self.element_type.value,
            "template_id": self.template_id,
            "parent_id": self.parent_id,
            "path": self.path,
            "attributes": [a.to_dict() for a in self.attributes],
            "children": self.children,
            "icon": self.icon,
            "color": self.color,
            "position": self.position,
            "metadata": self.metadata,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        return result


class AssetFramework:
    """
    Asset Framework Manager

    Manages the hierarchy of elements, templates, and attributes.
    Provides methods to:
    - Create/modify element templates
    - Build asset hierarchies
    - Link attributes to tags
    - Query elements by path, type, or template
    - Get real-time values for all attributes
    """

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent.parent / "config"

        # In-memory storage
        self.templates: Dict[str, ElementTemplate] = {}
        self.elements: Dict[str, Element] = {}
        self.root_elements: List[str] = []  # Elements with no parent

        # Tag mapping: tag_id -> attribute_id
        self.tag_to_attribute: Dict[str, str] = {}

        # Path index: path -> element_id
        self.path_index: Dict[str, str] = {}

        logger.info("🏗️ Asset Framework initialized")

    def load_from_file(self, filepath: Optional[str] = None) -> bool:
        """Load asset framework configuration from JSON file"""
        path = Path(filepath) if filepath else self.config_dir / "asset_framework.json"

        if not path.exists():
            logger.info(f"📁 Asset framework config not found: {path}")
            return False

        try:
            with open(path, 'r') as f:
                data = json.load(f)

            # Load templates
            for t_data in data.get('templates', []):
                template = self._dict_to_template(t_data)
                self.templates[template.id] = template

            # Load elements
            for e_data in data.get('elements', []):
                element = self._dict_to_element(e_data)
                self.elements[element.id] = element
                self.path_index[element.path] = element.id

                if not element.parent_id:
                    self.root_elements.append(element.id)

                # Build tag mapping
                for attr in element.attributes:
                    if attr.tag_id:
                        self.tag_to_attribute[attr.tag_id] = attr.id

            logger.info(f"✅ Loaded {len(self.templates)} templates and {len(self.elements)} elements")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to load asset framework: {e}")
            return False

    def save_to_file(self, filepath: Optional[str] = None) -> bool:
        """Save asset framework configuration to JSON file"""
        path = Path(filepath) if filepath else self.config_dir / "asset_framework.json"

        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "templates": [t.to_dict() for t in self.templates.values()],
                "elements": [e.to_dict() for e in self.elements.values()]
            }

            with open(path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"✅ Saved asset framework to {path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to save asset framework: {e}")
            return False

    def build_from_tags(self, tags_config_path: Optional[str] = None) -> int:
        """
        Automatically build asset hierarchy from tags_config.json

        Uses group_path and metadata to create elements and attributes.
        Returns number of elements created.
        """
        path = Path(tags_config_path) if tags_config_path else self.config_dir / "tags_config.json"

        if not path.exists():
            logger.warning(f"⚠️ Tags config not found: {path}")
            return 0

        try:
            with open(path, 'r') as f:
                tags_data = json.load(f)

            tags = tags_data.get('tags', [])
            logger.info(f"🔍 Building asset framework from {len(tags)} tags...")

            # Create default templates
            self._create_default_templates()

            # Group tags by path
            path_groups: Dict[str, List[Dict]] = {}
            for tag in tags:
                group_path = tag.get('group_path', 'Unknown')
                if group_path not in path_groups:
                    path_groups[group_path] = []
                path_groups[group_path].append(tag)

            # Create hierarchy
            created_count = 0
            for group_path, group_tags in path_groups.items():
                elements_created = self._create_elements_from_path(group_path, group_tags)
                created_count += elements_created

            # Update children references
            self._update_children_refs()

            logger.info(f"✅ Created {created_count} elements from tags")
            return created_count

        except Exception as e:
            logger.error(f"❌ Failed to build from tags: {e}", exc_info=True)
            return 0

    def _create_default_templates(self):
        """Create default element templates based on common industrial patterns"""

        # Motor template
        motor_template = ElementTemplate(
            id="template_motor",
            name="Motor",
            description="Electric motor with standard instrumentation",
            element_type=ElementType.EQUIPMENT,
            icon="motor",
            color="#4CAF50",
            attributes=[
                AttributeTemplate(
                    name="Running",
                    description="Motor running status",
                    data_type="boolean",
                    attribute_type=AttributeType.TAG,
                    tag_pattern="{element}_RUNNING",
                    categories=["status"]
                ),
                AttributeTemplate(
                    name="Current",
                    description="Motor current",
                    data_type="double",
                    default_uom="A",
                    attribute_type=AttributeType.TAG,
                    tag_pattern="{element}_I_A",
                    categories=["electrical"],
                    hi_hi=150.0,
                    hi=120.0
                ),
                AttributeTemplate(
                    name="Power",
                    description="Active power consumption",
                    data_type="double",
                    default_uom="kW",
                    attribute_type=AttributeType.TAG,
                    tag_pattern="{element}_P_KW",
                    categories=["electrical", "energy"]
                ),
                AttributeTemplate(
                    name="Thermal",
                    description="Thermal overload percentage",
                    data_type="double",
                    default_uom="%",
                    attribute_type=AttributeType.TAG,
                    tag_pattern="{element}_THERMAL_PCT",
                    categories=["protection"],
                    hi_hi=95.0,
                    hi=85.0
                )
            ]
        )
        self.templates[motor_template.id] = motor_template

        # Power Meter template
        pm_template = ElementTemplate(
            id="template_power_meter",
            name="Power Meter",
            description="Multifunction power meter",
            element_type=ElementType.EQUIPMENT,
            icon="meter",
            color="#2196F3",
            attributes=[
                AttributeTemplate(name="V_AB", data_type="double", default_uom="V", categories=["voltage"]),
                AttributeTemplate(name="V_BC", data_type="double", default_uom="V", categories=["voltage"]),
                AttributeTemplate(name="V_CA", data_type="double", default_uom="V", categories=["voltage"]),
                AttributeTemplate(name="I_A", data_type="double", default_uom="A", categories=["current"]),
                AttributeTemplate(name="I_B", data_type="double", default_uom="A", categories=["current"]),
                AttributeTemplate(name="I_C", data_type="double", default_uom="A", categories=["current"]),
                AttributeTemplate(name="P_KW", data_type="double", default_uom="kW", categories=["power"]),
                AttributeTemplate(name="Q_KVAR", data_type="double", default_uom="kVAr", categories=["power"]),
                AttributeTemplate(name="PF", data_type="double", default_uom="", categories=["power_quality"]),
                AttributeTemplate(name="Frequency", data_type="double", default_uom="Hz", categories=["power_quality"]),
                AttributeTemplate(name="KWH", data_type="double", default_uom="kWh", categories=["energy"]),
            ]
        )
        self.templates[pm_template.id] = pm_template

        # Transformer template
        transformer_template = ElementTemplate(
            id="template_transformer",
            name="Transformer",
            description="Power transformer",
            element_type=ElementType.EQUIPMENT,
            icon="transformer",
            color="#FF9800",
            attributes=[
                AttributeTemplate(name="Load_PCT", data_type="double", default_uom="%", hi_hi=100.0, hi=80.0),
                AttributeTemplate(name="Power_KW", data_type="double", default_uom="kW"),
                AttributeTemplate(name="Power_KVAR", data_type="double", default_uom="kVAr"),
                AttributeTemplate(name="Temperature", data_type="double", default_uom="°C", hi_hi=85.0, hi=70.0),
            ]
        )
        self.templates[transformer_template.id] = transformer_template

        # Shiploader template
        shiploader_template = ElementTemplate(
            id="template_shiploader",
            name="Shiploader",
            description="Ship loading equipment",
            element_type=ElementType.EQUIPMENT,
            icon="shiploader",
            color="#9C27B0",
            attributes=[
                AttributeTemplate(name="Flow_TPH", data_type="double", default_uom="t/h"),
                AttributeTemplate(name="Power_KW", data_type="double", default_uom="kW"),
                AttributeTemplate(name="Boom_Angle", data_type="double", default_uom="°"),
                AttributeTemplate(name="Slewing", data_type="double", default_uom="°"),
                AttributeTemplate(name="Shuttle_Position", data_type="double", default_uom="m"),
                AttributeTemplate(name="Total_Loaded", data_type="double", default_uom="t"),
                AttributeTemplate(name="Progress", data_type="double", default_uom="%"),
            ]
        )
        self.templates[shiploader_template.id] = shiploader_template

        # Area template
        area_template = ElementTemplate(
            id="template_area",
            name="Area",
            description="Plant area or section",
            element_type=ElementType.AREA,
            icon="area",
            color="#607D8B"
        )
        self.templates[area_template.id] = area_template

        logger.info(f"📋 Created {len(self.templates)} default templates")

    def _create_elements_from_path(self, group_path: str, tags: List[Dict]) -> int:
        """Create elements from a group path and its tags"""
        parts = group_path.split('/')
        created = 0
        parent_id = None
        current_path = ""

        # Create intermediate elements (areas, equipment groups)
        for i, part in enumerate(parts):
            current_path = f"/{'/'.join(parts[:i+1])}"

            if current_path in self.path_index:
                parent_id = self.path_index[current_path]
                continue

            # Determine element type based on position
            if i == 0:
                elem_type = ElementType.AREA
                template_id = "template_area"
            elif i == len(parts) - 1:
                # Last level - determine by name pattern
                elem_type = ElementType.EQUIPMENT
                template_id = self._guess_template(part, tags)
            else:
                elem_type = ElementType.EQUIPMENT_GROUP
                template_id = None

            element = Element(
                id=f"elem_{uuid.uuid4().hex[:8]}",
                name=part,
                description=f"{part} - Auto-generated from tags",
                element_type=elem_type,
                template_id=template_id,
                parent_id=parent_id,
                path=current_path,
                icon=self._get_icon_for_type(elem_type),
                color=self._get_color_for_type(elem_type)
            )

            self.elements[element.id] = element
            self.path_index[current_path] = element.id

            if not parent_id:
                self.root_elements.append(element.id)

            parent_id = element.id
            created += 1

        # Add attributes to the leaf element
        if parent_id and parent_id in self.elements:
            element = self.elements[parent_id]
            for tag in tags:
                attr = self._tag_to_attribute(tag)
                element.attributes.append(attr)
                if attr.tag_id:
                    self.tag_to_attribute[attr.tag_id] = attr.id

        return created

    def _guess_template(self, name: str, tags: List[Dict]) -> Optional[str]:
        """Guess the appropriate template based on element name and tags"""
        name_upper = name.upper()

        # Check for motor patterns
        if any(x in name_upper for x in ['CORR', 'VNT', 'BMB', 'MOTOR', 'ELV']):
            return "template_motor"

        # Check for power meter
        if any(x in name_upper for x in ['PM_', 'METER']):
            return "template_power_meter"

        # Check for transformer
        if any(x in name_upper for x in ['TR0', 'TRAFO', 'TRANSFORMER']):
            return "template_transformer"

        # Check for shiploader
        if any(x in name_upper for x in ['SLD', 'SHIPLOADER']):
            return "template_shiploader"

        return None

    def _tag_to_attribute(self, tag: Dict) -> Attribute:
        """Convert a tag configuration to an Attribute"""
        tag_name = tag.get('tag_name', tag.get('name', ''))

        # Extract attribute name from tag name
        parts = tag_name.split('_')
        attr_name = parts[-1] if len(parts) > 1 else tag_name

        return Attribute(
            id=f"attr_{uuid.uuid4().hex[:8]}",
            name=attr_name,
            description=tag.get('metadata', {}).get('description', ''),
            data_type=tag.get('data_type', 'double'),
            uom=tag.get('metadata', {}).get('engineering_units', ''),
            attribute_type=AttributeType.TAG,
            tag_id=tag.get('tag_id'),
            tag_address=tag.get('address'),
            categories=self._guess_categories(tag_name),
            metadata={
                "original_tag_name": tag_name,
                "adapter_id": tag.get('adapter_id'),
                "protocol": tag.get('protocol_type')
            }
        )

    def _guess_categories(self, tag_name: str) -> List[str]:
        """Guess categories based on tag name"""
        categories = []
        name_upper = tag_name.upper()

        if any(x in name_upper for x in ['V_', 'VOLTAGE', 'TENSAO']):
            categories.append("voltage")
        if any(x in name_upper for x in ['I_', 'CURRENT', 'CORRENTE', '_A']):
            categories.append("current")
        if any(x in name_upper for x in ['KW', 'POWER', 'POTENCIA']):
            categories.append("power")
        if any(x in name_upper for x in ['KWH', 'KVARH', 'ENERGY']):
            categories.append("energy")
        if any(x in name_upper for x in ['TEMP', 'TEMPERATURA']):
            categories.append("temperature")
        if any(x in name_upper for x in ['RUNNING', 'STATUS', 'STATE']):
            categories.append("status")
        if any(x in name_upper for x in ['ALARM', 'FAULT', 'TRIP']):
            categories.append("alarm")
        if any(x in name_upper for x in ['THERMAL', 'PROTECTION']):
            categories.append("protection")

        return categories if categories else ["process"]

    def _get_icon_for_type(self, elem_type: ElementType) -> str:
        """Get default icon for element type"""
        icons = {
            ElementType.PLANT: "factory",
            ElementType.AREA: "domain",
            ElementType.EQUIPMENT_GROUP: "category",
            ElementType.EQUIPMENT: "settings",
            ElementType.COMPONENT: "memory"
        }
        return icons.get(elem_type, "device_hub")

    def _get_color_for_type(self, elem_type: ElementType) -> str:
        """Get default color for element type"""
        colors = {
            ElementType.PLANT: "#1976D2",
            ElementType.AREA: "#388E3C",
            ElementType.EQUIPMENT_GROUP: "#F57C00",
            ElementType.EQUIPMENT: "#7B1FA2",
            ElementType.COMPONENT: "#455A64"
        }
        return colors.get(elem_type, "#757575")

    def _update_children_refs(self):
        """Update children references for all elements"""
        for elem_id, element in self.elements.items():
            if element.parent_id and element.parent_id in self.elements:
                parent = self.elements[element.parent_id]
                if elem_id not in parent.children:
                    parent.children.append(elem_id)

    def _dict_to_template(self, data: Dict) -> ElementTemplate:
        """Convert dictionary to ElementTemplate"""
        attributes = []
        for a in data.get('attributes', []):
            attr_type = AttributeType(a.get('attribute_type', 'tag'))
            attributes.append(AttributeTemplate(
                name=a['name'],
                description=a.get('description', ''),
                data_type=a.get('data_type', 'double'),
                default_uom=a.get('default_uom', ''),
                attribute_type=attr_type,
                tag_pattern=a.get('tag_pattern', ''),
                formula=a.get('formula', ''),
                categories=a.get('categories', []),
                hi_hi=a.get('hi_hi'),
                hi=a.get('hi'),
                lo=a.get('lo'),
                lo_lo=a.get('lo_lo')
            ))

        return ElementTemplate(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            element_type=ElementType(data.get('element_type', 'equipment')),
            base_template_id=data.get('base_template_id'),
            attributes=attributes,
            icon=data.get('icon', ''),
            color=data.get('color', ''),
            metadata=data.get('metadata', {}),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat())
        )

    def _dict_to_element(self, data: Dict) -> Element:
        """Convert dictionary to Element"""
        attributes = []
        for a in data.get('attributes', []):
            attr_type = AttributeType(a.get('attribute_type', 'tag'))
            attributes.append(Attribute(
                id=a['id'],
                name=a['name'],
                description=a.get('description', ''),
                data_type=a.get('data_type', 'double'),
                uom=a.get('uom', ''),
                attribute_type=attr_type,
                tag_id=a.get('tag_id'),
                tag_address=a.get('tag_address'),
                formula=a.get('formula'),
                constant_value=a.get('constant_value'),
                categories=a.get('categories', []),
                metadata=a.get('metadata', {}),
                hi_hi=a.get('hi_hi'),
                hi=a.get('hi'),
                lo=a.get('lo'),
                lo_lo=a.get('lo_lo')
            ))

        return Element(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            element_type=ElementType(data.get('element_type', 'equipment')),
            template_id=data.get('template_id'),
            parent_id=data.get('parent_id'),
            path=data.get('path', ''),
            attributes=attributes,
            children=data.get('children', []),
            icon=data.get('icon', ''),
            color=data.get('color', ''),
            position=data.get('position', {}),
            metadata=data.get('metadata', {}),
            tags=data.get('tags', []),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat())
        )

    # === Query Methods ===

    def get_element(self, element_id: str) -> Optional[Element]:
        """Get element by ID"""
        return self.elements.get(element_id)

    def get_element_by_path(self, path: str) -> Optional[Element]:
        """Get element by path"""
        elem_id = self.path_index.get(path)
        return self.elements.get(elem_id) if elem_id else None

    def get_children(self, element_id: str) -> List[Element]:
        """Get child elements"""
        element = self.elements.get(element_id)
        if not element:
            return []
        return [self.elements[c] for c in element.children if c in self.elements]

    def get_hierarchy(self, root_id: Optional[str] = None) -> List[Dict]:
        """Get element hierarchy as nested structure"""
        if root_id:
            roots = [root_id] if root_id in self.elements else []
        else:
            roots = self.root_elements

        def build_tree(elem_id: str) -> Dict:
            elem = self.elements.get(elem_id)
            if not elem:
                return {}

            return {
                "id": elem.id,
                "name": elem.name,
                "type": elem.element_type.value,
                "path": elem.path,
                "template_id": elem.template_id,
                "icon": elem.icon,
                "color": elem.color,
                "attributes_count": len(elem.attributes),
                "children": [build_tree(c) for c in elem.children]
            }

        return [build_tree(r) for r in roots]

    def get_elements_by_type(self, elem_type: ElementType) -> List[Element]:
        """Get all elements of a specific type"""
        return [e for e in self.elements.values() if e.element_type == elem_type]

    def get_elements_by_template(self, template_id: str) -> List[Element]:
        """Get all elements using a specific template"""
        return [e for e in self.elements.values() if e.template_id == template_id]

    def search_elements(self, query: str) -> List[Element]:
        """Search elements by name, path, or tags"""
        query_lower = query.lower()
        results = []

        for elem in self.elements.values():
            if (query_lower in elem.name.lower() or
                query_lower in elem.path.lower() or
                any(query_lower in t.lower() for t in elem.tags)):
                results.append(elem)

        return results

    def get_template(self, template_id: str) -> Optional[ElementTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)

    def list_templates(self) -> List[ElementTemplate]:
        """List all templates"""
        return list(self.templates.values())

    def get_statistics(self) -> Dict[str, Any]:
        """Get asset framework statistics"""
        type_counts = {}
        for elem in self.elements.values():
            t = elem.element_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        total_attributes = sum(len(e.attributes) for e in self.elements.values())
        linked_attributes = sum(
            1 for e in self.elements.values()
            for a in e.attributes if a.tag_id
        )

        return {
            "total_templates": len(self.templates),
            "total_elements": len(self.elements),
            "root_elements": len(self.root_elements),
            "elements_by_type": type_counts,
            "total_attributes": total_attributes,
            "linked_attributes": linked_attributes,
            "unlinked_attributes": total_attributes - linked_attributes
        }

    # === Modification Methods ===

    def create_element(self, element: Element) -> Element:
        """Create a new element"""
        if not element.id:
            element.id = f"elem_{uuid.uuid4().hex[:8]}"

        # Build path if not set
        if not element.path:
            if element.parent_id and element.parent_id in self.elements:
                parent = self.elements[element.parent_id]
                element.path = f"{parent.path}/{element.name}"
            else:
                element.path = f"/{element.name}"

        self.elements[element.id] = element
        self.path_index[element.path] = element.id

        if not element.parent_id:
            self.root_elements.append(element.id)
        elif element.parent_id in self.elements:
            parent = self.elements[element.parent_id]
            if element.id not in parent.children:
                parent.children.append(element.id)

        element.updated_at = datetime.now().isoformat()
        return element

    def update_element(self, element_id: str, updates: Dict[str, Any]) -> Optional[Element]:
        """Update an existing element"""
        if element_id not in self.elements:
            return None

        element = self.elements[element_id]

        for key, value in updates.items():
            if hasattr(element, key):
                setattr(element, key, value)

        element.updated_at = datetime.now().isoformat()
        return element

    def delete_element(self, element_id: str, recursive: bool = False) -> bool:
        """Delete an element"""
        if element_id not in self.elements:
            return False

        element = self.elements[element_id]

        # Delete children if recursive
        if recursive:
            for child_id in list(element.children):
                self.delete_element(child_id, recursive=True)
        elif element.children:
            # Cannot delete element with children unless recursive
            return False

        # Remove from parent
        if element.parent_id and element.parent_id in self.elements:
            parent = self.elements[element.parent_id]
            if element_id in parent.children:
                parent.children.remove(element_id)

        # Remove from root list
        if element_id in self.root_elements:
            self.root_elements.remove(element_id)

        # Remove from path index
        if element.path in self.path_index:
            del self.path_index[element.path]

        # Remove tag mappings
        for attr in element.attributes:
            if attr.tag_id and attr.tag_id in self.tag_to_attribute:
                del self.tag_to_attribute[attr.tag_id]

        # Delete element
        del self.elements[element_id]
        return True

    def create_template(self, template: ElementTemplate) -> ElementTemplate:
        """Create a new template"""
        if not template.id:
            template.id = f"template_{uuid.uuid4().hex[:8]}"

        self.templates[template.id] = template
        template.updated_at = datetime.now().isoformat()
        return template

    def delete_template(self, template_id: str) -> bool:
        """Delete a template (only if not in use)"""
        if template_id not in self.templates:
            return False

        # Check if template is in use
        for elem in self.elements.values():
            if elem.template_id == template_id:
                return False

        del self.templates[template_id]
        return True


# === Global Instance ===

_asset_framework: Optional[AssetFramework] = None


def get_asset_framework() -> AssetFramework:
    """Get global asset framework instance"""
    global _asset_framework
    if _asset_framework is None:
        _asset_framework = AssetFramework()
    return _asset_framework


async def init_asset_framework(config_dir: Optional[str] = None) -> AssetFramework:
    """Initialize asset framework and load configuration"""
    global _asset_framework
    _asset_framework = AssetFramework(config_dir)

    # Try to load existing configuration
    if not _asset_framework.load_from_file():
        # Build from tags if no config exists
        _asset_framework.build_from_tags()
        _asset_framework.save_to_file()

    return _asset_framework
