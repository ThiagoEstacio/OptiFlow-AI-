#!/usr/bin/env python3
"""
Script para gerar dados históricos de energia no InfluxDB para treinamento do modelo ML.
Gera >1000 pontos de dados com padrões realistas de consumo industrial.
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta
import random
import math

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


# InfluxDB Configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "optiflow-super-secret-auth-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "optiflow")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "optiflow")

# Energy tag IDs (matching gateway configuration)
ENERGY_TAGS = {
    "tag_eletrocentro_pm_geral_kwh_b0ff6a": "Eletrocentro_PM_GERAL_KWH",
    "tag_eletrocentro_pm_geral_kvarh_aee1d7": "Eletrocentro_PM_GERAL_KVARH",
    "tag_eletrocentro_pm_ccm01_kwh_6de263": "Eletrocentro_PM_CCM01_KWH",
    "tag_utilidades_energia_consumototal_kwh_2d7040": "Utilidades_Energia_ConsumoTotal_kWh",
}


def generate_consumption_pattern(hour: int, day_of_week: int, base_consumption: float) -> float:
    """
    Generate realistic industrial energy consumption pattern.

    Patterns:
    - Peak hours (6-18h): Higher consumption (production)
    - Night hours (22-6h): Lower consumption (maintenance/idle)
    - Peak tariff hours (18-21h): Slightly reduced (load management)
    - Weekends: 60% of weekday consumption
    """
    # Base multiplier
    multiplier = 1.0

    # Time of day pattern
    if 6 <= hour < 12:
        # Morning ramp-up
        multiplier = 0.8 + (hour - 6) * 0.05  # 0.8 -> 1.1
    elif 12 <= hour < 14:
        # Lunch break
        multiplier = 0.9
    elif 14 <= hour < 18:
        # Afternoon production
        multiplier = 1.1 + random.uniform(-0.1, 0.1)
    elif 18 <= hour < 21:
        # Peak tariff - load reduction
        multiplier = 0.85
    elif 21 <= hour < 23:
        # Evening wind-down
        multiplier = 0.6
    else:
        # Night shift (minimal)
        multiplier = 0.4

    # Weekend reduction
    if day_of_week >= 5:  # Saturday, Sunday
        multiplier *= 0.6

    # Add some noise
    noise = random.uniform(-0.05, 0.05)
    multiplier += noise

    return base_consumption * multiplier


def generate_cumulative_meter_data(
    start_time: datetime,
    end_time: datetime,
    interval_minutes: int = 15,
    initial_value: float = 66300000.0,  # Starting cumulative kWh
    base_hourly_consumption: float = 150.0  # Average kWh per hour
) -> list:
    """
    Generate cumulative meter readings (like real energy meters).
    Each reading is higher than the previous one.
    """
    data_points = []
    current_time = start_time
    current_value = initial_value

    while current_time <= end_time:
        hour = current_time.hour
        day_of_week = current_time.weekday()

        # Calculate consumption for this interval
        hourly_rate = generate_consumption_pattern(hour, day_of_week, base_hourly_consumption)
        interval_consumption = hourly_rate * (interval_minutes / 60.0)

        # Add to cumulative value
        current_value += interval_consumption

        data_points.append({
            "timestamp": current_time,
            "value": round(current_value, 2)
        })

        current_time += timedelta(minutes=interval_minutes)

    return data_points


def generate_reactive_power_data(active_power_data: list, power_factor: float = 0.92) -> list:
    """
    Generate reactive power (kVARh) based on active power and power factor.
    """
    reactive_data = []

    # Calculate reactive power factor
    # PF = P / sqrt(P^2 + Q^2) => Q = P * sqrt(1/PF^2 - 1)
    q_factor = math.sqrt(1 / (power_factor ** 2) - 1)

    for point in active_power_data:
        reactive_value = point["value"] * q_factor * 0.3  # Scale for typical industrial
        reactive_data.append({
            "timestamp": point["timestamp"],
            "value": round(reactive_value, 2)
        })

    return reactive_data


def write_to_influxdb(client: InfluxDBClient, tag_id: str, tag_name: str, data_points: list):
    """Write data points to InfluxDB."""
    write_api = client.write_api(write_options=SYNCHRONOUS)

    batch_size = 1000
    total_points = len(data_points)

    print(f"  Writing {total_points} points for {tag_name}...")

    for i in range(0, total_points, batch_size):
        batch = data_points[i:i + batch_size]
        points = []

        for dp in batch:
            point = (
                Point("tag_data")
                .tag("tag_id", tag_id)
                .tag("tag_name", tag_name)
                .field("value", dp["value"])
                .field("quality", "good")
                .time(dp["timestamp"], WritePrecision.S)
            )
            points.append(point)

        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)
        print(f"    Written batch {i // batch_size + 1}/{(total_points + batch_size - 1) // batch_size}")

    print(f"  Completed {tag_name}: {total_points} points")


def main():
    print("=" * 60)
    print("OptiFlow AI - Energy Training Data Generator")
    print("=" * 60)

    # Time range: 30 days of historical data
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=30)

    print(f"\nGenerating data from {start_time} to {end_time}")
    print(f"Interval: 15 minutes")
    print(f"Expected points per tag: ~{30 * 24 * 4} = ~2880 points")

    # Connect to InfluxDB
    print(f"\nConnecting to InfluxDB at {INFLUXDB_URL}...")
    client = InfluxDBClient(
        url=INFLUXDB_URL,
        token=INFLUXDB_TOKEN,
        org=INFLUXDB_ORG
    )

    # Verify connection
    try:
        health = client.health()
        print(f"InfluxDB status: {health.status}")
    except Exception as e:
        print(f"Error connecting to InfluxDB: {e}")
        print("Make sure InfluxDB is running and accessible.")
        return

    # Generate data for main energy meter (cumulative kWh)
    print("\n" + "-" * 40)
    print("Generating main energy meter data (cumulative kWh)...")
    main_kwh_data = generate_cumulative_meter_data(
        start_time=start_time,
        end_time=end_time,
        interval_minutes=15,
        initial_value=66300000.0,
        base_hourly_consumption=150.0
    )
    print(f"Generated {len(main_kwh_data)} data points")

    # Generate reactive power data
    print("\nGenerating reactive power data (kVARh)...")
    kvarh_data = generate_reactive_power_data(main_kwh_data, power_factor=0.92)
    print(f"Generated {len(kvarh_data)} data points")

    # Generate CCM01 data (subset of main consumption)
    print("\nGenerating CCM01 meter data...")
    ccm01_data = generate_cumulative_meter_data(
        start_time=start_time,
        end_time=end_time,
        interval_minutes=15,
        initial_value=15000000.0,
        base_hourly_consumption=45.0  # ~30% of main
    )
    print(f"Generated {len(ccm01_data)} data points")

    # Generate Utilidades data
    print("\nGenerating Utilidades meter data...")
    utilidades_data = generate_cumulative_meter_data(
        start_time=start_time,
        end_time=end_time,
        interval_minutes=15,
        initial_value=8500000.0,
        base_hourly_consumption=25.0  # Utilities
    )
    print(f"Generated {len(utilidades_data)} data points")

    # Write all data to InfluxDB
    print("\n" + "-" * 40)
    print("Writing data to InfluxDB...")

    # Main kWh meter
    write_to_influxdb(
        client,
        "tag_eletrocentro_pm_geral_kwh_b0ff6a",
        "Eletrocentro_PM_GERAL_KWH",
        main_kwh_data
    )

    # kVARh meter
    write_to_influxdb(
        client,
        "tag_eletrocentro_pm_geral_kvarh_aee1d7",
        "Eletrocentro_PM_GERAL_KVARH",
        kvarh_data
    )

    # CCM01 meter
    write_to_influxdb(
        client,
        "tag_eletrocentro_pm_ccm01_kwh_6de263",
        "Eletrocentro_PM_CCM01_KWH",
        ccm01_data
    )

    # Utilidades meter
    write_to_influxdb(
        client,
        "tag_utilidades_energia_consumototal_kwh_2d7040",
        "Utilidades_Energia_ConsumoTotal_kWh",
        utilidades_data
    )

    # Close client
    client.close()

    print("\n" + "=" * 60)
    print("DATA GENERATION COMPLETE!")
    print("=" * 60)
    print(f"\nTotal points written: {len(main_kwh_data) * 4}")
    print(f"Time range: {start_time} to {end_time}")
    print("\nYou can now train the ML model using:")
    print("  POST /api/v1/ml-models/train")
    print("\nOr trigger insights refresh:")
    print("  POST /api/v1/ml-insights/insights/refresh")


if __name__ == "__main__":
    main()
