"""
Industrial Gateway Package

Provides reliable connectivity to multiple industrial protocols:
- OPC-UA
- Modbus TCP
- Siemens S7
- Rockwell EtherNet/IP
"""

from .base_gateway import BaseGateway, GatewayStatus
from .gateway_manager import GatewayManager

__all__ = ['BaseGateway', 'GatewayStatus', 'GatewayManager']
