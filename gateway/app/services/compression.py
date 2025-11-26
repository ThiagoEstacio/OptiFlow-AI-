"""
Swinging Door Compression Algorithm
====================================

Implementation of the Swinging Door Trending (SDT) algorithm for data compression.
This is the same algorithm used by OSIsoft PI Data Archive and other industrial historians.

The algorithm works by:
1. Keeping track of an "opening" point (last archived value)
2. Drawing imaginary "doors" from the opening point through subsequent values
3. Only archiving a value when the doors can no longer "swing" to include the next point

Benefits:
- Significant data reduction (often 10:1 or better)
- Preserves data trends and inflection points
- Maintains engineering accuracy within configured tolerance
- Real-time operation with minimal memory footprint
"""

import math
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class CompressionMode(str, Enum):
    """Compression algorithm modes"""
    NONE = "none"              # No compression, store all values
    DEADBAND = "deadband"      # Simple deadband filtering
    SWINGING_DOOR = "swinging_door"  # Full SDT compression
    EXCEPTION = "exception"    # Exception-based (hybrid)


@dataclass
class CompressionConfig:
    """Configuration for data compression"""
    mode: CompressionMode = CompressionMode.SWINGING_DOOR

    # Compression deviation (engineering units)
    # Values within this tolerance are compressed out
    comp_dev: float = 0.5

    # Compression deviation as percentage (0-100)
    # If set, overrides comp_dev with: (max - min) * comp_dev_percent / 100
    comp_dev_percent: Optional[float] = None

    # Maximum time between archived values (seconds)
    # Ensures at least one value per max_time even if no change
    comp_max_time: float = 3600.0  # 1 hour default

    # Minimum time between archived values (seconds)
    # Prevents excessive archiving on noisy signals
    comp_min_time: float = 0.0

    # Exception deviation (for hybrid mode)
    # Must exceed this to immediately archive
    exc_dev: Optional[float] = None

    # Value range for percentage calculations
    range_min: float = 0.0
    range_max: float = 100.0


@dataclass
class CompressionState:
    """State for the Swinging Door algorithm"""
    # Opening point (last archived value)
    opening_value: Optional[float] = None
    opening_time: Optional[datetime] = None

    # Previous point (for door calculations)
    prev_value: Optional[float] = None
    prev_time: Optional[datetime] = None

    # Door slopes (upper and lower bounds)
    slope_high: Optional[float] = None
    slope_low: Optional[float] = None

    # Statistics
    values_received: int = 0
    values_archived: int = 0
    compression_ratio: float = 0.0

    # Held value (waiting to be archived)
    held_value: Optional[float] = None
    held_time: Optional[datetime] = None


class SwingingDoorCompressor:
    """
    Swinging Door Trending (SDT) Compression Algorithm

    This implementation follows the OSIsoft PI methodology:
    1. First value always archived as "opening"
    2. Subsequent values update door slopes
    3. When a value falls outside both doors, archive previous value
    4. Previous value becomes new opening

    Visual representation:
    ```
           slope_high (upper door)
          /
    O----*----X  (current value outside doors)
          \\
           slope_low (lower door)

    O = Opening point (last archived)
    * = Previous point (will be archived)
    X = Current point (triggers archive)
    ```
    """

    def __init__(self):
        # State per tag: tag_id -> CompressionState
        self._states: Dict[str, CompressionState] = {}

        # Config per tag: tag_id -> CompressionConfig
        self._configs: Dict[str, CompressionConfig] = {}

        # Statistics
        self._total_received = 0
        self._total_archived = 0

        logger.info("Swinging Door Compressor initialized")

    def configure_tag(self, tag_id: str, config: CompressionConfig):
        """Configure compression for a tag"""
        self._configs[tag_id] = config
        self._states[tag_id] = CompressionState()
        logger.debug(f"Configured compression for {tag_id}: mode={config.mode}, dev={config.comp_dev}")

    def remove_tag(self, tag_id: str):
        """Remove compression configuration for a tag"""
        self._configs.pop(tag_id, None)
        self._states.pop(tag_id, None)

    def process_value(
        self,
        tag_id: str,
        value: float,
        timestamp: datetime,
        quality: str = "Good"
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Process a value through compression algorithm.

        Args:
            tag_id: Tag identifier
            value: Current value
            timestamp: Value timestamp
            quality: Quality code

        Returns:
            Tuple of:
            - should_archive: True if this value should be archived
            - archive_data: Data to archive (may be held value, not current)
            - current_data: Current value data (for real-time display)
        """
        config = self._configs.get(tag_id)
        if not config:
            # No compression configured, archive everything
            return True, self._make_archive_data(tag_id, value, timestamp, quality), None

        state = self._states.get(tag_id)
        if not state:
            state = CompressionState()
            self._states[tag_id] = state

        self._total_received += 1
        state.values_received += 1

        # Current value data (always returned for real-time)
        current_data = self._make_archive_data(tag_id, value, timestamp, quality)

        # Route to appropriate compression method
        if config.mode == CompressionMode.NONE:
            return True, current_data, None

        elif config.mode == CompressionMode.DEADBAND:
            return self._process_deadband(tag_id, value, timestamp, quality, config, state)

        elif config.mode == CompressionMode.SWINGING_DOOR:
            return self._process_swinging_door(tag_id, value, timestamp, quality, config, state)

        elif config.mode == CompressionMode.EXCEPTION:
            return self._process_exception(tag_id, value, timestamp, quality, config, state)

        return True, current_data, None

    def _process_deadband(
        self, tag_id: str, value: float, timestamp: datetime,
        quality: str, config: CompressionConfig, state: CompressionState
    ) -> Tuple[bool, Optional[Dict], Optional[Dict]]:
        """Simple deadband compression"""
        current_data = self._make_archive_data(tag_id, value, timestamp, quality)

        # First value
        if state.opening_value is None:
            state.opening_value = value
            state.opening_time = timestamp
            self._total_archived += 1
            state.values_archived += 1
            return True, current_data, None

        # Check deadband
        deviation = self._get_deviation(config)
        if abs(value - state.opening_value) >= deviation:
            state.opening_value = value
            state.opening_time = timestamp
            self._total_archived += 1
            state.values_archived += 1
            return True, current_data, None

        # Check max time
        if self._exceeded_max_time(state.opening_time, timestamp, config.comp_max_time):
            state.opening_value = value
            state.opening_time = timestamp
            self._total_archived += 1
            state.values_archived += 1
            return True, current_data, None

        # Compressed out
        state.compression_ratio = state.values_archived / state.values_received if state.values_received > 0 else 0
        return False, None, current_data

    def _process_swinging_door(
        self, tag_id: str, value: float, timestamp: datetime,
        quality: str, config: CompressionConfig, state: CompressionState
    ) -> Tuple[bool, Optional[Dict], Optional[Dict]]:
        """
        Full Swinging Door Trending algorithm

        The algorithm maintains two "doors" hinged at the opening point:
        - Upper door: highest slope that still includes all previous points + deviation
        - Lower door: lowest slope that still includes all previous points - deviation

        When a new point falls outside both doors, we archive the previous point
        and start a new compression interval.
        """
        current_data = self._make_archive_data(tag_id, value, timestamp, quality)
        deviation = self._get_deviation(config)

        # First value - archive as opening
        if state.opening_value is None:
            state.opening_value = value
            state.opening_time = timestamp
            state.prev_value = value
            state.prev_time = timestamp
            state.slope_high = None
            state.slope_low = None
            self._total_archived += 1
            state.values_archived += 1
            return True, current_data, None

        # Calculate time delta from opening
        dt = (timestamp - state.opening_time).total_seconds()
        if dt <= 0:
            dt = 0.001  # Avoid division by zero

        # Calculate slopes to current point with deviation
        slope_to_high = ((value + deviation) - state.opening_value) / dt
        slope_to_low = ((value - deviation) - state.opening_value) / dt

        # First point after opening - initialize doors
        if state.slope_high is None:
            state.slope_high = slope_to_high
            state.slope_low = slope_to_low
            state.prev_value = value
            state.prev_time = timestamp
            state.held_value = value
            state.held_time = timestamp
            return False, None, current_data

        # Narrow the doors (tighten slopes)
        # Upper door can only go down, lower door can only go up
        state.slope_high = min(state.slope_high, slope_to_high)
        state.slope_low = max(state.slope_low, slope_to_low)

        # Check if doors have crossed (compression exception)
        if state.slope_low > state.slope_high:
            # Archive the previous (held) value
            archive_data = self._make_archive_data(
                tag_id,
                state.held_value,
                state.held_time,
                quality
            )

            # Previous value becomes new opening
            state.opening_value = state.held_value
            state.opening_time = state.held_time

            # Recalculate doors from new opening to current value
            dt_new = (timestamp - state.opening_time).total_seconds()
            if dt_new > 0:
                state.slope_high = ((value + deviation) - state.opening_value) / dt_new
                state.slope_low = ((value - deviation) - state.opening_value) / dt_new
            else:
                state.slope_high = None
                state.slope_low = None

            state.prev_value = value
            state.prev_time = timestamp
            state.held_value = value
            state.held_time = timestamp

            self._total_archived += 1
            state.values_archived += 1
            state.compression_ratio = state.values_archived / state.values_received

            return True, archive_data, current_data

        # Check max time exceeded
        if self._exceeded_max_time(state.opening_time, timestamp, config.comp_max_time):
            # Archive current value and reset
            state.opening_value = value
            state.opening_time = timestamp
            state.prev_value = value
            state.prev_time = timestamp
            state.slope_high = None
            state.slope_low = None
            state.held_value = None
            state.held_time = None

            self._total_archived += 1
            state.values_archived += 1
            state.compression_ratio = state.values_archived / state.values_received

            return True, current_data, None

        # Value compressed - update held value
        state.prev_value = value
        state.prev_time = timestamp
        state.held_value = value
        state.held_time = timestamp
        state.compression_ratio = state.values_archived / state.values_received

        return False, None, current_data

    def _process_exception(
        self, tag_id: str, value: float, timestamp: datetime,
        quality: str, config: CompressionConfig, state: CompressionState
    ) -> Tuple[bool, Optional[Dict], Optional[Dict]]:
        """
        Exception-based compression (hybrid mode)

        Combines:
        - Exception deviation: immediately archive if exceeded
        - Compression deviation: normal SDT compression
        """
        current_data = self._make_archive_data(tag_id, value, timestamp, quality)

        # First value
        if state.opening_value is None:
            state.opening_value = value
            state.opening_time = timestamp
            self._total_archived += 1
            state.values_archived += 1
            return True, current_data, None

        # Check exception deviation (immediate archive)
        exc_dev = config.exc_dev or (config.comp_dev * 2)  # Default: 2x compression dev
        if abs(value - state.opening_value) >= exc_dev:
            state.opening_value = value
            state.opening_time = timestamp
            self._total_archived += 1
            state.values_archived += 1
            return True, current_data, None

        # Fall through to swinging door
        return self._process_swinging_door(tag_id, value, timestamp, quality, config, state)

    def _get_deviation(self, config: CompressionConfig) -> float:
        """Calculate deviation value"""
        if config.comp_dev_percent is not None:
            range_span = config.range_max - config.range_min
            return range_span * config.comp_dev_percent / 100.0
        return config.comp_dev

    def _exceeded_max_time(
        self, opening_time: Optional[datetime],
        current_time: datetime,
        max_time: float
    ) -> bool:
        """Check if max compression time exceeded"""
        if opening_time is None:
            return True
        return (current_time - opening_time).total_seconds() >= max_time

    def _make_archive_data(
        self, tag_id: str, value: float,
        timestamp: datetime, quality: str
    ) -> Dict[str, Any]:
        """Create archive data structure"""
        return {
            'tag_id': tag_id,
            'value': value,
            'timestamp': timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
            'quality': quality,
            'compressed': True
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall compression statistics"""
        ratio = (1 - (self._total_archived / self._total_received)) * 100 if self._total_received > 0 else 0

        return {
            'total_received': self._total_received,
            'total_archived': self._total_archived,
            'total_compressed': self._total_received - self._total_archived,
            'compression_ratio_percent': round(ratio, 2),
            'configured_tags': len(self._configs)
        }

    def get_tag_statistics(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """Get compression statistics for a specific tag"""
        state = self._states.get(tag_id)
        if not state:
            return None

        config = self._configs.get(tag_id)
        ratio = (1 - (state.values_archived / state.values_received)) * 100 if state.values_received > 0 else 0

        return {
            'tag_id': tag_id,
            'mode': config.mode if config else 'unknown',
            'comp_dev': config.comp_dev if config else None,
            'values_received': state.values_received,
            'values_archived': state.values_archived,
            'compression_ratio_percent': round(ratio, 2),
            'opening_value': state.opening_value,
            'opening_time': state.opening_time.isoformat() if state.opening_time else None
        }

    def flush_tag(self, tag_id: str) -> Optional[Dict[str, Any]]:
        """
        Flush any held value for a tag (e.g., on shutdown)

        Returns the held value if any, which should be archived.
        """
        state = self._states.get(tag_id)
        if not state or state.held_value is None:
            return None

        archive_data = self._make_archive_data(
            tag_id,
            state.held_value,
            state.held_time,
            "Good"
        )

        # Reset held value
        state.held_value = None
        state.held_time = None

        return archive_data

    def flush_all(self) -> List[Dict[str, Any]]:
        """Flush all held values (e.g., on shutdown)"""
        flushed = []
        for tag_id in list(self._states.keys()):
            data = self.flush_tag(tag_id)
            if data:
                flushed.append(data)
        return flushed


# Global instance
_compressor: Optional[SwingingDoorCompressor] = None


def get_compressor() -> SwingingDoorCompressor:
    """Get or create the global compressor instance"""
    global _compressor
    if _compressor is None:
        _compressor = SwingingDoorCompressor()
    return _compressor
