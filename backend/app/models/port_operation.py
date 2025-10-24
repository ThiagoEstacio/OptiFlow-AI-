"""
SmartPort - Port Operation Model

Represents cargo operations (loading/unloading) at the port.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base


class OperationType(str, enum.Enum):
    """Type of port operation"""
    LOADING = "loading"
    UNLOADING = "unloading"
    BUNKERING = "bunkering"
    MAINTENANCE = "maintenance"
    INSPECTION = "inspection"
    PASSENGER_OPERATION = "passenger_operation"


class OperationStatus(str, enum.Enum):
    """Current status of a port operation"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DELAYED = "delayed"


class CargoType(str, enum.Enum):
    """Type of cargo being handled"""
    CONTAINERS = "containers"
    BULK_SOLID = "bulk_solid"
    BULK_LIQUID = "bulk_liquid"
    GENERAL_CARGO = "general_cargo"
    VEHICLES = "vehicles"
    PASSENGERS = "passengers"
    OTHER = "other"


class PortOperation(Base):
    """Port operation model for tracking cargo operations"""
    __tablename__ = "port_operations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References
    vessel_id = Column(UUID(as_uuid=True), ForeignKey("vessels.id"), nullable=False, index=True)
    berth_id = Column(UUID(as_uuid=True), ForeignKey("berths.id"), nullable=False, index=True)

    # Operation Details
    operation_type = Column(SQLEnum(OperationType), nullable=False, index=True)
    status = Column(SQLEnum(OperationStatus), nullable=False, default=OperationStatus.SCHEDULED, index=True)
    cargo_type = Column(SQLEnum(CargoType), nullable=True)

    # Quantities
    containers_planned = Column(Integer, nullable=True)
    containers_completed = Column(Integer, default=0)
    tonnage_planned = Column(Float, nullable=True)  # Metric tonnes
    tonnage_completed = Column(Float, default=0.0)
    cubic_meters_planned = Column(Float, nullable=True)
    cubic_meters_completed = Column(Float, default=0.0)

    # Scheduling
    scheduled_start = Column(DateTime(timezone=True), nullable=False, index=True)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    estimated_end = Column(DateTime(timezone=True), nullable=False)
    actual_end = Column(DateTime(timezone=True), nullable=True)

    # Resources
    cranes_assigned = Column(Integer, default=0)
    workforce_assigned = Column(Integer, default=0)
    equipment_used = Column(JSONB, nullable=True)  # List of equipment IDs/names

    # Performance Metrics
    productivity_rate = Column(Float, nullable=True)  # Containers or tonnes per hour
    downtime_hours = Column(Float, default=0.0)
    efficiency_percentage = Column(Float, nullable=True)  # 0-100

    # Cost & Billing
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    currency = Column(String(3), default="USD")

    # Priority & Risk
    priority = Column(Integer, default=3, nullable=False)  # 1=highest, 5=lowest
    weather_delay = Column(Boolean, default=False)
    equipment_delay = Column(Boolean, default=False)
    labor_delay = Column(Boolean, default=False)

    # Details
    cargo_description = Column(String(500), nullable=True)
    special_requirements = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=True)

    # Relationships
    vessel = relationship("Vessel", back_populates="operations")
    berth = relationship("Berth", back_populates="operations")

    def __repr__(self):
        return f"<PortOperation {self.operation_type.value} - {self.vessel_id} at {self.berth_id} ({self.status.value})>"

    @property
    def is_active(self) -> bool:
        """Check if operation is currently active"""
        return self.status in [OperationStatus.IN_PROGRESS, OperationStatus.PAUSED]

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage based on containers or tonnage"""
        if self.containers_planned and self.containers_planned > 0:
            return min(100.0, (self.containers_completed / self.containers_planned) * 100)
        elif self.tonnage_planned and self.tonnage_planned > 0:
            return min(100.0, (self.tonnage_completed / self.tonnage_planned) * 100)
        elif self.cubic_meters_planned and self.cubic_meters_planned > 0:
            return min(100.0, (self.cubic_meters_completed / self.cubic_meters_planned) * 100)
        return 0.0

    @property
    def duration_hours(self) -> Optional[float]:
        """Calculate actual or current duration in hours"""
        if self.actual_start:
            end_time = self.actual_end or datetime.utcnow()
            duration = end_time - self.actual_start
            return duration.total_seconds() / 3600
        return None

    @property
    def estimated_duration_hours(self) -> float:
        """Calculate estimated duration in hours"""
        duration = self.estimated_end - self.scheduled_start
        return duration.total_seconds() / 3600

    @property
    def is_delayed(self) -> bool:
        """Check if operation is delayed"""
        if self.status == OperationStatus.DELAYED:
            return True
        if self.status == OperationStatus.SCHEDULED and datetime.utcnow() > self.scheduled_start:
            return True
        if self.status == OperationStatus.IN_PROGRESS and datetime.utcnow() > self.estimated_end:
            return True
        return False

    @property
    def delay_hours(self) -> Optional[float]:
        """Calculate delay in hours if operation is delayed"""
        if not self.is_delayed:
            return None

        if self.status == OperationStatus.SCHEDULED:
            delay = datetime.utcnow() - self.scheduled_start
            return delay.total_seconds() / 3600
        elif self.status == OperationStatus.IN_PROGRESS:
            delay = datetime.utcnow() - self.estimated_end
            return max(0, delay.total_seconds() / 3600)
        return None

    def update_progress(self, containers: Optional[int] = None, tonnage: Optional[float] = None, cubic_meters: Optional[float] = None):
        """Update operation progress"""
        if containers is not None:
            self.containers_completed = min(containers, self.containers_planned or containers)
        if tonnage is not None:
            self.tonnage_completed = min(tonnage, self.tonnage_planned or tonnage)
        if cubic_meters is not None:
            self.cubic_meters_completed = min(cubic_meters, self.cubic_meters_planned or cubic_meters)

        # Auto-complete if target reached
        if self.completion_percentage >= 100.0 and self.status != OperationStatus.COMPLETED:
            self.status = OperationStatus.COMPLETED
            self.actual_end = datetime.utcnow()

    def calculate_productivity(self):
        """Calculate productivity rate based on actual progress"""
        if not self.actual_start:
            return None

        duration = self.duration_hours
        if not duration or duration == 0:
            return None

        if self.containers_completed > 0:
            self.productivity_rate = self.containers_completed / duration
        elif self.tonnage_completed > 0:
            self.productivity_rate = self.tonnage_completed / duration

        return self.productivity_rate

    def calculate_efficiency(self):
        """Calculate efficiency percentage"""
        estimated = self.estimated_duration_hours
        actual = self.duration_hours

        if actual and estimated and actual > 0:
            # Efficiency = (Estimated / Actual) * Completion%
            time_efficiency = (estimated / actual) * 100
            self.efficiency_percentage = min(100.0, (time_efficiency + self.completion_percentage) / 2)

        return self.efficiency_percentage
