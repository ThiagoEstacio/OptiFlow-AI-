#!/usr/bin/env python3
"""
Script de Verificação do SmartPort
Valida que todos os serviços e componentes estão funcionando corretamente
"""

import requests
import json
import sys
import subprocess
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class SmartPortVerifier:
    def __init__(self):
        self.results: List[Tuple[str, bool, str]] = []
        self.base_url = "http://localhost:8000"

    def print_header(self, title: str):
        """Imprime cabeçalho de seção"""
        print(f"\n{'='*70}")
        print(f"  {title}")
        print('='*70)

    def print_test(self, name: str, passed: bool, details: str = ""):
        """Imprime resultado de um teste"""
        status = "✓" if passed else "✗"
        color = "\033[92m" if passed else "\033[91m"  # Verde ou vermelho
        reset = "\033[0m"

        print(f"{color}{status}{reset} {name}")
        if details:
            print(f"  {details}")

        self.results.append((name, passed, details))

    def check_docker_services(self) -> bool:
        """Verifica se os containers Docker estão rodando"""
        self.print_header("VERIFICAÇÃO DE CONTAINERS DOCKER")

        try:
            result = subprocess.run(
                ['docker-compose', 'ps', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                self.print_test(
                    "Docker Compose",
                    False,
                    "Não foi possível executar docker-compose ps"
                )
                return False

            # Parse JSON output
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        containers.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

            expected_services = [
                'postgres', 'influxdb', 'redis', 'rabbitmq',
                'backend', 'celery-worker', 'celery-beat',
                'gateway', 'frontend', 'mlflow', 'grafana'
            ]

            running_services = []
            for container in containers:
                state = container.get('State', '')
                name = container.get('Service', '')
                if state == 'running':
                    running_services.append(name)
                    self.print_test(f"Container: {name}", True, f"Estado: {state}")
                else:
                    self.print_test(f"Container: {name}", False, f"Estado: {state}")

            # Verificar se todos os serviços essenciais estão rodando
            all_running = all(svc in running_services for svc in expected_services)

            return all_running

        except subprocess.TimeoutExpired:
            self.print_test("Docker Compose", False, "Timeout ao verificar containers")
            return False
        except FileNotFoundError:
            self.print_test("Docker Compose", False, "docker-compose não encontrado")
            return False
        except Exception as e:
            self.print_test("Docker Compose", False, f"Erro: {str(e)}")
            return False

    def check_backend_api(self) -> bool:
        """Verifica se o backend está acessível"""
        self.print_header("VERIFICAÇÃO DO BACKEND API")

        # Health check
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=5)
            self.print_test(
                "Health Check",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except requests.exceptions.RequestException as e:
            self.print_test("Health Check", False, f"Erro: {str(e)}")
            return False

        # Swagger docs
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            self.print_test(
                "Swagger UI",
                response.status_code == 200,
                "Disponível em /docs"
            )
        except requests.exceptions.RequestException as e:
            self.print_test("Swagger UI", False, f"Erro: {str(e)}")

        # ReDoc
        try:
            response = requests.get(f"{self.base_url}/redoc", timeout=5)
            self.print_test(
                "ReDoc",
                response.status_code == 200,
                "Disponível em /redoc"
            )
        except requests.exceptions.RequestException as e:
            self.print_test("ReDoc", False, f"Erro: {str(e)}")

        return True

    def check_databases(self, token: Optional[str] = None) -> bool:
        """Verifica conectividade com bancos de dados"""
        self.print_header("VERIFICAÇÃO DE BANCOS DE DADOS")

        # PostgreSQL
        try:
            result = subprocess.run(
                [
                    'docker', 'exec', 'optiflow-ai--postgres-1',
                    'psql', '-U', 'optiflow', '-d', 'optiflow',
                    '-c', 'SELECT 1;'
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.print_test(
                "PostgreSQL",
                result.returncode == 0,
                "Porta: 5432"
            )
        except Exception as e:
            self.print_test("PostgreSQL", False, f"Erro: {str(e)}")

        # InfluxDB
        try:
            result = subprocess.run(
                [
                    'docker', 'exec', 'optiflow-ai--influxdb-1',
                    'influx', 'ping'
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.print_test(
                "InfluxDB",
                result.returncode == 0,
                "Porta: 8086"
            )
        except Exception as e:
            self.print_test("InfluxDB", False, f"Erro: {str(e)}")

        # Redis
        try:
            result = subprocess.run(
                [
                    'docker', 'exec', 'optiflow-ai--redis-1',
                    'redis-cli', 'ping'
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.print_test(
                "Redis",
                'PONG' in result.stdout,
                "Porta: 6379"
            )
        except Exception as e:
            self.print_test("Redis", False, f"Erro: {str(e)}")

        return True

    def check_web_interfaces(self) -> bool:
        """Verifica interfaces web"""
        self.print_header("VERIFICAÇÃO DE INTERFACES WEB")

        interfaces = [
            ("Frontend", "http://localhost:5173", 200),
            ("Backend API Docs", "http://localhost:8000/docs", 200),
            ("MLflow", "http://localhost:5000", 200),
            ("Grafana", "http://localhost:3000", 200),
            ("RabbitMQ Management", "http://localhost:15672", 200),
        ]

        for name, url, expected_status in interfaces:
            try:
                response = requests.get(url, timeout=5, allow_redirects=True)
                self.print_test(
                    name,
                    response.status_code == expected_status,
                    f"{url} → {response.status_code}"
                )
            except requests.exceptions.RequestException as e:
                self.print_test(name, False, f"{url} → Erro: {str(e)}")

        return True

    def check_smartport_data(self, config_file: str = 'smartport_config.json') -> bool:
        """Verifica dados do SmartPort se configuração existir"""
        self.print_header("VERIFICAÇÃO DE DADOS SMARTPORT")

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            self.print_test(
                "Configuração SmartPort",
                False,
                "Arquivo smartport_config.json não encontrado. Execute smartport_setup.py primeiro."
            )
            return False

        token = config.get('token')
        if not token:
            self.print_test("Token de autenticação", False, "Token não encontrado")
            return False

        headers = {"Authorization": f"Bearer {token}"}

        # Verificar organização
        org_id = config['resources']['organization']['id']
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/organizations/{org_id}",
                headers=headers,
                timeout=5
            )
            self.print_test(
                "Organização",
                response.status_code == 200,
                f"ID: {org_id}"
            )
        except requests.exceptions.RequestException as e:
            self.print_test("Organização", False, f"Erro: {str(e)}")

        # Verificar site
        site_id = config['resources']['site']['id']
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/sites/{site_id}",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                site = response.json()
                self.print_test(
                    "Site SmartPort",
                    site.get('site_type') == 'smartport',
                    f"ID: {site_id}, Tipo: {site.get('site_type')}"
                )
            else:
                self.print_test("Site SmartPort", False, f"Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.print_test("Site SmartPort", False, f"Erro: {str(e)}")

        # Verificar dispositivo
        device_id = config['resources']['device']['id']
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/devices/{device_id}",
                headers=headers,
                timeout=5
            )
            self.print_test(
                "Dispositivo PLC",
                response.status_code == 200,
                f"ID: {device_id}"
            )
        except requests.exceptions.RequestException as e:
            self.print_test("Dispositivo PLC", False, f"Erro: {str(e)}")

        # Verificar tags
        tags_count = len(config['resources']['tags'])
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/tags/?device_id={device_id}",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                tags = response.json()
                self.print_test(
                    "Tags de Processo",
                    len(tags) == tags_count,
                    f"Encontradas: {len(tags)}, Esperadas: {tags_count}"
                )
            else:
                self.print_test("Tags de Processo", False, f"Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.print_test("Tags de Processo", False, f"Erro: {str(e)}")

        # Verificar se há dados de séries temporais
        if tags_count > 0:
            tag_id = config['resources']['tags'][0]['id']
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/timeseries/tags/{tag_id}/latest",
                    headers=headers,
                    timeout=5
                )
                has_data = response.status_code == 200 and response.json() is not None
                self.print_test(
                    "Dados de Séries Temporais",
                    has_data,
                    "Execute smartport_simulate.py para gerar dados" if not has_data else "Dados encontrados"
                )
            except requests.exceptions.RequestException as e:
                self.print_test("Dados de Séries Temporais", False, f"Erro: {str(e)}")

        return True

    def print_summary(self):
        """Imprime resumo dos resultados"""
        self.print_header("RESUMO DA VERIFICAÇÃO")

        total = len(self.results)
        passed = sum(1 for _, p, _ in self.results if p)
        failed = total - passed

        print(f"\nTotal de testes: {total}")
        print(f"✓ Aprovados: {passed}")
        print(f"✗ Reprovados: {failed}")
        print(f"Taxa de sucesso: {(passed/total*100):.1f}%\n")

        if failed > 0:
            print("Testes que falharam:")
            for name, passed, details in self.results:
                if not passed:
                    print(f"  • {name}")
                    if details:
                        print(f"    {details}")

        print("\n" + "="*70)

        if failed == 0:
            print("✅ TODOS OS TESTES PASSARAM!")
            print("="*70)
            print("\nO SmartPort está funcionando corretamente.")
            print("\nPróximos passos:")
            print("  1. Execute: python scripts/smartport_simulate.py")
            print("  2. Acesse: http://localhost:8000/docs")
            print("  3. Configure dashboards no Grafana: http://localhost:3000")
        else:
            print("❌ ALGUNS TESTES FALHARAM")
            print("="*70)
            print("\nVerifique os erros acima e:")
            print("  1. Certifique-se que todos os containers estão rodando: docker-compose ps")
            print("  2. Verifique os logs: docker-compose logs -f")
            print("  3. Execute o setup: python scripts/smartport_setup.py")

        print("\n")

        return failed == 0

    def run(self, check_data: bool = True):
        """Executa todas as verificações"""
        print("\n" + "="*70)
        print("  🔍 VERIFICAÇÃO DO SISTEMA SMARTPORT")
        print("="*70)
        print(f"  Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

        self.check_docker_services()
        self.check_backend_api()
        self.check_databases()
        self.check_web_interfaces()

        if check_data:
            self.check_smartport_data()

        success = self.print_summary()

        return 0 if success else 1

def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Verificação do sistema SmartPort')
    parser.add_argument(
        '--no-data',
        action='store_true',
        help='Não verificar dados do SmartPort'
    )

    args = parser.parse_args()

    verifier = SmartPortVerifier()
    exit_code = verifier.run(check_data=not args.no_data)

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
