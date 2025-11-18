#!/usr/bin/env python3
"""
Script to create alarm definitions for OPC UA simulator tags
Creates realistic alarm thresholds for:
- Conveyor temperature, vibration, current
- Silo levels, temperature
- Elevator temperature, current
- Grid power
"""

import requests
import sys

API_BASE = "http://localhost:8000/api/v1"

# Alarm definitions for simulator tags
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
        "tag_name": "CORR01_CURRENT_A_PV",
        "name": "CORR01 - Sobrecorrente",
        "description": "Corrente elétrica acima do normal",
        "alarm_type": "HIGH_LIMIT",
        "severity": "CRITICAL",
        "high_limit": 60.0,
        "deadband": 3.0,
        "delay_seconds": 5
    },
    
    # Repeat for CORR02 and CORR03
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
        "tag_name": "CORR02_VIBRATION_MMS_PV",
        "name": "CORR02 - Vibração Excessiva",
        "description": "Vibração indicando possível desalinhamento",
        "alarm_type": "HIGH_LIMIT",
        "severity": "MEDIUM",
        "high_limit": 8.0,
        "deadband": 1.0,
        "delay_seconds": 15
    },
    {
        "tag_name": "CORR03_TEMP_C_PV",
        "name": "CORR03 - Alta Temperatura",
        "description": "Temperatura do motor acima do normal",
        "alarm_type": "HIGH_LIMIT",
        "severity": "HIGH",
        "high_limit": 70.0,
        "deadband": 5.0,
        "delay_seconds": 10
    },
    
    # SILO ALARMS
    {
        "tag_name": "SILO01_LEVEL_PCT_PV",
        "name": "SILO01 - Nível Crítico Alto",
        "description": "Silo próximo da capacidade máxima",
        "alarm_type": "HIGH_LIMIT",
        "severity": "CRITICAL",
        "high_limit": 95.0,
        "deadband": 3.0,
        "delay_seconds": 30
    },
    {
        "tag_name": "SILO01_LEVEL_PCT_PV",
        "name": "SILO01 - Nível Baixo",
        "description": "Silo com estoque baixo",
        "alarm_type": "LOW_LIMIT",
        "severity": "LOW",
        "low_limit": 15.0,
        "deadband": 3.0,
        "delay_seconds": 60
    },
    {
        "tag_name": "SILO01_TEMP_GRAIN_C_PV",
        "name": "SILO01 - Temperatura do Grão Alta",
        "description": "Risco de deterioração do grão",
        "alarm_type": "HIGH_LIMIT",
        "severity": "HIGH",
        "high_limit": 35.0,
        "deadband": 2.0,
        "delay_seconds": 300
    },
    {
        "tag_name": "SILO01_HUMIDITY_PCT_PV",
        "name": "SILO01 - Umidade Alta",
        "description": "Umidade acima do recomendado",
        "alarm_type": "HIGH_LIMIT",
        "severity": "MEDIUM",
        "high_limit": 75.0,
        "deadband": 5.0,
        "delay_seconds": 180
    },
    
    # SILO02 and SILO03
    {
        "tag_name": "SILO02_LEVEL_PCT_PV",
        "name": "SILO02 - Nível Crítico Alto",
        "description": "Silo próximo da capacidade máxima",
        "alarm_type": "HIGH_LIMIT",
        "severity": "CRITICAL",
        "high_limit": 95.0,
        "deadband": 3.0,
        "delay_seconds": 30
    },
    {
        "tag_name": "SILO02_LEVEL_PCT_PV",
        "name": "SILO02 - Nível Baixo",
        "description": "Silo com estoque baixo",
        "alarm_type": "LOW_LIMIT",
        "severity": "LOW",
        "low_limit": 15.0,
        "deadband": 3.0,
        "delay_seconds": 60
    },
    {
        "tag_name": "SILO03_LEVEL_PCT_PV",
        "name": "SILO03 - Nível Crítico Alto",
        "description": "Silo próximo da capacidade máxima",
        "alarm_type": "HIGH_LIMIT",
        "severity": "CRITICAL",
        "high_limit": 95.0,
        "deadband": 3.0,
        "delay_seconds": 30
    },
    
    # ELEVATOR ALARMS
    {
        "tag_name": "ELEV01_TEMP_C_PV",
        "name": "ELEV01 - Alta Temperatura",
        "description": "Temperatura do motor elevador alta",
        "alarm_type": "HIGH_LIMIT",
        "severity": "HIGH",
        "high_limit": 75.0,
        "deadband": 5.0,
        "delay_seconds": 10
    },
    {
        "tag_name": "ELEV01_CURRENT_A_PV",
        "name": "ELEV01 - Sobrecorrente",
        "description": "Corrente elétrica acima do normal",
        "alarm_type": "HIGH_LIMIT",
        "severity": "CRITICAL",
        "high_limit": 65.0,
        "deadband": 3.0,
        "delay_seconds": 5
    },
    {
        "tag_name": "ELEV02_TEMP_C_PV",
        "name": "ELEV02 - Alta Temperatura",
        "description": "Temperatura do motor elevador alta",
        "alarm_type": "HIGH_LIMIT",
        "severity": "HIGH",
        "high_limit": 75.0,
        "deadband": 5.0,
        "delay_seconds": 10
    },
    
    # ENERGY ALARMS
    {
        "tag_name": "Energy_GRID_POWER_KW_PV",
        "name": "Energia - Demanda Excessiva",
        "description": "Consumo de energia acima do contratado",
        "alarm_type": "HIGH_LIMIT",
        "severity": "HIGH",
        "high_limit": 250.0,
        "deadband": 10.0,
        "delay_seconds": 60
    },
    {
        "tag_name": "Energy_POWER_FACTOR_PV",
        "name": "Energia - Fator de Potência Baixo",
        "description": "Fator de potência abaixo do mínimo",
        "alarm_type": "LOW_LIMIT",
        "severity": "MEDIUM",
        "low_limit": 0.85,
        "deadband": 0.03,
        "delay_seconds": 120
    },
]


def get_tag_id(tag_name):
    """Get tag UUID by name"""
    try:
        response = requests.get(f"{API_BASE}/tags/")
        response.raise_for_status()
        tags = response.json()
        
        for tag in tags:
            if tag["name"] == tag_name:
                return tag["id"]
        
        print(f"❌ Tag not found: {tag_name}")
        return None
    except Exception as e:
        print(f"❌ Error fetching tags: {e}")
        return None


def create_alarm_definition(alarm_def):
    """Create alarm definition via API"""
    tag_id = get_tag_id(alarm_def["tag_name"])
    if not tag_id:
        return False
    
    # Prepare payload
    payload = {
        "tag_id": tag_id,
        "name": alarm_def["name"],
        "description": alarm_def["description"],
        "alarm_type": alarm_def["alarm_type"],
        "severity": alarm_def["severity"],
        "enabled": True,
        "delay_seconds": alarm_def["delay_seconds"],
        "deadband": alarm_def["deadband"]
    }
    
    # Add limits based on alarm type
    if "high_limit" in alarm_def:
        payload["high_limit"] = alarm_def["high_limit"]
    if "low_limit" in alarm_def:
        payload["low_limit"] = alarm_def["low_limit"]
    
    try:
        response = requests.post(
            f"{API_BASE}/alarms/definitions",
            json=payload
        )
        response.raise_for_status()
        print(f"✅ Created: {alarm_def['name']}")
        return True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 422:
            print(f"⚠️  Already exists or validation error: {alarm_def['name']}")
        else:
            print(f"❌ Error creating {alarm_def['name']}: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Error creating {alarm_def['name']}: {e}")
        return False


def main():
    print("🚨 Creating Alarm Definitions for OPC UA Simulator Tags")
    print("=" * 60)
    
    created = 0
    failed = 0
    
    for alarm_def in ALARM_DEFINITIONS:
        if create_alarm_definition(alarm_def):
            created += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Successfully created: {created}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {len(ALARM_DEFINITIONS)}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
