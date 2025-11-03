"""
Gateway Configuration Models

Stores configuration for industrial protocol gateways.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum
from typing import Dict, Any


class GatewayType(str, enum.Enum):
    """Supported gateway protocols"""
    OPCUA = "opcua"
    MODBUS_TCP = "modbus_tcp"
    SIEMENS_S7 = "siemens_s7"
    ROCKWELL_EIP = "rockwell_eip"


class GatewayConfig(Base):
    """Gateway configuration"""
    __tablename__ = "gateway_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    gateway_type = Column(SQLEnum(GatewayType), nullable=False, index=True)
    enabled = Column(Boolean, default=True, nullable=False)

    # Connection settings (stored as JSON for flexibility)
    connection_config = Column(JSON, nullable=False)
    # Example for OPC-UA:
    # {
    #     "endpoint": "opc.tcp://192.168.1.100:4840",
    #     "namespace": "urn:shiploader:server",
    #     "security_policy": "None",
    #     "username": null,
    #     "password": null
    # }

    # Polling settings
    polling_interval_ms = Column(Integer, default=1000, nullable=False)
    max_retries = Column(Integer, default=5, nullable=False)
    base_retry_delay = Column(Integer, default=5, nullable=False)  # seconds
    max_buffer_size = Column(Integer, default=10000, nullable=False)

    # Metadata
    description = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tags = relationship("GatewayTag", back_populates="gateway", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "gateway_type": self.gateway_type.value,
            "enabled": self.enabled,
            "connection_config": self.connection_config,
            "polling_interval_ms": self.polling_interval_ms,
            "max_retries": self.max_retries,
            "base_retry_delay": self.base_retry_delay,
            "max_buffer_size": self.max_buffer_size,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags_count": len(self.tags) if self.tags else 0,
        }


class GatewayTag(Base):
    """Tag configuration for a specific gateway"""
    __tablename__ = "gateway_tags"

    id = Column(Integer, primary_key=True, index=True)
    gateway_id = Column(Integer, ForeignKey("gateway_configs.id", ondelete="CASCADE"), nullable=False)
    tag_name = Column(String(200), nullable=False, index=True)
    enabled = Column(Boolean, default=True, nullable=False)

    # Protocol-specific address configuration (stored as JSON)
    address_config = Column(JSON, nullable=False)
    # Examples:
    # OPC-UA: {"node_id": "ns=2;s=Belt.Speed"}
    # Modbus: {"address": 0, "count": 2, "type": "float32", "byte_order": "big"}
    # Siemens: {"area": "DB", "db_number": 1, "start": 0, "size": 4, "datatype": "real"}
    # Rockwell: {"tag_path": "Program:MainProgram.BeltSpeed"}

    # Data type and scaling
    data_type = Column(String(50), default="float")  # float, int, bool, string
    scale_factor = Column(Float, default=1.0)
    offset = Column(Float, default=0.0)
    unit = Column(String(50))  # Engineering unit (e.g., "m/s", "°C", "kg")

    # Metadata
    description = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    gateway = relationship("GatewayConfig", back_populates="tags")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "gateway_id": self.gateway_id,
            "tag_name": self.tag_name,
            "enabled": self.enabled,
            "address_config": self.address_config,
            "data_type": self.data_type,
            "scale_factor": self.scale_factor,
            "offset": self.offset,
            "unit": self.unit,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class GatewayHealthLog(Base):
    """Gateway health monitoring log"""
    __tablename__ = "gateway_health_logs"

    id = Column(Integer, primary_key=True, index=True)
    gateway_name = Column(String(200), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Status
    status = Column(String(50), nullable=False)  # connected, disconnected, error, buffering

    # Metrics
    successful_reads = Column(Integer, default=0)
    failed_reads = Column(Integer, default=0)
    buffer_size = Column(Integer, default=0)
    uptime_seconds = Column(Float)

    # Error info
    last_error = Column(String(1000))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "gateway_name": self.gateway_name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "status": self.status,
            "successful_reads": self.successful_reads,
            "failed_reads": self.failed_reads,
            "buffer_size": self.buffer_size,
            "uptime_seconds": self.uptime_seconds,
            "last_error": self.last_error,
        }
