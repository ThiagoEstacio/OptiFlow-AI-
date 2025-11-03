"""
Operational Data Models

Models for tracking port terminal operations:
- Truck entries (weighbridge data)
- Ship loading operations
- Daily operational summaries
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from typing import Dict, Any


class TruckEntry(Base):
    """
    Truck entry log from weighbridge operations.

    Tracks trucks arriving to deliver grain to the terminal.
    """
    __tablename__ = "truck_entries"

    id = Column(Integer, primary_key=True, index=True)

    # Truck identification
    truck_id = Column(String(50), nullable=False, index=True)  # License plate
    driver_name = Column(String(200))
    company = Column(String(200))

    # Weight measurements
    gross_weight = Column(Float, nullable=False)  # kg - truck + cargo
    tare_weight = Column(Float, nullable=False)   # kg - empty truck
    net_weight = Column(Float, nullable=False)    # kg - cargo only

    # Product information
    product_type = Column(String(100), nullable=False, index=True)  # corn, soy, wheat
    product_quality = Column(String(50))  # Grade A, B, C
    moisture_percent = Column(Float)  # Moisture content %
    impurity_percent = Column(Float)   # Impurity content %

    # Origin
    origin_farm = Column(String(200))
    origin_city = Column(String(200))
    origin_state = Column(String(50))

    # Timestamps
    entry_time = Column(DateTime(timezone=True), nullable=False, index=True)
    gross_weight_time = Column(DateTime(timezone=True))
    tare_weight_time = Column(DateTime(timezone=True))
    exit_time = Column(DateTime(timezone=True))

    # Status
    status = Column(String(50), default="pending", index=True)  # pending, weighed, unloaded, completed
    notes = Column(Text)

    # Site reference
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    site = relationship("Site")

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # User who created the entry
    created_by_user = relationship("User")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "truck_id": self.truck_id,
            "driver_name": self.driver_name,
            "company": self.company,
            "gross_weight": self.gross_weight,
            "tare_weight": self.tare_weight,
            "net_weight": self.net_weight,
            "product_type": self.product_type,
            "product_quality": self.product_quality,
            "moisture_percent": self.moisture_percent,
            "impurity_percent": self.impurity_percent,
            "origin_farm": self.origin_farm,
            "origin_city": self.origin_city,
            "origin_state": self.origin_state,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "gross_weight_time": self.gross_weight_time.isoformat() if self.gross_weight_time else None,
            "tare_weight_time": self.tare_weight_time.isoformat() if self.tare_weight_time else None,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "status": self.status,
            "notes": self.notes,
            "site_id": self.site_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ShipLoading(Base):
    """
    Ship loading operation record.

    Tracks grain loading operations onto ships at the terminal.
    """
    __tablename__ = "ship_loadings"

    id = Column(Integer, primary_key=True, index=True)

    # Ship identification
    ship_name = Column(String(200), nullable=False, index=True)
    ship_imo = Column(String(20))  # IMO number (International Maritime Organization)
    ship_flag = Column(String(50))  # Ship's flag country
    ship_dwt = Column(Float)  # Deadweight tonnage

    # Loading details
    berth_number = Column(Integer, nullable=False, index=True)  # Which berth
    product_type = Column(String(100), nullable=False, index=True)  # corn, soy, wheat
    target_tonnage = Column(Float, nullable=False)  # Target load in tons
    loaded_tonnage = Column(Float, default=0.0)     # Actual loaded tons

    # Loading performance
    loading_rate_avg = Column(Float)  # Average tons/hour
    loading_rate_peak = Column(Float)  # Peak tons/hour
    downtime_hours = Column(Float, default=0.0)  # Hours of downtime during loading

    # Timestamps
    arrival_time = Column(DateTime(timezone=True), index=True)
    berthing_time = Column(DateTime(timezone=True))
    loading_start_time = Column(DateTime(timezone=True))
    loading_end_time = Column(DateTime(timezone=True))
    departure_time = Column(DateTime(timezone=True))

    # Status
    status = Column(String(50), default="scheduled", index=True)
    # scheduled, arrived, berthing, loading, loaded, departed

    # Commercial details
    buyer_company = Column(String(200))
    destination_port = Column(String(200))
    destination_country = Column(String(100))
    contract_number = Column(String(100))

    # Quality control
    average_moisture = Column(Float)
    average_impurity = Column(Float)
    quality_approved = Column(Boolean, default=True)
    quality_notes = Column(Text)

    # Operational notes
    weather_conditions = Column(String(200))
    incidents = Column(Text)
    notes = Column(Text)

    # Site reference
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    site = relationship("Site")

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    created_by_user = relationship("User")

    def to_dict(self) -> Dict[str, Any]:
        # Calculate loading efficiency
        loading_efficiency = None
        if self.loading_start_time and self.loading_end_time:
            total_hours = (self.loading_end_time - self.loading_start_time).total_seconds() / 3600
            active_hours = total_hours - (self.downtime_hours or 0)
            if active_hours > 0:
                loading_efficiency = (self.loaded_tonnage / active_hours) if self.loaded_tonnage else 0

        # Calculate completion percentage
        completion_percent = None
        if self.target_tonnage and self.target_tonnage > 0:
            completion_percent = (self.loaded_tonnage / self.target_tonnage) * 100

        return {
            "id": self.id,
            "ship_name": self.ship_name,
            "ship_imo": self.ship_imo,
            "ship_flag": self.ship_flag,
            "ship_dwt": self.ship_dwt,
            "berth_number": self.berth_number,
            "product_type": self.product_type,
            "target_tonnage": self.target_tonnage,
            "loaded_tonnage": self.loaded_tonnage,
            "completion_percent": round(completion_percent, 2) if completion_percent else None,
            "loading_rate_avg": self.loading_rate_avg,
            "loading_rate_peak": self.loading_rate_peak,
            "loading_efficiency": round(loading_efficiency, 2) if loading_efficiency else None,
            "downtime_hours": self.downtime_hours,
            "arrival_time": self.arrival_time.isoformat() if self.arrival_time else None,
            "berthing_time": self.berthing_time.isoformat() if self.berthing_time else None,
            "loading_start_time": self.loading_start_time.isoformat() if self.loading_start_time else None,
            "loading_end_time": self.loading_end_time.isoformat() if self.loading_end_time else None,
            "departure_time": self.departure_time.isoformat() if self.departure_time else None,
            "status": self.status,
            "buyer_company": self.buyer_company,
            "destination_port": self.destination_port,
            "destination_country": self.destination_country,
            "contract_number": self.contract_number,
            "average_moisture": self.average_moisture,
            "average_impurity": self.average_impurity,
            "quality_approved": self.quality_approved,
            "quality_notes": self.quality_notes,
            "weather_conditions": self.weather_conditions,
            "incidents": self.incidents,
            "notes": self.notes,
            "site_id": self.site_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DailyOperations(Base):
    """
    Daily operational summary.

    Aggregated statistics for each day of operations.
    """
    __tablename__ = "daily_operations"

    id = Column(Integer, primary_key=True, index=True)

    # Date
    operation_date = Column(Date, nullable=False, index=True)

    # Truck operations
    trucks_received = Column(Integer, default=0)
    trucks_total_tonnage = Column(Float, default=0.0)
    trucks_avg_wait_time = Column(Float)  # Average wait time in minutes

    # Ship operations
    ships_in_port = Column(Integer, default=0)
    ships_loading = Column(Integer, default=0)
    ships_departed = Column(Integer, default=0)
    ships_total_tonnage = Column(Float, default=0.0)

    # Loading performance
    total_tonnage_loaded = Column(Float, default=0.0)
    avg_loading_rate = Column(Float)  # tons/hour
    operating_hours = Column(Float, default=0.0)
    downtime_hours = Column(Float, default=0.0)

    # Equipment availability
    shiploaders_available = Column(Integer)
    shiploaders_operating = Column(Integer)
    conveyors_available = Column(Integer)
    conveyors_operating = Column(Integer)

    # Product breakdown
    corn_tonnage = Column(Float, default=0.0)
    soy_tonnage = Column(Float, default=0.0)
    wheat_tonnage = Column(Float, default=0.0)
    other_tonnage = Column(Float, default=0.0)

    # Weather
    weather_condition = Column(String(100))
    avg_temperature = Column(Float)
    rainfall_mm = Column(Float)
    wind_speed_kmh = Column(Float)
    weather_delays_hours = Column(Float, default=0.0)

    # Incidents and delays
    incidents_count = Column(Integer, default=0)
    incidents_description = Column(Text)
    maintenance_hours = Column(Float, default=0.0)

    # Efficiency metrics
    operational_efficiency = Column(Float)  # Percentage
    equipment_utilization = Column(Float)   # Percentage

    # Notes
    notes = Column(Text)

    # Site reference
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    site = relationship("Site")

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    created_by_user = relationship("User")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "operation_date": self.operation_date.isoformat() if self.operation_date else None,
            "trucks_received": self.trucks_received,
            "trucks_total_tonnage": self.trucks_total_tonnage,
            "trucks_avg_wait_time": self.trucks_avg_wait_time,
            "ships_in_port": self.ships_in_port,
            "ships_loading": self.ships_loading,
            "ships_departed": self.ships_departed,
            "ships_total_tonnage": self.ships_total_tonnage,
            "total_tonnage_loaded": self.total_tonnage_loaded,
            "avg_loading_rate": self.avg_loading_rate,
            "operating_hours": self.operating_hours,
            "downtime_hours": self.downtime_hours,
            "shiploaders_available": self.shiploaders_available,
            "shiploaders_operating": self.shiploaders_operating,
            "conveyors_available": self.conveyors_available,
            "conveyors_operating": self.conveyors_operating,
            "corn_tonnage": self.corn_tonnage,
            "soy_tonnage": self.soy_tonnage,
            "wheat_tonnage": self.wheat_tonnage,
            "other_tonnage": self.other_tonnage,
            "weather_condition": self.weather_condition,
            "avg_temperature": self.avg_temperature,
            "rainfall_mm": self.rainfall_mm,
            "wind_speed_kmh": self.wind_speed_kmh,
            "weather_delays_hours": self.weather_delays_hours,
            "incidents_count": self.incidents_count,
            "incidents_description": self.incidents_description,
            "maintenance_hours": self.maintenance_hours,
            "operational_efficiency": self.operational_efficiency,
            "equipment_utilization": self.equipment_utilization,
            "notes": self.notes,
            "site_id": self.site_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
