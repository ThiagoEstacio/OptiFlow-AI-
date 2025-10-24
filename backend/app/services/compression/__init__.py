"""
Data Compression Services

Compression algorithms for reducing data storage while maintaining data fidelity.
Used for time-series data from industrial sensors and process variables.
"""
from app.services.compression.base import CompressionAlgorithm, DataPoint
from app.services.compression.swinging_door import SwingingDoorCompression
from app.services.compression.boxcar import BoxCarCompression
from app.services.compression.deadband import DeadbandCompression

__all__ = [
    "CompressionAlgorithm",
    "DataPoint",
    "SwingingDoorCompression",
    "BoxCarCompression",
    "DeadbandCompression",
]
