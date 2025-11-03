#!/usr/bin/env python3
"""
Test if the simulator API is updating values in real-time
"""
import requests
import time
import sys

BASE_URL = "http://localhost:8000/api/v1/simulator"

def test_realtime_updates():
    print("=" * 80)
    print("TESTE DE ATUALIZAÇÃO EM TEMPO REAL")
    print("=" * 80)

    # 1. Reset the system
    print("\n1. Resetando sistema...")
    try:
        response = requests.post(f"{BASE_URL}/reset")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ERRO: {e}")
        print(f"   Certifique-se que o backend está rodando: uvicorn app.main:app --reload")
        sys.exit(1)

    # 2. Get initial status
    print("\n2. Status inicial...")
    response = requests.get(f"{BASE_URL}/status")
    initial_status = response.json()
    print(f"   Time: {initial_status['system']['time_s']}s")
    print(f"   Running: {initial_status['system']['running']}")
    print(f"   CORR01 Current: {initial_status['belts']['CORR01']['current_A']:.1f}A")
    print(f"   CORR01 Power: {initial_status['belts']['CORR01']['power_kW']:.1f}kW")
    print(f"   CORR01 Temp: {initial_status['belts']['CORR01']['temp_bearing_C']:.1f}°C")

    # 3. Start the system
    print("\n3. Iniciando sistema...")
    response = requests.post(f"{BASE_URL}/start")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")

    # 4. Wait a moment for loop to start
    print("\n4. Aguardando 2 segundos para loop iniciar...")
    time.sleep(2)

    # 5. Check status after start
    print("\n5. Status após start...")
    response = requests.get(f"{BASE_URL}/status")
    status_after_start = response.json()
    print(f"   Time: {status_after_start['system']['time_s']}s")
    print(f"   Running: {status_after_start['system']['running']}")
    print(f"   CORR01 Current: {status_after_start['belts']['CORR01']['current_A']:.1f}A")
    print(f"   CORR01 Power: {status_after_start['belts']['CORR01']['power_kW']:.1f}kW")
    print(f"   CORR01 Temp: {status_after_start['belts']['CORR01']['temp_bearing_C']:.1f}°C")

    # 6. Monitor for 10 seconds
    print("\n6. Monitorando por 10 segundos...")
    print("   Time | Running | CORR01 Current | CORR01 Power | CORR01 Temp")
    print("   " + "-" * 70)

    samples = []
    for i in range(10):
        time.sleep(1)
        response = requests.get(f"{BASE_URL}/status")
        status = response.json()

        t = status['system']['time_s']
        running = status['system']['running']
        current = status['belts']['CORR01']['current_A']
        power = status['belts']['CORR01']['power_kW']
        temp = status['belts']['CORR01']['temp_bearing_C']

        samples.append({
            'time': t,
            'current': current,
            'power': power,
            'temp': temp
        })

        print(f"   {t:5.1f}s | {running:7} | {current:14.1f}A | {power:12.1f}kW | {temp:11.1f}°C")

    # 7. Analysis
    print("\n7. ANÁLISE:")
    print("   " + "=" * 70)

    # Check if time is advancing
    times = [s['time'] for s in samples]
    time_delta = times[-1] - times[0]
    print(f"   Tempo avançou: {time_delta:.1f}s (esperado: ~9-10s)")

    if time_delta < 1.0:
        print("   ❌ PROBLEMA: Tempo NÃO está avançando! Loop não está rodando.")
        return False
    else:
        print("   ✅ Tempo está avançando corretamente")

    # Check if current changed
    currents = [s['current'] for s in samples]
    current_changed = max(currents) - min(currents) > 1.0
    print(f"   Corrente: min={min(currents):.1f}A, max={max(currents):.1f}A")

    if not current_changed:
        print("   ❌ PROBLEMA: Corrente NÃO está mudando!")
        return False
    else:
        print("   ✅ Corrente está mudando")

    # Check if power changed
    powers = [s['power'] for s in samples]
    power_changed = max(powers) - min(powers) > 1.0
    print(f"   Potência: min={min(powers):.1f}kW, max={max(powers):.1f}kW")

    if not power_changed:
        print("   ❌ PROBLEMA: Potência NÃO está mudando!")
        return False
    else:
        print("   ✅ Potência está mudando")

    # Check if temperature changed
    temps = [s['temp'] for s in samples]
    temp_changed = max(temps) - min(temps) > 0.1
    print(f"   Temperatura: min={min(temps):.1f}°C, max={max(temps):.1f}°C")

    if not temp_changed:
        print("   ⚠️  AVISO: Temperatura pode não estar mudando significativamente")
    else:
        print("   ✅ Temperatura está mudando")

    print("\n" + "=" * 80)
    if time_delta >= 1.0 and current_changed and power_changed:
        print("✅ TESTE PASSOU! Simulador está atualizando valores em tempo real!")
        return True
    else:
        print("❌ TESTE FALHOU! Simulador NÃO está atualizando valores corretamente!")
        return False

if __name__ == "__main__":
    success = test_realtime_updates()
    sys.exit(0 if success else 1)
