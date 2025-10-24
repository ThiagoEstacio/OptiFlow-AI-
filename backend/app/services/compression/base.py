"""
Base classes for compression algorithms
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import time


@dataclass
class DataPoint:
    """
    Represents a single data point with timestamp and value.

    Attributes:
        timestamp: Unix timestamp in seconds (can be float for milliseconds)
        value: Numeric value
        quality: Quality code (Good, Bad, Uncertain)
        metadata: Optional additional metadata
    """
    timestamp: float
    value: float
    quality: str = "Good"
    metadata: Optional[dict] = None

    @classmethod
    def from_datetime(cls, dt: datetime, value: float, quality: str = "Good", metadata: Optional[dict] = None):
        """Create DataPoint from datetime object"""
        return cls(
            timestamp=dt.timestamp(),
            value=value,
            quality=quality,
            metadata=metadata
        )

    def to_datetime(self) -> datetime:
        """Convert timestamp to datetime object"""
        return datetime.fromtimestamp(self.timestamp)

    def __lt__(self, other):
        """Compare by timestamp for sorting"""
        return self.timestamp < other.timestamp


class CompressionAlgorithm(ABC):
    """
    Base class for all compression algorithms.

    Compression algorithms reduce data storage by eliminating redundant
    samples while maintaining data fidelity within acceptable bounds.
    """

    def __init__(self, config: dict):
        """
        Initialize compression algorithm.

        Args:
            config: Algorithm-specific configuration dictionary
        """
        self.config = config
        self.reset()

    @abstractmethod
    def reset(self) -> None:
        """Reset algorithm state"""
        pass

    @abstractmethod
    def add_sample(self, point: DataPoint) -> Optional[DataPoint]:
        """
        Add a new sample to the compression buffer.

        Args:
            point: New data point to process

        Returns:
            DataPoint to store, or None if sample is compressed out
        """
        pass

    @abstractmethod
    def flush(self) -> List[DataPoint]:
        """
        Flush any buffered data points.

        Called when forcing storage of pending samples
        (e.g., on shutdown or configuration change).

        Returns:
            List of buffered data points that should be stored
        """
        pass

    def get_statistics(self) -> dict:
        """
        Get compression statistics.

        Returns:
            Dictionary with statistics like compression ratio, samples processed, etc.
        """
        return {}

    def __repr__(self):
        return f"<{self.__class__.__name__} config={self.config}>"
