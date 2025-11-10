"""
Extended Tags and Formulas Models - PI Asset Framework style

Provides advanced tag features:
- Calculated tags with formulas
- Historical archiving configuration
- Tag grouping and organization
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum
from typing import Dict, Any


class TagType(str, enum.Enum):
    """Tag calculation types"""
    PHYSICAL = "physical"      # Direct from PLC/gateway
    CALCULATED = "calculated"  # Mathematical formula
    LOGICAL = "logical"        # Conditional logic
    AGGREGATED = "aggregated"  # Statistical (min/max/avg)


class GatewayTagExtended(Base):
    """
    Extended gateway tag with PI AF-like features:
    - Hierarchical organization (link to assets)
    - Calculated/logical tags
    - Historical archiving configuration
    - Formulas and expressions
    """
    __tablename__ = "gateway_tags_extended"

    id = Column(Integer, primary_key=True, index=True)

    # Core fields
    gateway_id = Column(Integer, ForeignKey("gateway_configs.id", ondelete="CASCADE"), nullable=True)
    tag_name = Column(String(200), nullable=False, index=True)
    enabled = Column(Boolean, default=True, nullable=False)

    # Hierarchy - link to existing assets table
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    tag_group = Column(String(200))  # Logical grouping within asset

    # Tag type and calculation
    tag_type = Column(SQLEnum(TagType), default=TagType.PHYSICAL, nullable=False)

    # For physical tags
    address_config = Column(JSON)  # Protocol-specific address
    data_type = Column(String(50), default="float")
    scale_factor = Column(Float, default=1.0)
    tag_offset = Column(Float, default=0.0)  # renamed from offset (reserved keyword)

    # For calculated/logical tags
    formula = Column(Text)  # Expression: "{TAG1} * 1.5 + {TAG2}"
    formula_tags = Column(JSON)  # List of tag IDs used in formula
    condition = Column(Text)  # Logical condition: "if {TAG1} > 100 then 1 else 0"

    # Units and limits
    unit = Column(String(50))  # Engineering unit
    min_value = Column(Float)  # Engineering range
    max_value = Column(Float)

    # Historical archiving (PI-style)
    archive_enabled = Column(Boolean, default=True)  # Enable historization
    archive_type = Column(String(50), default="on_change")  # on_change, periodic, compressed
    archive_deadband = Column(Float)  # Change threshold for archiving
    archive_interval_seconds = Column(Integer)  # For periodic archiving
    compression_deviation = Column(Float)  # Compression tolerance

    # Quality and alarms
    quality_enabled = Column(Boolean, default=True)
    alarm_enabled = Column(Boolean, default=False)
    alarm_config = Column(JSON)  # Alarm thresholds and settings

    # Metadata
    description = Column(String(1000))
    category = Column(String(100))  # Process, Control, Status, etc.
    properties = Column(JSON)  # Custom properties
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # asset = relationship("Asset")  # Link to existing Asset model

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "gateway_id": self.gateway_id,
            "tag_name": self.tag_name,
            "enabled": self.enabled,
            "asset_id": str(self.asset_id) if self.asset_id else None,
            "tag_group": self.tag_group,
            "tag_type": self.tag_type.value,
            "address_config": self.address_config,
            "data_type": self.data_type,
            "scale_factor": self.scale_factor,
            "tag_offset": self.tag_offset,
            "formula": self.formula,
            "formula_tags": self.formula_tags,
            "condition": self.condition,
            "unit": self.unit,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "archive_enabled": self.archive_enabled,
            "archive_type": self.archive_type,
            "archive_deadband": self.archive_deadband,
            "archive_interval_seconds": self.archive_interval_seconds,
            "compression_deviation": self.compression_deviation,
            "quality_enabled": self.quality_enabled,
            "alarm_enabled": self.alarm_enabled,
            "alarm_config": self.alarm_config,
            "description": self.description,
            "category": self.category,
            "properties": self.properties,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TagFormula(Base):
    """
    Reusable formulas and expressions
    Similar to PI AF Analysis/Calculations
    """
    __tablename__ = "tag_formulas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(String(1000))

    # Formula definition
    formula_type = Column(String(50), nullable=False)  # expression, script, sql
    expression = Column(Text, nullable=False)

    # Input/Output
    input_tags = Column(JSON)  # List of required tag patterns
    output_unit = Column(String(50))
    output_type = Column(String(50))  # float, int, bool, string

    # Execution
    execution_interval_seconds = Column(Integer)  # How often to execute
    is_active = Column(Boolean, default=True)

    # Metadata
    category = Column(String(100))  # Process, Quality, Efficiency, etc.
    tags_metadata = Column(JSON)  # Additional info
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "formula_type": self.formula_type,
            "expression": self.expression,
            "input_tags": self.input_tags,
            "output_unit": self.output_unit,
            "output_type": self.output_type,
            "execution_interval_seconds": self.execution_interval_seconds,
            "is_active": self.is_active,
            "category": self.category,
            "tags_metadata": self.tags_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
