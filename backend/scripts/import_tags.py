#!/usr/bin/env python3
"""
Import OPC UA tags into OptiFlow database
"""
import requests
import json

API_URL = "http://localhost:8000/api/v1/tags/"
DEVICE_ID = "9bf20d02-35c0-4dc2-9e65-64ffd36a2e12"

# Tags baseadas no servidor OPC UA Terminal
TAGS = [
    # Gates (Portões)
    {"name": "GATE01_POSITION", "address": "ns=2;s=TEAG.ARZ.GATES.GATE01.POSICAO.PV", "unit": "%", "description": "Gate 1 Position"},
    {"name": "GATE02_POSITION", "address": "ns=2;s=TEAG.ARZ.GATES.GATE02.POSICAO.PV", "unit": "%", "description": "Gate 2 Position"},
    {"name": "GATE03_POSITION", "address": "ns=2;s=TEAG.ARZ.GATES.GATE03.POSICAO.PV", "unit": "%", "description": "Gate 3 Position"},
    {"name": "GATE04_POSITION", "address": "ns=2;s=TEAG.ARZ.GATES.GATE04.POSICAO.PV", "unit": "%", "description": "Gate 4 Position"},
    {"name": "GATE05_POSITION", "address": "ns=2;s=TEAG.ARZ.GATES.GATE05.POSICAO.PV", "unit": "%", "description": "Gate 5 Position"},
    
    # Conveyors (Correias)
    {"name": "CONVEYOR01_FLOW", "address": "ns=2;s=TEAG.ARZ.CORR01.VAZAO.PV", "unit": "t/h", "description": "Conveyor 1 Flow Rate"},
    {"name": "CONVEYOR02_FLOW", "address": "ns=2;s=TEAG.ARZ.CORR02.VAZAO.PV", "unit": "t/h", "description": "Conveyor 2 Flow Rate"},
    {"name": "CONVEYOR03_FLOW", "address": "ns=2;s=TEAG.ARZ.CORR03.VAZAO.PV", "unit": "t/h", "description": "Conveyor 3 Flow Rate"},
    
    # Elevator (Elevador)
    {"name": "ELEVATOR01_MOTOR_TEMP", "address": "ns=2;s=TEAG.ELV.ELV01.TEMP_MOTOR.PV", "unit": "°C", "description": "Elevator 1 Motor Temperature"},
    
    # Scale (Balança)
    {"name": "SCALE01_WEIGHT", "address": "ns=2;s=TEAG.BAL.BAL01.PESO.PV", "unit": "kg", "description": "Scale 1 Weight"},
    
    # Shiploader (Carregador de Navios)
    {"name": "SHIPLOADER01_FLOW", "address": "ns=2;s=TEAG.SLD.SLD01.VAZAO.PV", "unit": "t/h", "description": "Shiploader 1 Flow Rate"},
    {"name": "SHIPLOADER01_FLOW_SP", "address": "ns=2;s=TEAG.SLD.SLD01.VAZAO.SP", "unit": "t/h", "description": "Shiploader 1 Flow Rate Setpoint"},
    
    # KPIs
    {"name": "TOTAL_ENERGY", "address": "ns=2;s=TEAG.KPIs.ENERGIA_TOTAL.TOT", "unit": "kWh", "description": "Total Energy Consumption"},
    {"name": "TOTAL_MASS", "address": "ns=2;s=TEAG.KPIs.MASSA_TOTAL.TOT", "unit": "t", "description": "Total Mass Processed"},
    {"name": "TOTAL_COST", "address": "ns=2;s=TEAG.KPIs.CUSTO_TOTAL.TOT", "unit": "R$", "description": "Total Operating Cost"},
]

def create_tag(tag_data):
    """Create a single tag via API"""
    payload = {
        "name": tag_data["name"],
        "address": tag_data["address"],
        "device_id": DEVICE_ID,
        "data_type": "FLOAT",
        "unit": tag_data["unit"],
        "description": tag_data["description"],
        "enabled": True
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=5)
        response.raise_for_status()
        print(f"✅ {tag_data['name']}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ {tag_data['name']}: {str(e)}")
        return False

def main():
    print(f"\n🚀 Importing {len(TAGS)} tags into OptiFlow...")
    print(f"   Device ID: {DEVICE_ID}\n")
    
    success_count = 0
    for tag in TAGS:
        if create_tag(tag):
            success_count += 1
    
    print(f"\n✅ Done! {success_count}/{len(TAGS)} tags imported successfully\n")
    
    # Verify
    try:
        response = requests.get(API_URL, timeout=5)
        total = len(response.json())
        print(f"📊 Total tags in database: {total}\n")
    except:
        pass

if __name__ == "__main__":
    main()
