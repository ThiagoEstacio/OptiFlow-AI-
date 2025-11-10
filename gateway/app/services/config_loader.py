"""
Configuration Loader - Load gateway configurations from backend API
"""
from typing import List, Dict, Any, Optional
import httpx
from app.core.logger import logger
from app.core.config import settings


class ConfigLoader:
    """
    Loads gateway configurations from backend API
    Similar to KEPServerEX remote configuration
    """

    def __init__(self, backend_url: str):
        """
        Initialize configuration loader

        Args:
            backend_url: Backend API base URL
        """
        self.backend_url = backend_url.rstrip('/')
        self.api_base = f"{self.backend_url}/api/v1/gateway-config"

    async def load_gateway_configs(
        self,
        gateway_id: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Load gateway configurations from backend

        Args:
            gateway_id: Optional specific gateway ID to load
            enabled_only: Only load enabled gateways

        Returns:
            List of gateway configurations
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Build query parameters
                params = {}
                if enabled_only:
                    params["enabled_only"] = "true"

                # Fetch gateway list
                response = await client.get(
                    f"{self.api_base}/",
                    params=params
                )

                if response.status_code != 200:
                    logger.error(f"Failed to load gateway configs: HTTP {response.status_code}")
                    return []

                configs = response.json()
                logger.info(f"Loaded {len(configs)} gateway configurations from backend")

                # Load full details for each gateway (including tags)
                detailed_configs = []
                for config in configs:
                    try:
                        detail_response = await client.get(
                            f"{self.api_base}/{config['id']}"
                        )

                        if detail_response.status_code == 200:
                            detailed_configs.append(detail_response.json())
                        else:
                            logger.warning(f"Failed to load details for gateway {config['id']}")

                    except Exception as e:
                        logger.error(f"Error loading details for gateway {config['id']}: {str(e)}")
                        continue

                return detailed_configs

        except httpx.RequestError as e:
            logger.error(f"Failed to connect to backend API: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error loading gateway configurations: {str(e)}")
            return []

    async def discover_and_create_gateway(
        self,
        gateway_name: str,
        endpoint: str,
        namespace_index: Optional[int] = None,
        tag_filter: Optional[str] = None,
        polling_interval_ms: int = 1000,
        description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Discover OPC-UA tags and create gateway configuration in backend

        Args:
            gateway_name: Name for the new gateway
            endpoint: OPC-UA server endpoint
            namespace_index: Optional namespace to filter
            tag_filter: Optional search term for tags
            polling_interval_ms: Polling interval in milliseconds
            description: Optional description

        Returns:
            Created gateway configuration or None on failure
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "gateway_name": gateway_name,
                    "endpoint": endpoint,
                    "polling_interval_ms": polling_interval_ms
                }

                if namespace_index is not None:
                    payload["namespace_index"] = namespace_index
                if tag_filter:
                    payload["tag_filter"] = tag_filter
                if description:
                    payload["description"] = description

                logger.info(f"Discovering and creating gateway '{gateway_name}' from {endpoint}")

                response = await client.post(
                    f"{self.api_base}/discover/opcua/import",
                    json=payload,
                    timeout=60.0
                )

                if response.status_code == 201:
                    config = response.json()
                    logger.info(f"✅ Gateway '{gateway_name}' created with {len(config.get('tags', []))} tags")
                    return config
                else:
                    error_detail = response.json().get("detail", "Unknown error")
                    logger.error(f"Failed to create gateway: {error_detail}")
                    return None

        except httpx.RequestError as e:
            logger.error(f"Failed to connect to backend API: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error creating gateway: {str(e)}")
            return None

    def convert_to_device_config(self, gateway_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert backend gateway configuration to device manager format

        Args:
            gateway_config: Gateway configuration from backend

        Returns:
            Device configuration for DeviceManager
        """
        # Map gateway_type to protocol string
        protocol_map = {
            "opcua": "opc_ua",
            "modbus_tcp": "modbus",
            "siemens_s7": "s7",
            "rockwell_eip": "ethernet_ip"
        }

        protocol = protocol_map.get(gateway_config["gateway_type"], gateway_config["gateway_type"])

        # Base device config
        device_config = {
            "device_id": f"gateway-{gateway_config['id']}",
            "protocol": protocol,
            "config": gateway_config["connection_config"],
            "scan_rate": gateway_config["polling_interval_ms"],
            "tags": []
        }

        # Convert tags
        for tag in gateway_config.get("tags", []):
            if not tag.get("enabled", True):
                continue

            device_tag = {
                "tag_id": str(tag["id"]),
                "tag_name": tag["tag_name"],
                "address": tag["address_config"].get("node_id", tag["address_config"]),
                "data_type": tag.get("data_type", "float"),
                "scale_factor": tag.get("scale_factor", 1.0),
                "offset": tag.get("offset", 0.0),
                "unit": tag.get("unit"),
                "description": tag.get("description")
            }

            device_config["tags"].append(device_tag)

        return device_config

    async def test_connection(self) -> bool:
        """
        Test connection to backend API

        Returns:
            True if connection successful
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try to fetch gateway list
                response = await client.get(f"{self.api_base}/", params={"limit": 1})
                return response.status_code == 200

        except Exception as e:
            logger.error(f"Backend API connection test failed: {str(e)}")
            return False
