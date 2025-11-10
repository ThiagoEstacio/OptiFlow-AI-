"""
Simulator HTTP Polling Service
Polls the grain terminal simulator and sends data to backend + InfluxDB
"""
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SimulatorPoller:
    """
    Service that polls the simulator HTTP endpoint and sends data to backend
    
    Flow: Simulator → Gateway (this) → Backend API → InfluxDB
    """
    
    def __init__(
        self,
        simulator_url: str = "http://localhost:8000",
        backend_client = None,
        poll_interval_s: float = 1.0
    ):
        """
        Initialize simulator poller
        
        Args:
            simulator_url: URL of the simulator API
            backend_client: Backend client instance for sending data
            poll_interval_s: Polling interval in seconds
        """
        self.simulator_url = simulator_url
        self.backend_client = backend_client
        self.poll_interval_s = poll_interval_s
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False
        self.tag_mapping: Dict[str, str] = {}  # tag_name -> tag_id
        
    async def initialize(self):
        """Initialize HTTP session and load tag mapping"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
            logger.info(f"✅ Simulator poller initialized: {self.simulator_url}")
        
        # Load tag mapping from backend
        await self._load_tag_mapping()
    
    async def _load_tag_mapping(self):
        """Load tag name to UUID mapping from backend"""
        try:
            if not self.backend_client or not self.backend_client.session:
                logger.warning("Backend client not available for tag mapping")
                return
            
            async with self.backend_client.session.get("/api/v1/tags/") as response:
                if response.status == 200:
                    tags = await response.json()
                    self.tag_mapping = {tag['name']: tag['id'] for tag in tags}
                    logger.info(f"✅ Loaded {len(self.tag_mapping)} tag mappings")
                else:
                    logger.error(f"Failed to load tag mapping: {response.status}")
        except Exception as e:
            logger.error(f"Error loading tag mapping: {e}")
    
    async def poll_once(self) -> Optional[Dict[str, Any]]:
        """
        Poll simulator status once
        
        Returns:
            Simulator status dict or None
        """
        try:
            url = f"{self.simulator_url}/api/v1/simulator/status"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Simulator poll failed: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error polling simulator: {e}")
            return None
    
    def _extract_datapoints(self, status: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract all data points from simulator status
        
        Args:
            status: Simulator status dictionary
            
        Returns:
            List of data points ready for backend
        """
        points = []
        timestamp = datetime.utcnow()
        
        # System values (lightweight simulator format)
        system = status.get('system', {})
        self._add_point(points, 'SYSTEM_RUNNING_PV', 1.0 if system.get('running') else 0.0, timestamp)
        self._add_point(points, 'SYSTEM_TIME_S_PV', system.get('time_s'), timestamp)
        self._add_point(points, 'TOTAL_MASS_T_PV', system.get('total_mass_t'), timestamp)
        self._add_point(points, 'TOTAL_KWH_PV', system.get('total_kWh'), timestamp)
        self._add_point(points, 'WAREHOUSE_LEVEL_PCT_PV', system.get('warehouse_level_pct'), timestamp)
        self._add_point(points, 'KWH_PER_TON_PV', system.get('kWh_per_ton'), timestamp)
        self._add_point(points, 'COST_BRL_PV', system.get('cost_BRL'), timestamp)
        
        # Gates (lightweight simulator returns list with 'name' key)
        for gate in status.get('gates', []):
            gate_name = gate.get('name', '')
            # Extract gate number from name (e.g., "GATE_01" -> "01")
            if '_' in gate_name:
                gate_num = gate_name.split('_')[-1]
                self._add_point(points, f'ARZ_GATES_GATE{gate_num}_POSICAO_PV', gate.get('opening_pct'), timestamp)
                self._add_point(points, f'ARZ_GATES_GATE{gate_num}_VAZAO_TPH_PV', gate.get('flow_tph'), timestamp)

        # Belts (lightweight simulator returns list with 'name' key)
        for belt in status.get('belts', []):
            belt_name = belt.get('name', '')
            self._add_point(points, f'{belt_name}_RUNNING_PV', 1.0 if belt.get('running') else 0.0, timestamp)
            self._add_point(points, f'{belt_name}_SPEED_MPS_PV', belt.get('speed_mps'), timestamp)
            self._add_point(points, f'{belt_name}_FLOW_TPH_PV', belt.get('flow_tph'), timestamp)
            self._add_point(points, f'{belt_name}_LOAD_PCT_PV', belt.get('load_pct'), timestamp)
            self._add_point(points, f'{belt_name}_CURRENT_A_PV', belt.get('current_a'), timestamp)
            self._add_point(points, f'{belt_name}_POWER_KW_PV', belt.get('power_kw'), timestamp)
            self._add_point(points, f'{belt_name}_TEMP_C_PV', belt.get('temp_c'), timestamp)
            self._add_point(points, f'{belt_name}_MISALIGNMENT_PV', belt.get('misalignment'), timestamp)
        
        # NOTE: Lightweight simulator does not include elevator and balance equipment
        # These were part of the old DEM-based simulator
        # Uncomment below if switching back to full simulator:

        # # Elevator
        # elevator = status.get('elevator', {})
        # self._add_point(points, 'ELV01_RUNNING_PV', 1.0 if elevator.get('running') else 0.0, timestamp)
        # self._add_point(points, 'ELV01_FLOW_TPH_PV', elevator.get('flow_tph'), timestamp)
        # self._add_point(points, 'ELV01_POWER_KW_PV', elevator.get('power_kW'), timestamp)
        # self._add_point(points, 'ELV01_TEMP_MOTOR_C_PV', elevator.get('temp_motor_C'), timestamp)

        # # Balance
        # balance = status.get('balance', {})
        # self._add_point(points, 'BAL01_RUNNING_PV', 1.0 if balance.get('running') else 0.0, timestamp)
        # self._add_point(points, 'BAL01_WEIGHT_KG_PV', balance.get('weight_kg'), timestamp)
        # self._add_point(points, 'BAL01_FLOW_TPH_PV', balance.get('avg_flow_tph'), timestamp)
        
        # Shiploader (lightweight simulator format)
        shiploader = status.get('shiploader', {})
        self._add_point(points, 'SLD01_SETPOINT_TPH_PV', shiploader.get('setpoint_tph'), timestamp)
        self._add_point(points, 'SLD01_FLOW_TPH_PV', shiploader.get('flow_tph'), timestamp)
        self._add_point(points, 'SLD01_POWER_KW_PV', shiploader.get('power_kw'), timestamp)
        self._add_point(points, 'SLD01_CURRENT_A_PV', shiploader.get('current_a'), timestamp)
        
        return points
    
    def _add_point(self, points: List, tag_name: str, value: Any, timestamp: datetime):
        """Helper to add a data point if tag exists in mapping"""
        if tag_name in self.tag_mapping and value is not None:
            points.append({
                'tag_id': self.tag_mapping[tag_name],
                'value': float(value),
                'timestamp': timestamp.isoformat(),
                'quality': 'good'
            })
    
    async def send_to_backend(self, points: List[Dict[str, Any]]) -> bool:
        """
        Send data points to backend API (which writes to InfluxDB)
        
        Args:
            points: List of data points
            
        Returns:
            True if successful
        """
        if not self.backend_client:
            logger.warning("No backend client configured")
            return False
        
        try:
            success = await self.backend_client.send_timeseries_batch(points)
            if success:
                logger.debug(f"✅ Sent {len(points)} points to backend → InfluxDB")
            return success
        except Exception as e:
            logger.error(f"Error sending to backend: {e}")
            return False
    
    async def start_polling(self):
        """Start continuous polling loop"""
        self.running = True
        logger.info(f"🔄 Starting simulator polling (interval: {self.poll_interval_s}s)")
        
        while self.running:
            try:
                # Step simulator
                step_url = f"{self.simulator_url}/api/v1/simulator/step"
                async with self.session.post(step_url, params={'dt_s': self.poll_interval_s}) as response:
                    if response.status != 200:
                        logger.warning(f"Simulator step failed: {response.status}")
                
                # Poll status
                status = await self.poll_once()
                
                if status:
                    # Extract data points
                    points = self._extract_datapoints(status)
                    
                    if points:
                        # Send to backend → InfluxDB
                        await self.send_to_backend(points)
                    else:
                        logger.debug("No data points extracted from simulator")
                else:
                    logger.warning("Failed to poll simulator")
                
                # Wait for next interval
                await asyncio.sleep(self.poll_interval_s)
                
            except asyncio.CancelledError:
                logger.info("Polling cancelled")
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(self.poll_interval_s)
    
    def stop_polling(self):
        """Stop polling loop"""
        self.running = False
        logger.info("⏹️  Stopping simulator polling")
    
    async def close(self):
        """Close resources"""
        self.stop_polling()
        if self.session:
            await self.session.close()
            self.session = None
