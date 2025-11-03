"""
Tag Label model - User-friendly aliases and metadata for tags
Allows clients to rename tags without losing connection to the original variable
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class TagLabel(Base):
    """
    Tag Label - User-friendly alias and metadata for a tag
    
    Allows clients to:
    - Give custom names to tags (e.g., "Posição do Portão 1" instead of "ARZ_GATES_GATE01_POSICAO_PV")
    - Organize by equipment and area
    - Add custom descriptions
    - Maintain connection to original tag in database
    
    Example:
        Original Tag: ARZ_GATES_GATE01_POSICAO_PV
        Display Name: Posição do Portão 1
        Equipment: Portão de Entrada
        Area: Armazém 01
        Description: Posição atual do portão de entrada do armazém
    """
    __tablename__ = "tag_labels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # User-friendly identifiers
    display_name = Column(String(255), nullable=False, index=True)  # "Posição do Portão 1"
    short_name = Column(String(100), nullable=True)  # "Portão 1" (for dashboards)
    
    # Organization
    equipment_name = Column(String(255), nullable=True, index=True)  # "Portão de Entrada"
    area_name = Column(String(255), nullable=True, index=True)  # "Armazém 01"
    system_name = Column(String(255), nullable=True, index=True)  # "Sistema de Acesso"
    
    # Custom description
    custom_description = Column(Text, nullable=True)
    
    # Additional metadata
    notes = Column(Text, nullable=True)  # Internal notes
    
    # Visibility
    is_visible = Column(Boolean, default=True, nullable=False)  # Show in UI
    is_favorite = Column(Boolean, default=False, nullable=False)  # Quick access
    
    # Audit
    created_by = Column(String(255), nullable=True)  # User who created
    updated_by = Column(String(255), nullable=True)  # User who last updated
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tag = relationship("Tag", backref="label")

    # Constraints
    __table_args__ = (
        # Ensure display names are unique per area (optional, can be removed if duplicates allowed)
        # UniqueConstraint('display_name', 'area_name', name='uq_tag_label_display_area'),
    )

    def __repr__(self):
        return f"<TagLabel '{self.display_name}' for {self.tag_id}>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "tag_id": str(self.tag_id),
            "display_name": self.display_name,
            "short_name": self.short_name,
            "equipment_name": self.equipment_name,
            "area_name": self.area_name,
            "system_name": self.system_name,
            "custom_description": self.custom_description,
            "notes": self.notes,
            "is_visible": self.is_visible,
            "is_favorite": self.is_favorite,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
