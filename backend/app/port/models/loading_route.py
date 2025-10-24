"""
Loading Route model - Paths/routes for material flow from storage to vessel
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Float, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class LoadingRoute(Base):
    """
    Loading Route model - represents material flow paths from storage to vessel
    """
    __tablename__ = "loading_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Route configuration
    source_storage_id = Column(UUID(as_uuid=True), ForeignKey("storage_units.id", ondelete="SET NULL"), nullable=True)
    destination_berth_id = Column(UUID(as_uuid=True), ForeignKey("berths.id", ondelete="SET NULL"), nullable=True)

    # Equipment in route (in order)
    equipment_sequence = Column(JSONB, default=list, nullable=False)
    # Example: [
    #   {"type": "stacker_reclaimer", "device_id": "uuid", "capacity": 5000},
    #   {"type": "conveyor_belt", "device_id": "uuid", "capacity": 4500},
    #   {"type": "shiploader", "device_id": "uuid", "capacity": 8000}
    # ]

    conveyor_ids = Column(ARRAY(String), default=list, nullable=False)  # OptiFlow device IDs
    transfer_point_ids = Column(ARRAY(String), default=list, nullable=False)

    # Capacity and specifications
    max_capacity = Column(Float, nullable=False)  # tons/hour
    optimal_capacity = Column(Float, nullable=True)  # tons/hour
    route_length = Column(Float, nullable=True)  # meters
    number_of_transfer_points = Column(Integer, default=0, nullable=False)

    # Performance metrics
    average_throughput = Column(Float, nullable=True)  # tons/hour
    peak_throughput = Column(Float, nullable=True)  # tons/hour
    total_material_moved = Column(Float, default=0.0, nullable=False)  # tons
    total_operations_count = Column(Integer, default=0, nullable=False)

    # Efficiency
    availability_percentage = Column(Float, nullable=True)
    utilization_percentage = Column(Float, nullable=True)
    energy_efficiency_kwh_per_ton = Column(Float, nullable=True)

    # Maintenance
    last_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    next_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    maintenance_notes = Column(Text, nullable=True)

    # Additional info
    metadata_json = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    site = relationship("Site", back_populates="loading_routes")
    source_storage = relationship("StorageUnit", foreign_keys=[source_storage_id], back_populates="outbound_routes")
    destination_berth = relationship("Berth")
    loading_operations = relationship("LoadingOperation", back_populates="route")

    def __repr__(self):
        return f"<LoadingRoute {self.name} ({self.code})>"
