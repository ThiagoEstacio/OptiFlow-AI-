#!/usr/bin/env python3
"""
Teste Completo de Todos os Serviços do OptiFlow AI
Testa: Docker, Backend, Frontend, Simulador, APIs, Banco de Dados
"""

import requests
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Tuple

# Configurações
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
INFLUXDB_URL = "http://localhost:8086"
GRAFANA_URL = "http://localhost:3001"
KAFKA_UI_URL = "http://localhost:8090"

# Cores para output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

class ServiceTester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def print_header(self, title: str):
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}{title.center(70)}{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")

    def print_test(self, test_name: str, status: bool, message: str = ""):
        self.total_tests += 1
        if status:
            self.passed_tests += 1
            status_str = f"{GREEN}✓ PASS{RESET}"
        else:
            self.failed_tests += 1
            status_str = f"{RED}✗ FAIL{RESET}"

        print(f"  {status_str} {test_name}")
        if message:
            print(f"       {YELLOW}{message}{RESET}")

        self.results.append({
            "test": test_name,
            "status": "PASS" if status else "FAIL",
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def test_docker_containers(self):
        """Testa se os containers Docker estão rodando"""
        self.print_header("1. TESTE DE CONTAINERS DOCKER")

        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=10
            )

            containers = result.stdout.strip().split("\n")
            required_containers = [
                "optiflow-backend",
                "optiflow-frontend",
                "optiflow-postgres",
                "optiflow-influxdb",
                "optiflow-redis",
                "optiflow-kafka"
            ]

            running_containers = [line.split("\t")[0] for line in containers if line]

            for container in required_containers:
                is_running = container in running_containers
                status_line = next((l for l in containers if container in l), "")
                self.print_test(
                    f"Container {container}",
                    is_running,
                    status_line.split("\t")[1] if "\t" in status_line else "Not found"
                )

        except Exception as e:
            self.print_test("Docker check", False, str(e))

    def test_backend_health(self):
        """Testa o health check do backend"""
        self.print_header("2. TESTE DO BACKEND")

        # Test 1: Health endpoint
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            self.print_test(
                "Backend /health endpoint",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("Backend /health endpoint", False, str(e))

        # Test 2: API docs
        try:
            response = requests.get(f"{BACKEND_URL}/docs", timeout=5)
            self.print_test(
                "Backend /docs (Swagger)",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("Backend /docs (Swagger)", False, str(e))

        # Test 3: API v1 base
        try:
            response = requests.get(f"{BACKEND_URL}/api/v1/", timeout=5)
            self.print_test(
                "Backend /api/v1/",
                response.status_code in [200, 404, 307],  # 404 ou redirect é ok
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("Backend /api/v1/", False, str(e))

    def test_backend_endpoints(self):
        """Testa endpoints principais da API"""
        self.print_header("3. TESTE DE ENDPOINTS DA API")

        endpoints = [
            ("/api/v1/simulator/status", "GET", "Status do simulador"),
            ("/api/v1/ai/insights/autonomous", "GET", "Insights do Autonomous Agent"),
            ("/api/v1/tags/", "GET", "Lista de tags"),
            ("/api/v1/sites/", "GET", "Lista de sites"),
        ]

        for path, method, description in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{BACKEND_URL}{path}", timeout=5)

                self.print_test(
                    description,
                    response.status_code in [200, 401, 403],  # 401/403 = precisa auth
                    f"Status: {response.status_code}, Response length: {len(response.text)}"
                )
            except Exception as e:
                self.print_test(description, False, str(e))

    def test_database(self):
        """Testa conexão com banco de dados"""
        self.print_header("4. TESTE DO BANCO DE DADOS")

        try:
            result = subprocess.run(
                ["docker", "exec", "optiflow-postgres",
                 "psql", "-U", "optiflow_user", "-d", "optiflow_db",
                 "-c", "SELECT COUNT(*) FROM tags;"],
                capture_output=True,
                text=True,
                timeout=10
            )

            has_tags = "count" in result.stdout.lower()
            self.print_test(
                "PostgreSQL - Tabela tags",
                has_tags,
                "Tags table exists and queryable" if has_tags else "Cannot query tags"
            )

            # Contar quantas tags existem
            if has_tags:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if line.strip().isdigit():
                        tag_count = int(line.strip())
                        self.print_test(
                            f"Total de tags no banco",
                            tag_count > 0,
                            f"{tag_count} tags encontradas"
                        )
                        break

        except Exception as e:
            self.print_test("Database check", False, str(e))

    def test_influxdb(self):
        """Testa InfluxDB"""
        self.print_header("5. TESTE DO INFLUXDB")

        try:
            # Test health
            response = requests.get(f"{INFLUXDB_URL}/health", timeout=5)
            self.print_test(
                "InfluxDB /health",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )

            # Test API
            response = requests.get(f"{INFLUXDB_URL}/api/v2/ping", timeout=5)
            self.print_test(
                "InfluxDB /api/v2/ping",
                response.status_code == 204,
                f"Status: {response.status_code}"
            )

        except Exception as e:
            self.print_test("InfluxDB check", False, str(e))

    def test_frontend(self):
        """Testa o frontend"""
        self.print_header("6. TESTE DO FRONTEND")

        try:
            response = requests.get(FRONTEND_URL, timeout=10)
            self.print_test(
                "Frontend homepage",
                response.status_code == 200,
                f"Status: {response.status_code}, Length: {len(response.text)}"
            )

            # Check if it's actually React app
            has_react = "react" in response.text.lower() or "root" in response.text
            self.print_test(
                "Frontend React app",
                has_react,
                "React app detected" if has_react else "No React detected"
            )

        except Exception as e:
            self.print_test("Frontend check", False, str(e))

    def test_monitoring(self):
        """Testa serviços de monitoramento"""
        self.print_header("7. TESTE DE MONITORAMENTO")

        # Grafana
        try:
            response = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
            self.print_test(
                "Grafana",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("Grafana", False, str(e))

        # Kafka UI
        try:
            response = requests.get(KAFKA_UI_URL, timeout=5)
            self.print_test(
                "Kafka UI",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("Kafka UI", False, str(e))

    def test_simulator(self):
        """Testa o simulador"""
        self.print_header("8. TESTE DO SIMULADOR")

        try:
            # Status
            response = requests.get(f"{BACKEND_URL}/api/v1/simulator/status", timeout=5)
            self.print_test(
                "Simulador - Status",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )

            if response.status_code == 200:
                data = response.json()
                self.print_test(
                    "Simulador - Running",
                    data.get("is_running", False),
                    f"Running: {data.get('is_running')}, Time: {data.get('current_time', 'N/A')}"
                )

        except Exception as e:
            self.print_test("Simulator check", False, str(e))

    def print_summary(self):
        """Imprime resumo dos testes"""
        self.print_header("RESUMO DOS TESTES")

        percentage = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0

        print(f"  Total de testes: {self.total_tests}")
        print(f"  {GREEN}Passou: {self.passed_tests}{RESET}")
        print(f"  {RED}Falhou: {self.failed_tests}{RESET}")
        print(f"  Taxa de sucesso: {percentage:.1f}%\n")

        if percentage >= 90:
            print(f"  {GREEN}✓ Sistema está saudável (>= 90%){RESET}")
        elif percentage >= 70:
            print(f"  {YELLOW}⚠ Sistema funcional mas com problemas (70-89%){RESET}")
        else:
            print(f"  {RED}✗ Sistema com problemas críticos (< 70%){RESET}")

    def save_results(self):
        """Salva resultados em arquivo JSON"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": self.total_tests,
                "passed": self.passed_tests,
                "failed": self.failed_tests,
                "percentage": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
            },
            "tests": self.results
        }

        filename = f"/home/thiestacio/OptiFlow-AI-/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n  Relatório salvo em: {filename}\n")
        return filename

    def run_all_tests(self):
        """Executa todos os testes"""
        print(f"\n{BLUE}{'='*70}")
        print(f"TESTE COMPLETO DO OPTIFLOW AI - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}{RESET}\n")

        self.test_docker_containers()
        self.test_backend_health()
        self.test_backend_endpoints()
        self.test_database()
        self.test_influxdb()
        self.test_frontend()
        self.test_monitoring()
        self.test_simulator()

        self.print_summary()
        report_file = self.save_results()

        return self.passed_tests / self.total_tests >= 0.7 if self.total_tests > 0 else False

if __name__ == "__main__":
    tester = ServiceTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
