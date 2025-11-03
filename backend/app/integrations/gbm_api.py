"""
GBM API Integration

Integration with GBM (Gestão de Berços e Movimentação) - Port Operations API.

GBM is a port operations management system that provides:
- Ship schedule and berthing information
- Real-time berth availability
- Loading operations data
- Terminal operations metrics
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class GBMShip(BaseModel):
    """Ship information from GBM API."""
    ship_name: str
    ship_imo: Optional[str] = None
    eta: Optional[datetime] = None  # Estimated Time of Arrival
    etb: Optional[datetime] = None  # Estimated Time of Berthing
    etd: Optional[datetime] = None  # Estimated Time of Departure
    berth_number: Optional[int] = None
    cargo_type: Optional[str] = None
    quantity: Optional[float] = None  # Expected tonnage
    status: str = "scheduled"


class GBMBerth(BaseModel):
    """Berth status from GBM API."""
    berth_number: int
    berth_name: str
    status: str  # available, occupied, maintenance
    current_ship: Optional[str] = None
    occupancy_start: Optional[datetime] = None
    expected_release: Optional[datetime] = None


class GBMLoadingOperation(BaseModel):
    """Loading operation data from GBM API."""
    operation_id: str
    ship_name: str
    berth_number: int
    product_type: str
    loaded_tonnage: float
    loading_start: datetime
    loading_end: Optional[datetime] = None
    loading_rate: Optional[float] = None  # tons/hour
    status: str


class GBMAPIClient:
    """
    Client for GBM Port Operations API.

    Provides methods to fetch ship schedules, berth status, and loading operations.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize GBM API client.

        Args:
            base_url: Base URL of GBM API (e.g., "https://api.gbm.com.br")
            api_key: API key for authentication (if required)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout

        # HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._get_headers()
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    async def fetch_ship_schedule(
        self,
        terminal_id: Optional[str] = None,
        days_ahead: int = 7
    ) -> List[GBMShip]:
        """
        Fetch upcoming ship schedule.

        Args:
            terminal_id: Terminal identifier (optional)
            days_ahead: Number of days to look ahead

        Returns:
            List of scheduled ships
        """
        try:
            params = {
                "days_ahead": days_ahead
            }

            if terminal_id:
                params["terminal_id"] = terminal_id

            response = await self.client.get("/api/v1/ships/schedule", params=params)
            response.raise_for_status()

            data = response.json()

            # Parse response
            ships = []
            for ship_data in data.get("ships", []):
                try:
                    ship = GBMShip(
                        ship_name=ship_data.get("name"),
                        ship_imo=ship_data.get("imo"),
                        eta=datetime.fromisoformat(ship_data.get("eta")) if ship_data.get("eta") else None,
                        etb=datetime.fromisoformat(ship_data.get("etb")) if ship_data.get("etb") else None,
                        etd=datetime.fromisoformat(ship_data.get("etd")) if ship_data.get("etd") else None,
                        berth_number=ship_data.get("berth_number"),
                        cargo_type=ship_data.get("cargo_type"),
                        quantity=ship_data.get("quantity"),
                        status=ship_data.get("status", "scheduled"),
                    )
                    ships.append(ship)
                except Exception as e:
                    logger.error(f"Error parsing ship data: {e}")
                    continue

            logger.info(f"Fetched {len(ships)} ships from GBM API")
            return ships

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching ship schedule: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching ship schedule: {e}")
            return []

    async def fetch_berth_status(
        self,
        terminal_id: Optional[str] = None
    ) -> List[GBMBerth]:
        """
        Fetch real-time berth availability.

        Args:
            terminal_id: Terminal identifier (optional)

        Returns:
            List of berth statuses
        """
        try:
            params = {}
            if terminal_id:
                params["terminal_id"] = terminal_id

            response = await self.client.get("/api/v1/berths/status", params=params)
            response.raise_for_status()

            data = response.json()

            # Parse response
            berths = []
            for berth_data in data.get("berths", []):
                try:
                    berth = GBMBerth(
                        berth_number=berth_data.get("number"),
                        berth_name=berth_data.get("name"),
                        status=berth_data.get("status", "available"),
                        current_ship=berth_data.get("current_ship"),
                        occupancy_start=datetime.fromisoformat(berth_data.get("occupancy_start")) if berth_data.get("occupancy_start") else None,
                        expected_release=datetime.fromisoformat(berth_data.get("expected_release")) if berth_data.get("expected_release") else None,
                    )
                    berths.append(berth)
                except Exception as e:
                    logger.error(f"Error parsing berth data: {e}")
                    continue

            logger.info(f"Fetched {len(berths)} berths from GBM API")
            return berths

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching berth status: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching berth status: {e}")
            return []

    async def fetch_loading_operations(
        self,
        terminal_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[GBMLoadingOperation]:
        """
        Fetch loading operations data.

        Args:
            terminal_id: Terminal identifier (optional)
            start_date: Start date for filtering
            end_date: End date for filtering

        Returns:
            List of loading operations
        """
        try:
            params = {}

            if terminal_id:
                params["terminal_id"] = terminal_id
            if start_date:
                params["start_date"] = start_date.isoformat()
            if end_date:
                params["end_date"] = end_date.isoformat()

            response = await self.client.get("/api/v1/loading/operations", params=params)
            response.raise_for_status()

            data = response.json()

            # Parse response
            operations = []
            for op_data in data.get("operations", []):
                try:
                    operation = GBMLoadingOperation(
                        operation_id=op_data.get("id"),
                        ship_name=op_data.get("ship_name"),
                        berth_number=op_data.get("berth_number"),
                        product_type=op_data.get("product_type"),
                        loaded_tonnage=op_data.get("loaded_tonnage", 0),
                        loading_start=datetime.fromisoformat(op_data.get("loading_start")),
                        loading_end=datetime.fromisoformat(op_data.get("loading_end")) if op_data.get("loading_end") else None,
                        loading_rate=op_data.get("loading_rate"),
                        status=op_data.get("status"),
                    )
                    operations.append(operation)
                except Exception as e:
                    logger.error(f"Error parsing operation data: {e}")
                    continue

            logger.info(f"Fetched {len(operations)} operations from GBM API")
            return operations

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching loading operations: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching loading operations: {e}")
            return []

    async def sync_ship_schedule(self, db_session, site_id: int) -> Dict[str, Any]:
        """
        Synchronize ship schedule with local database.

        Args:
            db_session: Database session
            site_id: Site ID for storing ships

        Returns:
            Sync statistics
        """
        from app.models.operational_data import ShipLoading

        try:
            # Fetch ships from GBM
            ships = await self.fetch_ship_schedule()

            created_count = 0
            updated_count = 0
            skipped_count = 0

            for gbm_ship in ships:
                # Check if ship already exists
                from sqlalchemy import select
                result = await db_session.execute(
                    select(ShipLoading).where(
                        ShipLoading.ship_name == gbm_ship.ship_name,
                        ShipLoading.site_id == site_id,
                        ShipLoading.status.in_(["scheduled", "arrived"])
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing ship
                    if gbm_ship.etb:
                        existing.berthing_time = gbm_ship.etb
                    if gbm_ship.status:
                        existing.status = gbm_ship.status

                    updated_count += 1
                else:
                    # Create new ship loading entry
                    if gbm_ship.quantity and gbm_ship.cargo_type and gbm_ship.berth_number:
                        ship_loading = ShipLoading(
                            ship_name=gbm_ship.ship_name,
                            ship_imo=gbm_ship.ship_imo,
                            berth_number=gbm_ship.berth_number,
                            product_type=gbm_ship.cargo_type,
                            target_tonnage=gbm_ship.quantity,
                            arrival_time=gbm_ship.eta,
                            berthing_time=gbm_ship.etb,
                            status=gbm_ship.status,
                            site_id=site_id,
                        )
                        db_session.add(ship_loading)
                        created_count += 1
                    else:
                        skipped_count += 1

            await db_session.commit()

            logger.info(
                f"GBM sync completed: {created_count} created, "
                f"{updated_count} updated, {skipped_count} skipped"
            )

            return {
                "status": "success",
                "created": created_count,
                "updated": updated_count,
                "skipped": skipped_count,
                "total_fetched": len(ships),
            }

        except Exception as e:
            await db_session.rollback()
            logger.error(f"Error syncing ship schedule: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
