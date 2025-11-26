"""
Config Sync Service
===================

Synchronizes configurations from Backend to Gateway.
Gateway is read-only for configs - Backend is the source of truth.

Architecture:
- Backend: Owns all configurations (tags, alarms, formulas)
- Gateway: Fetches and caches configs locally for execution

Sync Events:
1. On startup: Full sync of all configs
2. Periodic: Polling for updates (configurable interval)
3. On-demand: Manual sync via API
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class TagConfig:
    """Tag configuration from Backend"""
    id: str
    name: str
    description: Optional[str] = None
    data_type: str = "float"
    unit: Optional[str] = None
    # Scaling
    raw_min: Optional[float] = None
    raw_max: Optional[float] = None
    eng_min: Optional[float] = None
    eng_max: Optional[float] = None
    # Quality
    deadband: Optional[float] = None
    deadband_type: str = "absolute"  # absolute, percentage
    # Historization
    historize: bool = True
    compression_enabled: bool = True
    compression_deviation: float = 0.5
    # Source
    adapter_id: Optional[str] = None
    source_address: Optional[str] = None


@dataclass
class AlarmConfig:
    """Alarm configuration from Backend"""
    id: str
    tag_id: str
    name: str
    description: Optional[str] = None
    # Thresholds
    alarm_type: str = "high"  # high, low, high_high, low_low, deviation
    setpoint: float = 0.0
    deadband: float = 0.0
    delay_seconds: float = 0.0
    # Priority
    priority: int = 3  # 1=critical, 2=high, 3=medium, 4=low
    # Actions
    enabled: bool = True


@dataclass
class FormulaConfig:
    """Formula configuration from Backend"""
    id: str
    name: str
    expression: str
    description: Optional[str] = None
    # Output
    output_tag_id: Optional[str] = None
    output_unit: Optional[str] = None
    # Dependencies
    input_tags: List[str] = field(default_factory=list)
    # Execution
    enabled: bool = True
    evaluation_interval_ms: int = 1000


@dataclass
class SyncStatus:
    """Current sync status"""
    last_sync: Optional[datetime] = None
    tags_count: int = 0
    alarms_count: int = 0
    formulas_count: int = 0
    last_error: Optional[str] = None
    is_syncing: bool = False


class ConfigSyncService:
    """
    Synchronizes configurations from Backend to Gateway.

    Responsibilities:
    1. Fetch tags from backend on startup
    2. Fetch alarms from backend on startup
    3. Fetch formulas from backend on startup
    4. Periodic polling for updates
    5. Notify components about changes
    """

    def __init__(
        self,
        backend_url: str,
        api_key: Optional[str] = None,
        sync_interval_seconds: int = 60,
        timeout_seconds: int = 30
    ):
        self.backend_url = backend_url.rstrip("/")
        self.api_key = api_key
        self.sync_interval = sync_interval_seconds
        self.timeout = timeout_seconds

        # Cached configs
        self._tags: Dict[str, TagConfig] = {}
        self._alarms: Dict[str, AlarmConfig] = {}
        self._formulas: Dict[str, FormulaConfig] = {}

        # Status
        self._status = SyncStatus()
        self._sync_task: Optional[asyncio.Task] = None
        self._running = False

        # Callbacks for config changes
        self._on_tags_updated: List[Callable] = []
        self._on_alarms_updated: List[Callable] = []
        self._on_formulas_updated: List[Callable] = []

        logger.info(f"ConfigSyncService initialized: backend={backend_url}, interval={sync_interval_seconds}s")

    # ==================== Properties ====================

    @property
    def tags(self) -> Dict[str, TagConfig]:
        """Get cached tag configs"""
        return self._tags.copy()

    @property
    def alarms(self) -> Dict[str, AlarmConfig]:
        """Get cached alarm configs"""
        return self._alarms.copy()

    @property
    def formulas(self) -> Dict[str, FormulaConfig]:
        """Get cached formula configs"""
        return self._formulas.copy()

    @property
    def status(self) -> SyncStatus:
        """Get sync status"""
        return self._status

    # ==================== Lifecycle ====================

    async def start(self):
        """Start config sync service"""
        if self._running:
            logger.warning("ConfigSyncService already running")
            return

        self._running = True
        logger.info("Starting ConfigSyncService...")

        # Initial sync
        await self.sync_all()

        # Start periodic sync
        self._sync_task = asyncio.create_task(self._periodic_sync())
        logger.info("ConfigSyncService started")

    async def stop(self):
        """Stop config sync service"""
        self._running = False

        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass

        logger.info("ConfigSyncService stopped")

    async def _periodic_sync(self):
        """Periodic sync loop"""
        while self._running:
            try:
                await asyncio.sleep(self.sync_interval)
                if self._running:
                    await self.sync_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic sync error: {e}")
                self._status.last_error = str(e)

    # ==================== Sync Methods ====================

    async def sync_all(self) -> bool:
        """
        Sync all configurations from backend.

        Returns:
            True if sync successful
        """
        if self._status.is_syncing:
            logger.warning("Sync already in progress")
            return False

        self._status.is_syncing = True
        success = True

        try:
            logger.info("Starting full config sync...")

            # Sync in parallel
            results = await asyncio.gather(
                self.sync_tags(),
                self.sync_alarms(),
                self.sync_formulas(),
                return_exceptions=True
            )

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Sync error: {result}")
                    success = False

            self._status.last_sync = datetime.now()
            self._status.last_error = None if success else "Partial sync failure"

            logger.info(
                f"Config sync complete: "
                f"tags={self._status.tags_count}, "
                f"alarms={self._status.alarms_count}, "
                f"formulas={self._status.formulas_count}"
            )

        except Exception as e:
            logger.error(f"Full sync failed: {e}")
            self._status.last_error = str(e)
            success = False
        finally:
            self._status.is_syncing = False

        return success

    async def sync_tags(self) -> List[TagConfig]:
        """
        Fetch tags from backend.

        Returns:
            List of tag configurations
        """
        try:
            data = await self._fetch("/api/v1/tags")

            if not data:
                logger.warning("No tags returned from backend")
                return []

            # Parse tags
            tags = []
            for item in data:
                try:
                    tag = TagConfig(
                        id=item.get("id", ""),
                        name=item.get("name", ""),
                        description=item.get("description"),
                        data_type=item.get("data_type", "float"),
                        unit=item.get("unit"),
                        raw_min=item.get("raw_min"),
                        raw_max=item.get("raw_max"),
                        eng_min=item.get("eng_min"),
                        eng_max=item.get("eng_max"),
                        deadband=item.get("deadband"),
                        deadband_type=item.get("deadband_type", "absolute"),
                        historize=item.get("historize", True),
                        compression_enabled=item.get("compression_enabled", True),
                        compression_deviation=item.get("compression_deviation", 0.5),
                        adapter_id=item.get("adapter_id"),
                        source_address=item.get("source_address"),
                    )
                    tags.append(tag)
                except Exception as e:
                    logger.warning(f"Failed to parse tag {item.get('id')}: {e}")

            # Update cache
            self._tags = {t.id: t for t in tags}
            self._status.tags_count = len(tags)

            # Notify listeners
            for callback in self._on_tags_updated:
                try:
                    await callback(tags)
                except Exception as e:
                    logger.error(f"Tag update callback error: {e}")

            logger.info(f"Synced {len(tags)} tags from backend")
            return tags

        except Exception as e:
            logger.error(f"Failed to sync tags: {e}")
            raise

    async def sync_alarms(self) -> List[AlarmConfig]:
        """
        Fetch alarms from backend.

        Returns:
            List of alarm configurations
        """
        try:
            data = await self._fetch("/api/v1/alarms")

            if not data:
                logger.warning("No alarms returned from backend")
                return []

            # Parse alarms
            alarms = []
            for item in data:
                try:
                    alarm = AlarmConfig(
                        id=item.get("id", ""),
                        tag_id=item.get("tag_id", ""),
                        name=item.get("name", ""),
                        description=item.get("description"),
                        alarm_type=item.get("alarm_type", "high"),
                        setpoint=item.get("setpoint", 0.0),
                        deadband=item.get("deadband", 0.0),
                        delay_seconds=item.get("delay_seconds", 0.0),
                        priority=item.get("priority", 3),
                        enabled=item.get("enabled", True),
                    )
                    alarms.append(alarm)
                except Exception as e:
                    logger.warning(f"Failed to parse alarm {item.get('id')}: {e}")

            # Update cache
            self._alarms = {a.id: a for a in alarms}
            self._status.alarms_count = len(alarms)

            # Notify listeners
            for callback in self._on_alarms_updated:
                try:
                    await callback(alarms)
                except Exception as e:
                    logger.error(f"Alarm update callback error: {e}")

            logger.info(f"Synced {len(alarms)} alarms from backend")
            return alarms

        except Exception as e:
            logger.error(f"Failed to sync alarms: {e}")
            raise

    async def sync_formulas(self) -> List[FormulaConfig]:
        """
        Fetch formulas from backend.

        Returns:
            List of formula configurations
        """
        try:
            data = await self._fetch("/api/v1/formulas")

            if not data:
                logger.warning("No formulas returned from backend")
                return []

            # Parse formulas
            formulas = []
            for item in data:
                try:
                    formula = FormulaConfig(
                        id=item.get("id", ""),
                        name=item.get("name", ""),
                        expression=item.get("expression", ""),
                        description=item.get("description"),
                        output_tag_id=item.get("output_tag_id"),
                        output_unit=item.get("output_unit"),
                        input_tags=item.get("input_tags", []),
                        enabled=item.get("enabled", True),
                        evaluation_interval_ms=item.get("evaluation_interval_ms", 1000),
                    )
                    formulas.append(formula)
                except Exception as e:
                    logger.warning(f"Failed to parse formula {item.get('id')}: {e}")

            # Update cache
            self._formulas = {f.id: f for f in formulas}
            self._status.formulas_count = len(formulas)

            # Notify listeners
            for callback in self._on_formulas_updated:
                try:
                    await callback(formulas)
                except Exception as e:
                    logger.error(f"Formula update callback error: {e}")

            logger.info(f"Synced {len(formulas)} formulas from backend")
            return formulas

        except Exception as e:
            logger.error(f"Failed to sync formulas: {e}")
            raise

    # ==================== Callbacks ====================

    def on_tags_updated(self, callback: Callable):
        """Register callback for tag updates"""
        self._on_tags_updated.append(callback)

    def on_alarms_updated(self, callback: Callable):
        """Register callback for alarm updates"""
        self._on_alarms_updated.append(callback)

    def on_formulas_updated(self, callback: Callable):
        """Register callback for formula updates"""
        self._on_formulas_updated.append(callback)

    # ==================== HTTP Client ====================

    async def _fetch(self, endpoint: str) -> Any:
        """
        Fetch data from backend API.

        Args:
            endpoint: API endpoint (e.g., /api/v1/tags)

        Returns:
            Parsed JSON response
        """
        url = f"{self.backend_url}{endpoint}"
        headers = {"Accept": "application/json"}

        if self.api_key:
            headers["X-API-Key"] = self.api_key

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        logger.warning(f"Backend endpoint not found: {endpoint}")
                        return []
                    else:
                        text = await response.text()
                        raise Exception(f"Backend returned {response.status}: {text}")

        except asyncio.TimeoutError:
            raise Exception(f"Backend request timeout: {url}")
        except aiohttp.ClientError as e:
            raise Exception(f"Backend connection error: {e}")

    # ==================== Status ====================

    def get_status(self) -> Dict[str, Any]:
        """Get detailed sync status"""
        return {
            "backend_url": self.backend_url,
            "sync_interval_seconds": self.sync_interval,
            "is_running": self._running,
            "is_syncing": self._status.is_syncing,
            "last_sync": self._status.last_sync.isoformat() if self._status.last_sync else None,
            "last_error": self._status.last_error,
            "cached_configs": {
                "tags": self._status.tags_count,
                "alarms": self._status.alarms_count,
                "formulas": self._status.formulas_count,
            }
        }


# ==================== Singleton ====================

_config_sync_service: Optional[ConfigSyncService] = None


def init_config_sync(
    backend_url: str,
    api_key: Optional[str] = None,
    sync_interval_seconds: int = 60
) -> ConfigSyncService:
    """Initialize the config sync service singleton"""
    global _config_sync_service
    _config_sync_service = ConfigSyncService(
        backend_url=backend_url,
        api_key=api_key,
        sync_interval_seconds=sync_interval_seconds
    )
    return _config_sync_service


def get_config_sync() -> Optional[ConfigSyncService]:
    """Get the config sync service singleton"""
    return _config_sync_service
