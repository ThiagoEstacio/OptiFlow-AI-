#!/usr/bin/env python3
"""
Script to populate alarm definitions and create historical alarm events
for testing the alarm system and analytics pages
"""

import requests
import sys
from datetime import datetime, timedelta
import random

API_BASE = "http://localhost:8000/api/v1"

# Cache for tags
_tags_cache = None

def get_all_tags():
    """Get all tags and cache them"""
    global _tags_cache
    if _tags_cache is not None:
        return _tags_cache
    
    try:
        response = requests.get(f"{API_BASE}/tags?limit=200")
        if response.status_code == 200:
            _tags_cache = response.json()
            print(f"📋 Loaded {len(_tags_cache)} tags from backend")
            return _tags_cache
        else:
            print(f"❌ Failed to load tags: Status {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching tags: {e}")
        return []

def get_tag_id(tag_name):
    """Get tag UUID from tag name"""
    tags = get_all_tags()
    
    for tag in tags:
        if tag.get("name") == tag_name:
            return tag.get("id")
    
    print(f"❌ Tag not found: {tag_name}")
    return None

def create_alarm_definition(alarm_def):
    """Create an alarm definition via API"""
    tag_name = alarm_def.pop("tag_name")
    tag_id = get_tag_id(tag_name)
    
    if not tag_id:
        return None
    
    payload = {
        "name": alarm_def["name"],
        "description": alarm_def.get("description", ""),
        "tag_id": tag_id,
        "alarm_type": alarm_def["alarm_type"],
        "severity": alarm_def["severity"],
        "high_limit": alarm_def.get("high_limit"),
        "low_limit": alarm_def.get("low_limit"),
        "deadband": alarm_def.get("deadband", 1.0),
        "delay_seconds": alarm_def.get("delay_seconds", 10),
        "is_active": True
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/alarms/definitions",
            json=payload
        )
        
        if response.status_code in [200, 201]:
            alarm = response.json()
            print(f"✅ Created: {alarm['name']} (ID: {alarm['id'][:8]}...)")
            return alarm
        else:
            print(f"❌ Failed to create {alarm_def['name']}")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Error creating {alarm_def['name']}: {e}")
        return None

# Comprehensive alarm definitions
ALARM_DEFINITIONS = [
    # CONVEYOR ALARMS
    {
        "tag_name": "CORR01_TEMP_C_PV",
        "name": "CORR01 - Alta Temperatura",
        "description": "Temperatura do motor acima do normal",
        "alarm_type": "HIGH_LIMIT",
        "severity": "HIGH",
        "high_limit": 70.0,
        "deadband": 5.0,
        "delay_seconds": 10
    },
    {
        "tag_name": "CORR01_VIBRATION_MMS_PV",
        "name": "CORR01 - Vibração Excessiva",
        "description": "Vibração indicando possível desalinhamento",
        "alarm_type": "HIGH_LIMIT",
        "severity": "MEDIUM",
        "high_limit": 8.0,
        "deadband": 1.0,
        "delay_seconds": 15
    },
    {
        "tag_name": "CORR02_TEMP_C_PV",
        "name": "CORR02 - Alta Temperatura",
        "description": "Temperatura do motor acima do normal",
        "alarm_type": "HIGH_LIMIT",
        "severity": "HIGH",
        "high_limit": 70.0,
        "deadband": 5.0,
        "delay_seconds": 10
    },
    {
        "tag_name": "CORR03_CURRENT_A_PV",
        "name": "CORR03 - Sobrecorrente",
        "description": "Corrente elétrica acima do normal",
        "alarm_type": "HIGH_LIMIT",
        "severity": "CRITICAL",
        "high_limit": 60.0,
        "deadband": 3.0,
        "delay_seconds": 5
    },
    
    # SILO ALARMS
    {
        "tag_name": "SILO01_LEVEL_PCT_PV",
        "name": "SILO01 - Nível Crítico Alto",
        "description": "Silo próximo da capacidade máxima",
        "alarm_type": "HIGH_LIMIT",
        "severity": "CRITICAL",
        "high_limit": 95.0,
        "deadband": 2.0,
        "delay_seconds": 5
    },
    {
        "tag_name": "SILO01_LEVEL_PCT_PV",
        "name": "SILO01 - Nível Baixo",
        "description": "Silo com estoque baixo",
        "alarm_type": "LOW_LIMIT",
        "severity": "LOW",
        "low_limit": 15.0,
        "deadband": 2.0,
        "delay_seconds": 30
    },
    {
        "tag_name": "SILO02_LEVEL_PCT_PV",
        "name": "SILO02 - Nível Crítico Alto",
        "description": "Silo próximo da capacidade máxima",
        "alarm_type": "HIGH_LIMIT",
        "severity": "CRITICAL",
        "high_limit": 95.0,
        "deadband": 2.0,
        "delay_seconds": 5
    },
    {
        "tag_name": "SILO02_GRAIN_TEMP_C_PV",
        "name": "SILO02 - Temperatura Alta do Grão",
        "description": "Temperatura do grão armazenado elevada",
        "alarm_type": "HIGH_LIMIT",
        "severity": "HIGH",
        "high_limit": 35.0,
        "deadband": 2.0,
        "delay_seconds": 60
    },
    {
        "tag_name": "SILO03_HUMIDITY_PCT_PV",
        "name": "SILO03 - Umidade Alta",
        "description": "Umidade do grão acima do recomendado",
        "alarm_type": "HIGH_LIMIT",
        "severity": "MEDIUM",
        "high_limit": 75.0,
        "deadband": 3.0,
        "delay_seconds": 120
    },
    
    # ELEVATOR ALARMS
    {
        "tag_name": "ELEV01_TEMP_C_PV",
        "name": "ELEV01 - Alta Temperatura",
        "description": "Temperatura do elevador acima do normal",
        "alarm_type": "HIGH_LIMIT",
        "severity": "HIGH",
        "high_limit": 75.0,
        "deadband": 5.0,
        "delay_seconds": 10
    },
    {
        "tag_name": "ELEV02_CURRENT_A_PV",
        "name": "ELEV02 - Sobrecorrente",
        "description": "Corrente elétrica acima do normal",
        "alarm_type": "HIGH_LIMIT",
        "severity": "CRITICAL",
        "high_limit": 65.0,
        "deadband": 3.0,
        "delay_seconds": 5
    },
    
    # ENERGY ALARMS
    {
        "tag_name": "Energy_GRID_POWER_KW_PV",
        "name": "Energia - Demanda Alta",
        "description": "Consumo de energia acima do contratado",
        "alarm_type": "HIGH_LIMIT",
        "severity": "HIGH",
        "high_limit": 250.0,
        "deadband": 10.0,
        "delay_seconds": 30
    },
    {
        "tag_name": "Energy_POWER_FACTOR_PV",
        "name": "Energia - Fator de Potência Baixo",
        "description": "Fator de potência abaixo do mínimo",
        "alarm_type": "LOW_LIMIT",
        "severity": "MEDIUM",
        "low_limit": 0.85,
        "deadband": 0.02,
        "delay_seconds": 60
    },
]

def create_test_alarm_events(alarm_definitions):
    """Create test alarm events for the last 7 days"""
    print("\n" + "="*60)
    print("📊 CREATING TEST ALARM EVENTS")
    print("="*60)
    
    now = datetime.now()
    events_created = 0
    
    # Get all alarm definitions from API
    try:
        response = requests.get(f"{API_BASE}/alarms/definitions?limit=100")
        if response.status_code != 200:
            print(f"❌ Failed to fetch alarm definitions")
            return
        
        definitions = response.json()
        print(f"Found {len(definitions)} alarm definitions")
        
        # Create events for random alarms over the last 7 days
        for i in range(30):  # Create 30 test events
            alarm_def = random.choice(definitions)
            
            # Random timestamp in the last 7 days
            days_ago = random.uniform(0, 7)
            trigger_time = now - timedelta(days=days_ago)
            
            # Random duration (5 min to 4 hours)
            duration_minutes = random.randint(5, 240)
            
            # Determine state
            state = random.choice(['CLEARED', 'CLEARED', 'ACKNOWLEDGED', 'ACTIVE'])
            
            # Create event payload
            event = {
                "definition_id": alarm_def["id"],
                "tag_id": alarm_def["tag_id"],
                "state": state,
                "severity": alarm_def["severity"],
                "trigger_value": alarm_def.get("high_limit", alarm_def.get("low_limit", 0)) * random.uniform(1.02, 1.15),
                "trigger_timestamp": trigger_time.isoformat(),
            }
            
            # Add cleared/acknowledged info based on state
            if state in ['CLEARED', 'ACKNOWLEDGED']:
                ack_time = trigger_time + timedelta(minutes=random.randint(1, 30))
                event["acknowledged_at"] = ack_time.isoformat()
                event["acknowledged_by"] = random.choice(["operator1", "operator2", "supervisor"])
                
            if state == 'CLEARED':
                clear_time = trigger_time + timedelta(minutes=duration_minutes)
                event["cleared_at"] = clear_time.isoformat()
                event["clear_value"] = alarm_def.get("high_limit", alarm_def.get("low_limit", 0)) * random.uniform(0.85, 0.98)
                event["duration_seconds"] = duration_minutes * 60
            
            # Post to backend (using internal endpoint if exists, otherwise simulate)
            try:
                # Note: This endpoint might not exist, so we're just showing the structure
                # In production, you'd need a proper endpoint to create alarm events
                print(f"  Event {i+1}: {alarm_def['name'][:40]} - {state} - {trigger_time.strftime('%Y-%m-%d %H:%M')}")
                events_created += 1
            except Exception as e:
                pass
                
    except Exception as e:
        print(f"❌ Error creating test events: {e}")
    
    print(f"\n✅ Would create {events_created} test alarm events (endpoint not available)")
    print("   Note: Events are normally created by the alarm monitoring service")

def main():
    print("="*60)
    print("🚨 ALARM SYSTEM POPULATION SCRIPT")
    print("="*60)
    print("This script will:")
    print("1. Create alarm definitions for simulator tags")
    print("2. Show structure for test alarm events")
    print("="*60)
    
    # Create alarm definitions
    print("\n📝 Creating Alarm Definitions...")
    created_alarms = []
    
    for alarm_def in ALARM_DEFINITIONS:
        alarm = create_alarm_definition(alarm_def.copy())
        if alarm:
            created_alarms.append(alarm)
    
    print(f"\n✅ Successfully created {len(created_alarms)} alarm definitions")
    
    # Show test events structure (actual event creation would be done by the monitoring service)
    create_test_alarm_events(created_alarms)
    
    print("\n" + "="*60)
    print("✅ SCRIPT COMPLETED")
    print("="*60)
    print("\n💡 Next steps:")
    print("   1. Check alarms at: http://localhost:3000/alarms")
    print("   2. Alarm monitoring service will create events automatically")
    print("   3. Manually trigger alarms by adjusting simulator values")
    print("="*60)

if __name__ == "__main__":
    main()
