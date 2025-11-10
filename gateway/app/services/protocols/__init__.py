"""
Protocol Adapters Package
=========================

This package contains protocol adapters for industrial communication protocols.
Each adapter publishes data to Kafka following the event-driven architecture.

Supported Protocols:
- OPC UA (Unified Architecture)
- Modbus TCP
- MQTT (Message Queue Telemetry Transport)
- Ethernet/IP (Industrial Protocol)
- Siemens S7 (S7comm)

All adapters inherit from BaseProtocolAdapter and publish to Kafka topic 'raw_tags'.
"""

from .base_adapter import BaseProtocolAdapter, ProtocolConfig, TagData

__all__ = [
    'BaseProtocolAdapter',
    'ProtocolConfig',
    'TagData',
]
