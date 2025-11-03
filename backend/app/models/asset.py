"""
Asset model - Hierarchical asset structure (similar to PI Vision Asset Framework)

Provides hierarchical organization of industrial assets:
- Enterprise (Company level)
- Site (Plant/Facility)
- Area (Process Area)
- Equipment (Individual equipment)

Each asset can have attributes that reference tags or contain static values.
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class AssetType(str, enum.Enum):
    """Asset types in hierarchy"""
    ENTERPRISE = "enterprise"  # Top level - Company
    SITE = "site"              # Plant/Facility
    AREA = "area"              # Process area within site
    UNIT = "unit"              # Process unit within area
    EQUIPMENT = "equipment"    # Individual equipment
    COMPONENT = "component"    # Sub-component of equipment


class Asset(Base):
    """
    Asset model - Hierarchical structure for organizing industrial equipment

    Similar to PI Vision Asset Framework, allows:
    - Tree navigation (Enterprise → Site → Area → Equipment)
    - Asset templates
    - Attribute inheritance
    - Context-aware dashboards
    """
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    asset_type = Column(SQLEnum(AssetType), nullable=False, index=True)

    # Hierarchy - self-referential foreign key
    parent_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=True, index=True)

    # Optional template reference (for future use)
    template_id = Column(UUID(as_uuid=True), ForeignKey("asset_templates.id"), nullable=True, index=True)

    # Active flag
    is_active = Column(Boolean, default=True, nullable=False)

    # Additional metadata (flexible JSON storage)
    metadata = Column(JSONB, default=dict, nullable=False)
    # metadata can contain:
    # - manufacturer, model, serial_number
    # - installation_date, warranty_expiry
    # - location (GPS coordinates, building, floor)
    # - criticality_level, maintenance_priority
    # - custom fields specific to industry

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    # Self-referential for parent-child
    parent = relationship("Asset", remote_side=[id], back_populates="children")
    children = relationship(
        "Asset",
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="Asset.name"
    )

    # Attributes of this asset
    attributes = relationship(
        "AssetAttribute",
        back_populates="asset",
        cascade="all, delete-orphan",
        order_by="AssetAttribute.name"
    )

    # Health alerts for this asset
    health_alerts = relationship(
        "AssetHealthAlert",
        back_populates="asset",
        cascade="all, delete-orphan",
        order_by="AssetHealthAlert.triggered_at.desc()"
    )

    # Template relationship
    template = relationship("AssetTemplate", back_populates="instances")

    def __repr__(self):
        return f"<Asset {self.name} ({self.asset_type})>"

    @property
    def full_path(self) -> str:
        """Returns full hierarchical path (e.g., 'Enterprise/Site A/Area 1/Equipment 1')"""
        if self.parent:
            return f"{self.parent.full_path}/{self.name}"
        return self.name

    @property
    def level(self) -> int:
        """Returns hierarchy level (0 = top level)"""
        if self.parent:
            return self.parent.level + 1
        return 0

    def get_ancestors(self) -> list:
        """Returns list of all ancestors (parent, grandparent, etc)"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def get_descendants(self) -> list:
        """Returns list of all descendants (children, grandchildren, etc)"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants


class AssetAttribute(Base):
    """
    Asset Attribute - Links assets to tags or contains static values

    Types:
    - TAG_REFERENCE: Points to a Tag (e.g., Speed → TAG_MOTOR_01_SPEED)
    - STATIC: Static value (e.g., Design_Speed = 1200 RPM)
    - CALCULATED: Formula-based (e.g., Efficiency = (Actual/Design)*100)
    """
    __tablename__ = "asset_attributes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)

    # Attribute info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Attribute type
    attribute_type = Column(
        SQLEnum(
            "tag_reference",
            "static",
            "calculated",
            name="asset_attribute_type"
        ),
        default="tag_reference",
        nullable=False
    )

    # For TAG_REFERENCE type: reference to actual tag
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="SET NULL"), nullable=True, index=True)

    # For STATIC type: static value
    static_value = Column(String(500), nullable=True)

    # For CALCULATED type: formula
    formula = Column(Text, nullable=True)
    # Formula syntax examples:
    # - "{Speed} / {Design_Speed} * 100"  (references other attributes)
    # - "({Tag1} + {Tag2}) / 2"
    # - "IF({Status} == 'Running', {Power}, 0)"

    # Unit of measure
    unit = Column(String(50), nullable=True)

    # Display order
    display_order = Column(Integer, default=0, nullable=False)

    # Additional settings
    settings = Column(JSONB, default=dict, nullable=False)
    # settings can contain:
    # - display_format, decimal_places
    # - min_value, max_value, thresholds
    # - color_coding_rules
    # - refresh_rate

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    asset = relationship("Asset", back_populates="attributes")
    tag = relationship("Tag")

    def __repr__(self):
        return f"<AssetAttribute {self.name} ({self.attribute_type})>"


class AssetTemplate(Base):
    """
    Asset Template - Reusable asset definitions

    Similar to PI Vision Element Templates, allows:
    - Define standard attributes for a type of equipment
    - Instantiate multiple assets from template
    - Update template and propagate changes to instances
    """
    __tablename__ = "asset_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Template info
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    asset_type = Column(SQLEnum(AssetType), nullable=False, index=True)

    # Template definition (JSON structure)
    attribute_definitions = Column(JSONB, default=list, nullable=False)
    # attribute_definitions format:
    # [
    #   {
    #     "name": "Speed",
    #     "attribute_type": "tag_reference",
    #     "unit": "RPM",
    #     "settings": {"min_value": 0, "max_value": 1500}
    #   },
    #   {
    #     "name": "Design_Speed",
    #     "attribute_type": "static",
    #     "static_value": "1200",
    #     "unit": "RPM"
    #   },
    #   {
    #     "name": "Efficiency",
    #     "attribute_type": "calculated",
    #     "formula": "{Speed} / {Design_Speed} * 100",
    #     "unit": "%"
    #   }
    # ]

    # Analysis definitions (for future use)
    analyses = Column(JSONB, default=list, nullable=False)

    # Active flag
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    instances = relationship("Asset", back_populates="template")

    def __repr__(self):
        return f"<AssetTemplate {self.name}>"

    def instantiate(self, name: str, parent_id=None, **kwargs) -> Asset:
        """
        Create a new Asset instance from this template

        Args:
            name: Name for the new asset
            parent_id: Optional parent asset ID
            **kwargs: Additional asset properties

        Returns:
            New Asset instance with attributes defined by template
        """
        # Create asset
        asset = Asset(
            name=name,
            asset_type=self.asset_type,
            parent_id=parent_id,
            template_id=self.id,
            **kwargs
        )

        # Create attributes from template
        for attr_def in self.attribute_definitions:
            attribute = AssetAttribute(
                asset=asset,
                name=attr_def["name"],
                attribute_type=attr_def["attribute_type"],
                static_value=attr_def.get("static_value"),
                formula=attr_def.get("formula"),
                unit=attr_def.get("unit"),
                settings=attr_def.get("settings", {})
            )

        return asset
