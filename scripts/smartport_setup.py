#!/usr/bin/env python3
"""
Script de Setup Inicial do SmartPort
Cria estrutura básica: usuário admin, organização, site, dispositivo e tags
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"

class SmartPortSetup:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.created_resources: Dict[str, Any] = {}

    def print_step(self, step: str, message: str):
        """Imprime passo do setup"""
        print(f"\n{'='*60}")
        print(f"PASSO {step}: {message}")
        print('='*60)

    def print_success(self, message: str):
        """Imprime mensagem de sucesso"""
        print(f"✓ {message}")

    def print_error(self, message: str):
        """Imprime mensagem de erro"""
        print(f"✗ ERRO: {message}", file=sys.stderr)

    def check_health(self) -> bool:
        """Verifica se o backend está online"""
        self.print_step("1", "Verificando disponibilidade do backend")
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                self.print_success("Backend está online e respondendo")
                return True
            else:
                self.print_error(f"Backend retornou status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_error(f"Não foi possível conectar ao backend: {e}")
            return False

    def create_admin_user(self) -> bool:
        """Cria usuário administrador"""
        self.print_step("2", "Criando usuário administrador")

        user_data = {
            "email": "admin@smartport.com",
            "password": "Admin@123456",
            "full_name": "SmartPort Administrator",
            "is_superuser": True
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/register",
                json=user_data,
                timeout=10
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.print_success("Usuário admin criado com sucesso")
                print(f"  Email: {user_data['email']}")
                print(f"  Senha: {user_data['password']}")
                self.created_resources['user'] = data
                return True
            elif response.status_code == 400 and "already exists" in response.text.lower():
                self.print_success("Usuário admin já existe")
                return True
            else:
                self.print_error(f"Falha ao criar usuário: {response.status_code}")
                print(f"  Resposta: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_error(f"Erro na requisição: {e}")
            return False

    def login(self) -> bool:
        """Faz login e obtém token JWT"""
        self.print_step("3", "Autenticando usuário")

        login_data = {
            "username": "admin@smartport.com",
            "password": "Admin@123456"
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                data=login_data,  # Form data, não JSON
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.print_success("Login realizado com sucesso")
                print(f"  Token obtido: {self.token[:50]}...")
                return True
            else:
                self.print_error(f"Falha no login: {response.status_code}")
                print(f"  Resposta: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_error(f"Erro na requisição: {e}")
            return False

    def get_headers(self) -> Dict[str, str]:
        """Retorna headers com autenticação"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def create_organization(self) -> bool:
        """Cria organização"""
        self.print_step("4", "Criando organização")

        org_data = {
            "name": "Porto de Santos",
            "description": "Terminal de containers - Santos/SP",
            "settings": {
                "timezone": "America/Sao_Paulo",
                "language": "pt-BR",
                "currency": "BRL"
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/organizations/",
                json=org_data,
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.created_resources['organization'] = data
                self.print_success("Organização criada com sucesso")
                print(f"  ID: {data.get('id')}")
                print(f"  Nome: {data.get('name')}")
                return True
            else:
                self.print_error(f"Falha ao criar organização: {response.status_code}")
                print(f"  Resposta: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_error(f"Erro na requisição: {e}")
            return False

    def create_smartport_site(self) -> bool:
        """Cria site SmartPort"""
        self.print_step("5", "Criando site SmartPort")

        site_data = {
            "name": "Terminal T1 - Santos",
            "site_type": "smartport",
            "organization_id": self.created_resources['organization']['id'],
            "description": "Terminal de containers automatizado",
            "address": "Av. Portuária, 1000",
            "city": "Santos",
            "state": "SP",
            "country": "Brasil",
            "postal_code": "11013-000",
            "latitude": -23.9618,
            "longitude": -46.3322,
            "timezone": "America/Sao_Paulo",
            "settings": {
                "operational_hours": "24/7",
                "max_capacity_teu": 10000,
                "berths": 4,
                "cranes": 8
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/sites/",
                json=site_data,
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.created_resources['site'] = data
                self.print_success("Site SmartPort criado com sucesso")
                print(f"  ID: {data.get('id')}")
                print(f"  Nome: {data.get('name')}")
                print(f"  Tipo: {data.get('site_type')}")
                return True
            else:
                self.print_error(f"Falha ao criar site: {response.status_code}")
                print(f"  Resposta: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_error(f"Erro na requisição: {e}")
            return False

    def create_device(self) -> bool:
        """Cria dispositivo PLC"""
        self.print_step("6", "Criando dispositivo (PLC Portainer)")

        device_data = {
            "name": "PLC Portainer 01",
            "site_id": self.created_resources['site']['id'],
            "device_type": "PLC",
            "protocol": "opc_ua",
            "description": "Controlador do Portainer de Containers 01",
            "ip_address": "192.168.100.50",
            "port": 4840,
            "connection_config": {
                "endpoint": "opc.tcp://192.168.100.50:4840",
                "security_mode": "None",
                "security_policy": "None",
                "username": "",
                "password": ""
            },
            "scan_rate": 1000,
            "enabled": True,
            "settings": {
                "crane_id": "PC-01",
                "max_load_kg": 65000,
                "max_height_m": 40,
                "max_reach_m": 50
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/devices/",
                json=device_data,
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.created_resources['device'] = data
                self.print_success("Dispositivo criado com sucesso")
                print(f"  ID: {data.get('id')}")
                print(f"  Nome: {data.get('name')}")
                print(f"  Protocolo: {data.get('protocol')}")
                return True
            else:
                self.print_error(f"Falha ao criar dispositivo: {response.status_code}")
                print(f"  Resposta: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_error(f"Erro na requisição: {e}")
            return False

    def create_tags(self) -> bool:
        """Cria tags de processo"""
        self.print_step("7", "Criando tags de processo")

        tags_data = [
            {
                "name": "PC01_Motor_Temperature",
                "description": "Temperatura do motor principal",
                "address": "ns=2;s=Crane.Motor.Temperature",
                "data_type": "float",
                "unit": "°C",
                "category": "maintenance",
                "scan_rate": 5000,
                "deadband": 0.5,
                "min_value": 0.0,
                "max_value": 150.0,
            },
            {
                "name": "PC01_Spreader_Height",
                "description": "Altura atual do spreader",
                "address": "ns=2;s=Crane.Spreader.Height",
                "data_type": "float",
                "unit": "m",
                "category": "process",
                "scan_rate": 1000,
                "deadband": 0.1,
                "min_value": 0.0,
                "max_value": 40.0,
            },
            {
                "name": "PC01_Spreader_Position_X",
                "description": "Posição X do spreader",
                "address": "ns=2;s=Crane.Spreader.Position.X",
                "data_type": "float",
                "unit": "m",
                "category": "process",
                "scan_rate": 1000,
                "deadband": 0.1,
                "min_value": 0.0,
                "max_value": 50.0,
            },
            {
                "name": "PC01_Load_Weight",
                "description": "Peso da carga atual",
                "address": "ns=2;s=Crane.Load.Weight",
                "data_type": "float",
                "unit": "kg",
                "category": "process",
                "scan_rate": 2000,
                "min_value": 0.0,
                "max_value": 65000.0,
            },
            {
                "name": "PC01_Operational_Status",
                "description": "Status operacional do portainer",
                "address": "ns=2;s=Crane.Status.Operational",
                "data_type": "integer",
                "category": "status",
                "scan_rate": 2000,
                "settings": {
                    "0": "Stopped",
                    "1": "Running",
                    "2": "Error",
                    "3": "Maintenance"
                }
            },
            {
                "name": "PC01_Energy_Consumption",
                "description": "Consumo de energia instantâneo",
                "address": "ns=2;s=Crane.Energy.Current",
                "data_type": "float",
                "unit": "kW",
                "category": "energy",
                "scan_rate": 5000,
                "min_value": 0.0,
                "max_value": 500.0,
            }
        ]

        self.created_resources['tags'] = []

        for tag_data in tags_data:
            tag_data['device_id'] = self.created_resources['device']['id']
            tag_data['enabled'] = True

            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/tags/",
                    json=tag_data,
                    headers=self.get_headers(),
                    timeout=10
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    self.created_resources['tags'].append(data)
                    self.print_success(f"Tag criada: {tag_data['name']}")
                else:
                    self.print_error(f"Falha ao criar tag {tag_data['name']}: {response.status_code}")
                    print(f"  Resposta: {response.text}")
            except requests.exceptions.RequestException as e:
                self.print_error(f"Erro ao criar tag {tag_data['name']}: {e}")

        return len(self.created_resources['tags']) > 0

    def create_alarm(self) -> bool:
        """Cria definição de alarme"""
        self.print_step("8", "Criando alarme de temperatura")

        # Encontrar tag de temperatura
        temp_tag = None
        for tag in self.created_resources['tags']:
            if 'Temperature' in tag['name']:
                temp_tag = tag
                break

        if not temp_tag:
            self.print_error("Tag de temperatura não encontrada")
            return False

        alarm_data = {
            "name": "Temperatura Motor Alta",
            "tag_id": temp_tag['id'],
            "alarm_type": "high_limit",
            "severity": "high",
            "description": "Alarme quando temperatura do motor excede 85°C",
            "setpoint": 85.0,
            "deadband": 5.0,
            "delay": 10,
            "enabled": True,
            "notification_enabled": True,
            "notification_emails": ["operacao@smartport.com"],
            "message_template": "ATENÇÃO: Temperatura do motor PC-01 atingiu {value}°C (limite: {setpoint}°C)"
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/alarms/definitions/",
                json=alarm_data,
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.created_resources['alarm'] = data
                self.print_success("Alarme criado com sucesso")
                print(f"  ID: {data.get('id')}")
                print(f"  Nome: {data.get('name')}")
                print(f"  Setpoint: {data.get('setpoint')}°C")
                return True
            else:
                self.print_error(f"Falha ao criar alarme: {response.status_code}")
                print(f"  Resposta: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_error(f"Erro na requisição: {e}")
            return False

    def save_configuration(self):
        """Salva configuração em arquivo JSON"""
        self.print_step("9", "Salvando configuração")

        config = {
            "base_url": self.base_url,
            "token": self.token,
            "resources": self.created_resources
        }

        try:
            with open('smartport_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self.print_success("Configuração salva em smartport_config.json")
            print(f"  Token: {self.token}")
            print(f"  Organization ID: {self.created_resources['organization']['id']}")
            print(f"  Site ID: {self.created_resources['site']['id']}")
            print(f"  Device ID: {self.created_resources['device']['id']}")
            print(f"  Tags: {len(self.created_resources['tags'])} criadas")
        except Exception as e:
            self.print_error(f"Erro ao salvar configuração: {e}")

    def run(self):
        """Executa setup completo"""
        print("\n" + "="*60)
        print("🚀 SMARTPORT - SETUP INICIAL")
        print("="*60)

        steps = [
            ("Verificar backend", self.check_health),
            ("Criar usuário admin", self.create_admin_user),
            ("Fazer login", self.login),
            ("Criar organização", self.create_organization),
            ("Criar site SmartPort", self.create_smartport_site),
            ("Criar dispositivo", self.create_device),
            ("Criar tags", self.create_tags),
            ("Criar alarme", self.create_alarm),
        ]

        for step_name, step_func in steps:
            if not step_func():
                print("\n" + "="*60)
                print(f"❌ SETUP FALHOU NA ETAPA: {step_name}")
                print("="*60)
                sys.exit(1)

        self.save_configuration()

        print("\n" + "="*60)
        print("✅ SETUP CONCLUÍDO COM SUCESSO!")
        print("="*60)
        print("\nRecursos criados:")
        print(f"  • 1 Usuário (admin@smartport.com)")
        print(f"  • 1 Organização (Porto de Santos)")
        print(f"  • 1 Site SmartPort (Terminal T1)")
        print(f"  • 1 Dispositivo PLC (Portainer 01)")
        print(f"  • {len(self.created_resources['tags'])} Tags de processo")
        print(f"  • 1 Alarme (Temperatura Motor)")
        print("\nPróximos passos:")
        print("  1. Execute: python scripts/smartport_simulate.py")
        print("  2. Acesse: http://localhost:8000/docs")
        print("  3. Acesse: http://localhost:5173")
        print("\n")

if __name__ == "__main__":
    setup = SmartPortSetup()
    setup.run()
