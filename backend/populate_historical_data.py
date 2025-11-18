#!/usr/bin/env python3
"""
Populate InfluxDB with historical timeseries data

Generates realistic historical data for the last 7 days to enable:
- Chart visualization in frontend
- LSTM model validation
- Trend analysis
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta
import random
import math

# Add backend to path
sys.path.insert(0, '/app')

from app.services.optimized_influxdb_service import optimized_influxdb_service

# Historical data configuration (7 days back)
DAYS_BACK = 7
INTERVAL_MINUTES = 5  # Data point every 5 minutes
TOTAL_POINTS = (DAYS_BACK * 24 * 60) // INTERVAL_MINUTES

# Tag configurations with realistic patterns
TAG_CONFIGS = {
    'energy_consumption': {
        'base': 1100.0,
        'amplitude': 200.0,
        'noise': 30.0,
        'trend': 0.0,  # kWh
    },
    'production_rate': {
        'base': 100.0,
        'amplitude': 30.0,
        'noise': 10.0,
        'trend': 0.5,  # tons/h - slight increase over time
    },
    'conveyor_speed': {
        'base': 2.0,
        'amplitude': 0.5,
        'noise': 0.2,
        'trend': 0.0,  # m/s
    },
    'motor_temperature': {
        'base': 60.0,
        'amplitude': 15.0,
        'noise': 3.0,
        'trend': 0.1,  # °C - slight warming trend
    },
    'vibration_level': {
        'base': 2.5,
        'amplitude': 1.5,
        'noise': 0.5,
        'trend': 0.05,  # mm/s - degradation over time
    },
    'pressure_sensor_1': {
        'base': 5.0,
        'amplitude': 2.0,
        'noise': 0.5,
        'trend': 0.0,  # bar
    },
    'flow_rate_01': {
        'base': 30.0,
        'amplitude': 10.0,
        'noise': 3.0,
        'trend': 0.0,  # m3/h
    },
    'quality_index': {
        'base': 95.0,
        'amplitude': 5.0,
        'noise': 2.0,
        'trend': -0.02,  # % - slight degradation over time
    },
    'ambient_temperature': {
        'base': 25.0,
        'amplitude': 5.0,
        'noise': 1.0,
        'trend': 0.0,  # °C - daily variation
    },
    'humidity_level': {
        'base': 55.0,
        'amplitude': 15.0,
        'noise': 5.0,
        'trend': 0.0,  # %
    },
}


def generate_value(tag_name: str, point_index: int, total_points: int) -> float:
    """
    Generate realistic value for a tag at a specific point in time.

    Uses:
    - Sinusoidal pattern (daily/weekly cycles)
    - Random noise
    - Long-term trend
    - Occasional anomalies
    """
    config = TAG_CONFIGS[tag_name]

    # Time-based factor (0 to 1)
    time_factor = point_index / total_points

    # Daily cycle (24-hour pattern)
    daily_cycle = math.sin(2 * math.pi * point_index / (24 * 60 / INTERVAL_MINUTES))

    # Weekly cycle (7-day pattern)
    weekly_cycle = 0.3 * math.sin(2 * math.pi * point_index / (7 * 24 * 60 / INTERVAL_MINUTES))

    # Base value with trend
    base_value = config['base'] + (config['trend'] * time_factor * total_points)

    # Cyclic variation
    cyclic_variation = config['amplitude'] * (daily_cycle + weekly_cycle)

    # Random noise
    noise = random.gauss(0, config['noise'])

    # Occasional anomalies (1% chance)
    if random.random() < 0.01:
        noise += random.gauss(0, config['amplitude'])

    # Calculate final value
    value = base_value + cyclic_variation + noise

    # Ensure value is within reasonable bounds
    if tag_name == 'quality_index':
        value = max(85.0, min(100.0, value))
    elif tag_name == 'vibration_level':
        value = max(0.5, min(5.0, value))

    return round(value, 2)


async def populate_historical_data():
    """Populate InfluxDB with historical data"""
    print("=" * 70)
    print("POPULATING INFLUXDB WITH HISTORICAL DATA")
    print("=" * 70)
    print(f"Days back: {DAYS_BACK}")
    print(f"Interval: {INTERVAL_MINUTES} minutes")
    print(f"Total points per tag: {TOTAL_POINTS}")
    print(f"Total tags: {len(TAG_CONFIGS)}")
    print(f"Total data points: {TOTAL_POINTS * len(TAG_CONFIGS):,}")
    print("=" * 70)

    # Start time (7 days ago)
    start_time = datetime.utcnow() - timedelta(days=DAYS_BACK)

    # Generate data for each tag
    for tag_name, config in TAG_CONFIGS.items():
        print(f"\nGenerating data for '{tag_name}'...")

        batch_size = 500  # Write in batches for efficiency
        points_written = 0

        for batch_start in range(0, TOTAL_POINTS, batch_size):
            batch_end = min(batch_start + batch_size, TOTAL_POINTS)

            # Generate batch of data points
            batch_data = []
            for i in range(batch_start, batch_end):
                timestamp = start_time + timedelta(minutes=i * INTERVAL_MINUTES)
                value = generate_value(tag_name, i, TOTAL_POINTS)

                batch_data.append({
                    'tag_id': tag_name,  # Using tag name as ID
                    'value': value,
                    'timestamp': timestamp.isoformat() + 'Z',
                    'quality': 'GOOD'
                })

            # Write batch to InfluxDB
            try:
                success = optimized_influxdb_service.write_batch(batch_data)
                if success:
                    points_written += len(batch_data)
                else:
                    print(f"  ⚠ Batch write returned False")

                # Progress indicator
                progress = (points_written / TOTAL_POINTS) * 100
                print(f"  Progress: {progress:.1f}% ({points_written}/{TOTAL_POINTS} points)")

            except Exception as e:
                print(f"  ✗ Error writing batch: {e}")
                continue

        print(f"  ✓ Completed '{tag_name}': {points_written} points written")

    print("\n" + "=" * 70)
    print("✓ HISTORICAL DATA POPULATION COMPLETE!")
    print("=" * 70)
    print("\nYou can now:")
    print("  1. View charts in the frontend dashboard")
    print("  2. Validate LSTM predictions")
    print("  3. Analyze trends and patterns")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(populate_historical_data())
