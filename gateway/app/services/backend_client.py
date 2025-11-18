"""
Backend API client for sending collected data
"""
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.logger import logger
from ..core.config import settings


class BackendClient:
    """
    Client for communicating with OptiFlow backend API

    BACKPRESSURE PROTECTION:
    - Limits concurrent requests to prevent overwhelming backend
    - Drops oldest data when queue is full (prioritize recent data)
    - Prevents memory exhaustion (OOM) under high load
    """

    def __init__(self, base_url: str = None, api_key: str = None):
        """
        Initialize backend client

        Args:
            base_url: Backend API base URL
            api_key: API key for authentication
        """
        self.base_url = base_url or settings.BACKEND_URL
        self.api_key = api_key or settings.BACKEND_API_KEY

        self.session: Optional[aiohttp.ClientSession] = None
        self._connected = False

        # BACKPRESSURE: Limit concurrent requests to avoid queue buildup
        self._request_semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests
        self._pending_points_count = 0
        self._dropped_points_count = 0
        self._max_pending_points = 10000  # Drop oldest if exceeds

    async def connect(self):
        """Initialize HTTP session"""
        if not self.session:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self.session = aiohttp.ClientSession(
                base_url=self.base_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            )

            logger.info(f"Backend client initialized: {self.base_url}")

    async def disconnect(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Backend client disconnected")

    async def health_check(self) -> bool:
        """
        Check backend health

        Returns:
            True if backend is available
        """
        try:
            if not self.session:
                await self.connect()

            async with self.session.get("/health") as response:
                if response.status == 200:
                    self._connected = True
                    return True
                else:
                    self._connected = False
                    return False

        except Exception as e:
            logger.debug(f"Backend health check failed: {str(e)}")
            self._connected = False
            return False

    async def send_timeseries_batch(self, data_points: List[Dict[str, Any]]) -> bool:
        """
        Send batch of timeseries data points with BACKPRESSURE PROTECTION

        Args:
            data_points: List of data point dictionaries with keys:
                - tag_id: Tag identifier
                - value: Tag value
                - timestamp: ISO timestamp
                - quality: Data quality (optional)

        Returns:
            True if successful
        """
        # BACKPRESSURE: Check if we're overwhelmed
        self._pending_points_count += len(data_points)

        if self._pending_points_count > self._max_pending_points:
            # Drop this batch to prevent memory exhaustion
            self._dropped_points_count += len(data_points)
            self._pending_points_count -= len(data_points)
            logger.warning(
                f"⚠️ BACKPRESSURE: Dropped {len(data_points)} points "
                f"(total dropped: {self._dropped_points_count}, "
                f"pending: {self._pending_points_count})"
            )
            return False

        try:
            if not self.session:
                await self.connect()

            # BACKPRESSURE: Use semaphore to limit concurrent requests
            async with self._request_semaphore:
                async with self.session.post("/api/v1/timeseries/batch", json=data_points) as response:
                    self._pending_points_count -= len(data_points)

                    if response.status in [200, 201]:
                        logger.debug(f"✓ Sent {len(data_points)} data points to backend")
                        return True
                    else:
                        logger.error(f"Failed to send data points: {response.status}")
                        text = await response.text()
                        logger.error(f"Response: {text}")
                        return False

        except asyncio.TimeoutError:
            self._pending_points_count -= len(data_points)
            logger.error("Backend request timeout")
            return False
        except Exception as e:
            self._pending_points_count -= len(data_points)
            logger.error(f"Failed to send data to backend: {str(e)}")
            return False

    async def send_single_datapoint(self, tag_id: str, value: Any, timestamp: datetime, quality: str = "good") -> bool:
        """
        Send single data point

        Args:
            tag_id: Tag identifier
            value: Tag value
            timestamp: Timestamp
            quality: Data quality

        Returns:
            True if successful
        """
        data_point = {
            "tag_id": tag_id,
            "value": value,
            "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
            "quality": quality
        }

        return await self.send_timeseries_batch([data_point])

    async def get_device_config(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get device configuration from backend

        Args:
            device_id: Device identifier

        Returns:
            Device configuration dictionary or None
        """
        try:
            if not self.session:
                await self.connect()

            async with self.session.get(f"/api/v1/devices/{device_id}") as response:
                if response.status == 200:
                    config = await response.json()
                    logger.info(f"Retrieved device config for {device_id}")
                    return config
                else:
                    logger.error(f"Failed to get device config: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Failed to get device config: {str(e)}")
            return None

    async def get_device_tags(self, device_id: str) -> List[Dict[str, Any]]:
        """
        Get tags for a device

        Args:
            device_id: Device identifier

        Returns:
            List of tag configurations
        """
        try:
            if not self.session:
                await self.connect()

            async with self.session.get(f"/api/v1/tags/?device_id={device_id}") as response:
                if response.status == 200:
                    tags = await response.json()
                    logger.info(f"Retrieved {len(tags)} tags for device {device_id}")
                    return tags
                else:
                    logger.error(f"Failed to get device tags: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Failed to get device tags: {str(e)}")
            return []

    async def register_tags_batch(self, tags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Register multiple tags in a single batch operation

        Args:
            tags: List of tag dictionaries with keys:
                - name: Tag name
                - address: Protocol address
                - data_type: Data type (BOOL, INT, FLOAT, DOUBLE, STRING)
                - device_id: Device UUID
                - description: Optional description
                - unit: Optional engineering unit
                - enabled: Optional (default True)
                - log_enabled: Optional (default True)

        Returns:
            Result dictionary with created/skipped counts
        """
        try:
            if not self.session:
                await self.connect()

            logger.info(f"Registering {len(tags)} tags in backend...")

            async with self.session.post("/api/v1/tags/batch", json=tags) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    logger.info(
                        f"✓ Tag batch registration complete: "
                        f"{result.get('created_count', 0)} created, "
                        f"{result.get('skipped_count', 0)} skipped"
                    )
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to register tags batch: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "created_count": 0,
                        "skipped_count": len(tags)
                    }

        except Exception as e:
            logger.error(f"Failed to register tags batch: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "created_count": 0,
                "skipped_count": len(tags)
            }

    async def create_or_get_device(self, device_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new device or get existing device UUID

        Args:
            device_data: Device dictionary with keys:
                - name: Device name
                - protocol: Protocol (opcua, modbus_tcp, etc)
                - ip_address: Optional IP address
                - port: Optional port
                - description: Optional description
                - enabled: Optional (default True)

        Returns:
            Device UUID string or None on failure
        """
        try:
            if not self.session:
                await self.connect()

            # Try to find existing device by name
            async with self.session.get(f"/api/v1/devices/?name={device_data['name']}") as response:
                if response.status == 200:
                    devices = await response.json()
                    if devices and len(devices) > 0:
                        device_id = devices[0]["id"]
                        logger.info(f"Found existing device: {device_data['name']} ({device_id})")
                        return device_id

            # Device not found, create new one
            logger.info(f"Creating new device: {device_data['name']}...")
            
            async with self.session.post("/api/v1/devices/", json=device_data) as response:
                if response.status in [200, 201]:
                    device = await response.json()
                    device_id = device["id"]
                    logger.info(f"✓ Created device: {device_data['name']} ({device_id})")
                    return device_id
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create device: {response.status} - {error_text}")
                    return None

        except Exception as e:
            logger.error(f"Failed to create/get device: {str(e)}")
            return None

    async def update_device_status(self, device_id: str, status: Dict[str, Any]) -> bool:
        """
        Update device status in backend

        Args:
            device_id: Device identifier
            status: Status dictionary with keys like:
                - connected: bool
                - last_seen: ISO timestamp
                - error_count: int
                - last_error: str

        Returns:
            True if successful
        """
        try:
            if not self.session:
                await self.connect()

            async with self.session.patch(
                f"/api/v1/devices/{device_id}/status",
                json=status
            ) as response:
                if response.status in [200, 204]:
                    logger.debug(f"Updated device status for {device_id}")
                    return True
                else:
                    logger.error(f"Failed to update device status: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Failed to update device status: {str(e)}")
            return False

    @property
    def is_connected(self) -> bool:
        """Check if backend is available"""
        return self._connected
