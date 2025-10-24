"""
Device model - Industrial equipment/PLC/RTU/Sensor
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base


class DeviceProtocol(str, enum.Enum):
    """Supported protocols"""
    OPC_UA = "opcua"
    MODBUS_TCP = "modbus_tcp"
    MODBUS_RTU = "modbus_rtu"
    MQTT = "mqtt"
    S7 = "s7"
    ETHERNET_IP = "ethernet_ip"
    HTTP = "http"


class DeviceStatus(str, enum.Enum):
    """Device connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    UNKNOWN = "unknown"


class Device(Base):
    """
    Device model - represents industrial equipment
    """
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    protocol = Column(SQLEnum(DeviceProtocol), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Connection info (stored as JSON for flexibility)
    connection_config = Column(JSONB, nullable=False)
    # Example for OPC UA:
    # {
    #   "endpoint": "opc.tcp://192.168.1.100:4840",
    #   "security_mode": "SignAndEncrypt",
    #   "username": "admin",
    #   "password": "encrypted_password"
    # }

    # Status
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.UNKNOWN, nullable=False, index=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    manufacturer = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    firmware_version = Column(String(50), nullable=True)

    # Performance metrics
    total_tags = Column(Integer, default=0, nullable=False)
    data_points_collected = Column(Integer, default=0, nullable=False)

    # Additional settings
    settings = Column(JSONB, default=dict, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    site = relationship("Site", back_populates="devices")
    tags = relationship("Tag", back_populates="device", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Device {self.name} ({self.protocol.value})>"
