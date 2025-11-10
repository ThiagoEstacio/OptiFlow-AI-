#!/usr/bin/env python3
"""
Populate demo tags via API

Creates demo tags using the REST API instead of direct database access.
This avoids SQLAlchemy relationship issues.
"""
import requests
import json
from datetime import datetime, timedelta
import random

BASE_URL = "http://localhost:8000/api/v1"

# Login credentials
USERNAME = "admin@optiflow.com"
PASSWORD = "admin123"

# Demo tags configuration
DEMO_TAGS = [
    {
        'name': 'energy_consumption',
        'tag_address': 'energy_consumption',
        'description': 'Total Energy Consumption',
        'unit': 'kWh',
        'category': 'ENERGY',
        'data_type': 'FLOAT',
        'min_value': 800.0,
        'max_value': 1500.0,
        'is_active': True
    },
    {
        'name': 'production_rate',
        'tag_address': 'production_rate',
        'description': 'Production Rate',
        'unit': 'tons/h',
        'category': 'PROCESS',
        'data_type': 'FLOAT',
        'min_value': 50.0,
        'max_value': 150.0,
        'is_active': True
    },
    {
        'name': 'conveyor_speed',
        'tag_address': 'conveyor_speed',
        'description': 'Conveyor Belt Speed',
        'unit': 'm/s',
        'category': 'PROCESS',
        'data_type': 'FLOAT',
        'min_value': 0.5,
        'max_value': 3.0,
        'is_active': True
    },
    {
        'name': 'motor_temperature',
        'tag_address': 'motor_temperature',
        'description': 'Motor Temperature',
        'unit': '°C',
        'category': 'MAINTENANCE',
        'data_type': 'FLOAT',
        'min_value': 40.0,
        'max_value': 85.0,
        'is_active': True
    },
    {
        'name': 'vibration_level',
        'tag_address': 'vibration_level',
        'description': 'Vibration Level',
        'unit': 'mm/s',
        'category': 'MAINTENANCE',
        'data_type': 'FLOAT',
        'min_value': 0.5,
        'max_value': 5.0,
        'is_active': True
    },
    {
        'name': 'pressure_sensor_1',
        'tag_address': 'pressure_sensor_1',
        'description': 'Pressure Sensor 1',
        'unit': 'bar',
        'category': 'PROCESS',
        'data_type': 'FLOAT',
        'min_value': 1.0,
        'max_value': 8.0,
        'is_active': True
    },
    {
        'name': 'flow_rate_01',
        'tag_address': 'flow_rate_01',
        'description': 'Flow Rate 01',
        'unit': 'm3/h',
        'category': 'PROCESS',
        'data_type': 'FLOAT',
        'min_value': 10.0,
        'max_value': 50.0,
        'is_active': True
    },
    {
        'name': 'quality_index',
        'tag_address': 'quality_index',
        'description': 'Product Quality Index',
        'unit': '%',
        'category': 'QUALITY',
        'data_type': 'FLOAT',
        'min_value': 85.0,
        'max_value': 100.0,
        'is_active': True
    },
    {
        'name': 'ambient_temperature',
        'tag_address': 'ambient_temperature',
        'description': 'Ambient Temperature',
        'unit': '°C',
        'category': 'PROCESS',
        'data_type': 'FLOAT',
        'min_value': 15.0,
        'max_value': 35.0,
        'is_active': True
    },
    {
        'name': 'humidity_level',
        'tag_address': 'humidity_level',
        'description': 'Humidity Level',
        'unit': '%',
        'category': 'PROCESS',
        'data_type': 'FLOAT',
        'min_value': 30.0,
        'max_value': 80.0,
        'is_active': True
    },
]


def login():
    """Login and get access token"""
    print("Logging in...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            'username': USERNAME,
            'password': PASSWORD
        }
    )

    if response.status_code == 200:
        token = response.json()['access_token']
        print(f"✓ Login successful")
        return token
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(response.text)
        return None


def create_tag(token, tag_data):
    """Create a tag via API"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    response = requests.post(
        f"{BASE_URL}/tags/",
        headers=headers,
        json=tag_data
    )

    if response.status_code == 200:
        return response.json()
    else:
        return None


def main():
    """Main function"""
    print("=" * 60)
    print("POPULATING DEMO TAGS VIA API")
    print("=" * 60)

    # Login
    token = login()
    if not token:
        print("ERROR: Could not login")
        return

    print("\nCreating demo tags...")
    created_count = 0
    skipped_count = 0

    for tag_config in DEMO_TAGS:
        # Check if tag already exists
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f"{BASE_URL}/tags/", headers=headers)

        if response.status_code == 200:
            existing_tags = response.json()
            if any(t['name'] == tag_config['name'] for t in existing_tags):
                print(f"  ⚠ Tag '{tag_config['name']}' already exists")
                skipped_count += 1
                continue

        # Create tag
        result = create_tag(token, tag_config)
        if result:
            print(f"  ✓ Created tag '{tag_config['name']}'")
            created_count += 1
        else:
            print(f"  ✗ Failed to create tag '{tag_config['name']}'")

    print("\n" + "=" * 60)
    print(f"✓ DEMO TAGS CREATED!")
    print("=" * 60)
    print(f"  Created: {created_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total: {len(DEMO_TAGS)}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
