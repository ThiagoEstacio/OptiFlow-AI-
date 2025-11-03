#!/usr/bin/env python3
"""
Script de Simulação de Dados do SmartPort
Simula dados de um portainer em operação
"""

import requests
import json
import time
import random
import math
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class SmartPortSimulator:
    def __init__(self, config_file: str = 'smartport_config.json'):
        self.config = self.load_config(config_file)
        self.base_url = self.config['base_url']
        self.token = self.config['token']
        self.tags = {tag['name']: tag for tag in self.config['resources']['tags']}

        # Estado do portainer
        self.crane_state = {
            'height': 0.0,  # m
            'position_x': 0.0,  # m
            'load_weight': 0.0,  # kg
            'motor_temp': 45.0,  # °C
            'status': 1,  # 1=Running
            'energy': 0.0,  # kW
            'cycle_count': 0,
            'operation': 'idle'  # idle, loading, moving, unloading
        }

    def load_config(self, config_file: str) -> Dict:
        """Carrega configuração do arquivo"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Arquivo de configuração não encontrado: {config_file}")
            print("   Execute primeiro: python scripts/smartport_setup.py")
            sys.exit(1)

    def get_headers(self) -> Dict[str, str]:
        """Retorna headers com autenticação"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def write_data_point(self, tag_name: str, value: float):
        """Escreve um ponto de dado no InfluxDB"""
        if tag_name not in self.tags:
            return

        tag_id = self.tags[tag_name]['id']
        timestamp = datetime.utcnow().isoformat() + "Z"

        data = {
            "tag_id": tag_id,
            "value": round(value, 2),
            "timestamp": timestamp
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/timeseries/write",
                json=data,
                headers=self.get_headers(),
                timeout=5
            )

            if response.status_code not in [200, 201]:
                print(f"⚠️  Erro ao escrever {tag_name}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Erro de conexão ao escrever {tag_name}: {e}")

    def simulate_crane_cycle(self):
        """Simula um ciclo completo de operação do portainer"""

        # Fase 1: Carregar container (0-30s)
        print("  📦 Carregando container...")
        for i in range(30):
            self.crane_state['operation'] = 'loading'
            self.crane_state['load_weight'] = min(i * 1000, 25000)  # Carregar até 25 toneladas
            self.crane_state['motor_temp'] += 0.1  # Temperatura sobe levemente
            self.crane_state['energy'] = 150 + random.uniform(-10, 10)
            self.crane_state['height'] = 2.0  # Baixo
            self.update_all_tags()
            time.sleep(1)

        # Fase 2: Levantar (30-60s)
        print("  ⬆️  Levantando carga...")
        for i in range(30):
            self.crane_state['operation'] = 'lifting'
            self.crane_state['height'] = 2.0 + (i / 30) * 38.0  # Subir até 40m
            self.crane_state['motor_temp'] += 0.3  # Temperatura sobe mais
            self.crane_state['energy'] = 350 + random.uniform(-20, 20)
            self.update_all_tags()
            time.sleep(1)

        # Fase 3: Mover horizontalmente (60-120s)
        print("  ➡️  Movendo horizontalmente...")
        for i in range(60):
            self.crane_state['operation'] = 'moving'
            self.crane_state['position_x'] = (i / 60) * 45.0  # Mover até 45m
            self.crane_state['height'] = 40.0 + random.uniform(-0.5, 0.5)
            self.crane_state['motor_temp'] += 0.2
            self.crane_state['energy'] = 250 + random.uniform(-15, 15)
            self.update_all_tags()
            time.sleep(1)

        # Fase 4: Descer (120-150s)
        print("  ⬇️  Descendo carga...")
        for i in range(30):
            self.crane_state['operation'] = 'lowering'
            self.crane_state['height'] = 40.0 - (i / 30) * 38.0  # Descer até 2m
            self.crane_state['motor_temp'] += 0.1
            self.crane_state['energy'] = 100 + random.uniform(-10, 10)
            self.update_all_tags()
            time.sleep(1)

        # Fase 5: Descarregar (150-170s)
        print("  📤 Descarregando container...")
        for i in range(20):
            self.crane_state['operation'] = 'unloading'
            self.crane_state['load_weight'] = 25000 - (i / 20) * 25000
            self.crane_state['motor_temp'] += 0.05
            self.crane_state['energy'] = 80 + random.uniform(-10, 10)
            self.update_all_tags()
            time.sleep(1)

        # Fase 6: Retornar (170-220s)
        print("  ↩️  Retornando à posição inicial...")
        for i in range(50):
            self.crane_state['operation'] = 'returning'
            self.crane_state['position_x'] = 45.0 - (i / 50) * 45.0
            self.crane_state['height'] = 2.0
            self.crane_state['motor_temp'] -= 0.1  # Temperatura começa a cair
            self.crane_state['energy'] = 120 + random.uniform(-10, 10)
            self.update_all_tags()
            time.sleep(1)

        # Fase 7: Idle (220-250s)
        print("  💤 Em espera...")
        for i in range(30):
            self.crane_state['operation'] = 'idle'
            self.crane_state['position_x'] = 0.0
            self.crane_state['height'] = 0.0
            self.crane_state['load_weight'] = 0.0
            self.crane_state['motor_temp'] = max(45.0, self.crane_state['motor_temp'] - 0.3)
            self.crane_state['energy'] = 20 + random.uniform(-5, 5)
            self.update_all_tags()
            time.sleep(1)

        self.crane_state['cycle_count'] += 1

    def update_all_tags(self):
        """Atualiza todas as tags com valores simulados"""
        # Adicionar ruído e variação realista
        noise = lambda val, pct=2: val + random.uniform(-val*pct/100, val*pct/100)

        # Temperatura do motor
        temp = noise(self.crane_state['motor_temp'], 1)
        self.write_data_point('PC01_Motor_Temperature', temp)

        # Altura do spreader
        height = noise(self.crane_state['height'], 0.5)
        self.write_data_point('PC01_Spreader_Height', max(0, height))

        # Posição X
        pos_x = noise(self.crane_state['position_x'], 0.5)
        self.write_data_point('PC01_Spreader_Position_X', max(0, pos_x))

        # Peso da carga
        weight = noise(self.crane_state['load_weight'], 1)
        self.write_data_point('PC01_Load_Weight', max(0, weight))

        # Status operacional
        self.write_data_point('PC01_Operational_Status', self.crane_state['status'])

        # Consumo de energia
        energy = noise(self.crane_state['energy'], 3)
        self.write_data_point('PC01_Energy_Consumption', max(0, energy))

    def simulate_continuous(self, duration_minutes: int = 60):
        """Simula operação contínua por X minutos"""
        print("\n" + "="*60)
        print("🏗️  SIMULADOR SMARTPORT - PORTAINER 01")
        print("="*60)
        print(f"Duração: {duration_minutes} minutos")
        print(f"Base URL: {self.base_url}")
        print(f"Tags: {len(self.tags)}")
        print("="*60 + "\n")

        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)

        cycle = 1

        try:
            while datetime.now() < end_time:
                print(f"\n🔄 Ciclo {cycle} (Início: {datetime.now().strftime('%H:%M:%S')})")
                print("-" * 60)

                self.simulate_crane_cycle()

                print(f"✓ Ciclo {cycle} concluído")
                print(f"  Temperatura motor: {self.crane_state['motor_temp']:.1f}°C")
                print(f"  Total de ciclos: {self.crane_state['cycle_count']}")

                remaining = (end_time - datetime.now()).total_seconds()
                if remaining > 0:
                    print(f"  Tempo restante: {remaining/60:.1f} minutos")

                cycle += 1

        except KeyboardInterrupt:
            print("\n\n⚠️  Simulação interrompida pelo usuário")

        print("\n" + "="*60)
        print("✅ SIMULAÇÃO FINALIZADA")
        print("="*60)
        print(f"Ciclos completados: {self.crane_state['cycle_count']}")
        print(f"Duração total: {(datetime.now() - start_time).total_seconds()/60:.1f} minutos")
        print("\nPróximos passos:")
        print("  1. Visualize os dados em: http://localhost:8000/docs")
        print("  2. Execute queries de séries temporais")
        print("  3. Configure dashboards no Grafana")
        print("="*60 + "\n")

    def simulate_quick_test(self):
        """Simulação rápida para testes (5 minutos)"""
        print("\n" + "="*60)
        print("🧪 TESTE RÁPIDO - SMARTPORT")
        print("="*60)
        print("Duração: 5 minutos")
        print("="*60 + "\n")

        for cycle in range(1, 3):  # 2 ciclos completos
            print(f"\n🔄 Ciclo {cycle}/2")
            print("-" * 60)
            self.simulate_crane_cycle()
            print(f"✓ Ciclo {cycle} concluído\n")

        print("\n" + "="*60)
        print("✅ TESTE RÁPIDO FINALIZADO")
        print("="*60)
        print(f"Ciclos completados: {self.crane_state['cycle_count']}")
        print("\nVerifique os dados:")
        print(f"  curl -H 'Authorization: Bearer {self.token}' \\")
        print(f"       {self.base_url}/api/v1/timeseries/tags/<tag_id>/latest")
        print("="*60 + "\n")

def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Simulador de dados SmartPort')
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='Duração da simulação em minutos (padrão: 60)'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Executa teste rápido (5 minutos, 2 ciclos)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='smartport_config.json',
        help='Arquivo de configuração (padrão: smartport_config.json)'
    )

    args = parser.parse_args()

    simulator = SmartPortSimulator(config_file=args.config)

    if args.quick:
        simulator.simulate_quick_test()
    else:
        simulator.simulate_continuous(duration_minutes=args.duration)

if __name__ == "__main__":
    main()
