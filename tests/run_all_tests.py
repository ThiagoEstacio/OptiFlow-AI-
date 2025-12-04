#!/usr/bin/env python3
"""
OptiFlow AI - Test Runner
=========================

Este script executa todos os testes automatizados do sistema:
1. Testes de API Backend (endpoints REST)
2. Testes de Integração (Gateway, Kafka, InfluxDB)
3. Testes de Frontend (se disponíveis)

Uso:
    python tests/run_all_tests.py [--backend] [--frontend] [--integration] [--all]
"""

import sys
import os
import time
import json
import asyncio
import argparse
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    os.system(f"{sys.executable} -m pip install httpx")
    import httpx


@dataclass
class TestResult:
    """Result of a single test"""
    name: str
    passed: bool
    duration_ms: float
    error: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuite:
    """Collection of test results"""
    name: str
    results: List[TestResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def duration_ms(self) -> float:
        return sum(r.duration_ms for r in self.results)


class OptiFlowTestRunner:
    """Main test runner for OptiFlow AI"""

    def __init__(self, backend_url: str = "http://localhost:8000", gateway_url: str = "http://localhost:8080"):
        self.backend_url = backend_url
        self.gateway_url = gateway_url
        self.token: str = ""
        self.suites: List[TestSuite] = []

    async def setup(self) -> bool:
        """Setup test environment and get auth token"""
        print("\n🔧 Setting up test environment...")

        # Check if backend is running
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.backend_url}/api/health", timeout=5.0)
                if response.status_code != 200:
                    print(f"❌ Backend health check failed: {response.status_code}")
                    return False
                print("✅ Backend is healthy")
        except Exception as e:
            print(f"❌ Cannot connect to backend: {e}")
            return False

        # Login to get token (uses form data, not JSON)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.backend_url}/api/v1/auth/login",
                    data={"username": "admin@optiflow.com", "password": "admin123"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("access_token", "")
                    print("✅ Authentication successful")
                else:
                    print(f"⚠️ Login failed: {response.status_code} - Using demo mode")
        except Exception as e:
            print(f"⚠️ Login error: {e} - Using demo mode")

        return True

    async def run_test(self, name: str, test_func) -> TestResult:
        """Run a single test and return result"""
        start = time.time()
        try:
            result = await test_func()
            duration_ms = (time.time() - start) * 1000
            if isinstance(result, tuple):
                passed, details = result
            else:
                passed, details = result, {}
            return TestResult(
                name=name,
                passed=passed,
                duration_ms=duration_ms,
                details=details
            )
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            return TestResult(
                name=name,
                passed=False,
                duration_ms=duration_ms,
                error=str(e)
            )

    def get_headers(self) -> Dict[str, str]:
        """Get auth headers"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    # ========== Backend API Tests ==========

    async def test_health_endpoint(self) -> Tuple[bool, Dict]:
        """Test /api/health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.backend_url}/api/health", timeout=5.0)
            return response.status_code == 200, {"status": response.status_code}

    async def test_dashboard_stats(self) -> Tuple[bool, Dict]:
        """Test /api/v1/dashboard/stats endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.backend_url}/api/v1/dashboard/stats",
                headers=self.get_headers(),
                timeout=10.0
            )
            return response.status_code == 200, {"status": response.status_code}

    async def test_tags_list(self) -> Tuple[bool, Dict]:
        """Test /api/v1/tags endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.backend_url}/api/v1/tags",
                headers=self.get_headers(),
                params={"limit": 10},
                timeout=10.0
            )
            passed = response.status_code == 200
            data = response.json() if passed else {}
            return passed, {"count": len(data.get("items", [])) if isinstance(data, dict) else 0}

    async def test_quality_spc(self) -> Tuple[bool, Dict]:
        """Test /api/v1/quality/spc/analysis endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.backend_url}/api/v1/quality/spc/analysis",
                headers=self.get_headers(),
                params={"tag_id": "temp_001", "time_range": "24h"},
                timeout=15.0
            )
            return response.status_code == 200, {"status": response.status_code}

    async def test_maintenance_kpis(self) -> Tuple[bool, Dict]:
        """Test /api/v1/maintenance/kpis/all endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.backend_url}/api/v1/maintenance/kpis/all",
                headers=self.get_headers(),
                timeout=15.0
            )
            return response.status_code == 200, {"status": response.status_code}

    async def test_executive_summary(self) -> Tuple[bool, Dict]:
        """Test /api/v1/executive-summary/overview endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.backend_url}/api/v1/executive-summary/overview",
                headers=self.get_headers(),
                timeout=15.0
            )
            return response.status_code == 200, {"status": response.status_code}

    async def test_alarms_list(self) -> Tuple[bool, Dict]:
        """Test /api/v1/alarms endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.backend_url}/api/v1/alarms",
                headers=self.get_headers(),
                params={"limit": 10},
                timeout=10.0
            )
            passed = response.status_code in [200, 404]
            return passed, {"status": response.status_code}

    async def test_energy_dashboard(self) -> Tuple[bool, Dict]:
        """Test /api/v1/executive-summary/energy endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.backend_url}/api/v1/executive-summary/energy",
                headers=self.get_headers(),
                params={"time_range": "24h"},
                timeout=15.0
            )
            return response.status_code == 200, {"status": response.status_code}

    async def test_ml_anomaly_detection(self) -> Tuple[bool, Dict]:
        """Test /api/v1/ml/anomaly/detect endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.backend_url}/api/v1/ml/anomaly/detect",
                headers=self.get_headers(),
                params={"tag_id": "temp_001", "time_range": "24h"},
                timeout=20.0
            )
            return response.status_code == 200, {"status": response.status_code}

    async def test_pdca_cycles(self) -> Tuple[bool, Dict]:
        """Test /api/v1/pdca/cycles endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.backend_url}/api/v1/pdca/cycles",
                headers=self.get_headers(),
                timeout=10.0
            )
            return response.status_code == 200, {"status": response.status_code}

    async def run_backend_tests(self) -> TestSuite:
        """Run all backend API tests"""
        suite = TestSuite(name="Backend API Tests")

        tests = [
            ("Health Check", self.test_health_endpoint),
            ("Dashboard Stats", self.test_dashboard_stats),
            ("Tags List", self.test_tags_list),
            ("Quality SPC Analysis", self.test_quality_spc),
            ("Maintenance KPIs", self.test_maintenance_kpis),
            ("Executive Summary", self.test_executive_summary),
            ("Alarms List", self.test_alarms_list),
            ("Energy Dashboard", self.test_energy_dashboard),
            ("ML Anomaly Detection", self.test_ml_anomaly_detection),
            ("PDCA Cycles", self.test_pdca_cycles),
        ]

        for name, test_func in tests:
            result = await self.run_test(name, test_func)
            suite.results.append(result)
            status = "✅" if result.passed else "❌"
            print(f"  {status} {name} ({result.duration_ms:.0f}ms)")
            if result.error:
                print(f"      Error: {result.error}")

        return suite

    # ========== Gateway Tests ==========

    async def test_gateway_health(self) -> Tuple[bool, Dict]:
        """Test Gateway health endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.gateway_url}/health", timeout=5.0)
            return response.status_code == 200, {"status": response.status_code}

    async def test_gateway_adapters(self) -> Tuple[bool, Dict]:
        """Test Gateway adapters endpoint"""
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(f"{self.gateway_url}/api/adapters/", timeout=10.0)
            passed = response.status_code == 200
            data = response.json() if passed else {}
            return passed, {"adapters": len(data) if isinstance(data, list) else 0}

    async def test_gateway_tags(self) -> Tuple[bool, Dict]:
        """Test Gateway tags endpoint"""
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(f"{self.gateway_url}/api/tags/", timeout=10.0)
            passed = response.status_code == 200
            data = response.json() if passed else {}
            return passed, {"tags": len(data) if isinstance(data, list) else 0}

    async def test_gateway_realtime(self) -> Tuple[bool, Dict]:
        """Test Gateway realtime values endpoint"""
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(f"{self.gateway_url}/api/tags/realtime/", timeout=10.0)
            passed = response.status_code == 200
            return passed, {"status": response.status_code}

    async def run_gateway_tests(self) -> TestSuite:
        """Run all gateway tests"""
        suite = TestSuite(name="Gateway Integration Tests")

        tests = [
            ("Gateway Health", self.test_gateway_health),
            ("Gateway Adapters", self.test_gateway_adapters),
            ("Gateway Tags", self.test_gateway_tags),
            ("Gateway Realtime Values", self.test_gateway_realtime),
        ]

        for name, test_func in tests:
            result = await self.run_test(name, test_func)
            suite.results.append(result)
            status = "✅" if result.passed else "❌"
            print(f"  {status} {name} ({result.duration_ms:.0f}ms)")
            if result.error:
                print(f"      Error: {result.error}")

        return suite

    # ========== Integration Tests ==========

    async def test_data_pipeline(self) -> Tuple[bool, Dict]:
        """Test complete data pipeline (Gateway -> Kafka -> InfluxDB)"""
        async with httpx.AsyncClient() as client:
            # Get pipeline status
            response = await client.get(
                f"{self.backend_url}/api/v1/pipeline/status",
                headers=self.get_headers(),
                timeout=15.0
            )
            if response.status_code == 200:
                data = response.json()
                is_operational = data.get("status") == "operational"
                return is_operational, data
            return False, {"status": response.status_code}

    async def test_websocket_connection(self) -> Tuple[bool, Dict]:
        """Test WebSocket connection (basic check)"""
        # Just check if the endpoint exists
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.backend_url}/api/v1/ws/status",
                headers=self.get_headers(),
                timeout=5.0
            )
            # WebSocket upgrade endpoint may return different codes
            return response.status_code in [200, 400, 426], {"status": response.status_code}

    async def run_integration_tests(self) -> TestSuite:
        """Run all integration tests"""
        suite = TestSuite(name="Integration Tests")

        tests = [
            ("Data Pipeline Status", self.test_data_pipeline),
        ]

        for name, test_func in tests:
            result = await self.run_test(name, test_func)
            suite.results.append(result)
            status = "✅" if result.passed else "❌"
            print(f"  {status} {name} ({result.duration_ms:.0f}ms)")
            if result.error:
                print(f"      Error: {result.error}")

        return suite

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        total_passed = 0
        total_failed = 0
        total_duration = 0

        for suite in self.suites:
            print(f"\n📁 {suite.name}")
            print(f"   Passed: {suite.passed}/{suite.total}")
            print(f"   Failed: {suite.failed}/{suite.total}")
            print(f"   Duration: {suite.duration_ms:.0f}ms")

            total_passed += suite.passed
            total_failed += suite.failed
            total_duration += suite.duration_ms

            if suite.failed > 0:
                print("   Failed tests:")
                for result in suite.results:
                    if not result.passed:
                        print(f"     ❌ {result.name}")
                        if result.error:
                            print(f"        {result.error[:100]}")

        print("\n" + "-" * 60)
        print(f"TOTAL: {total_passed}/{total_passed + total_failed} tests passed")
        print(f"Duration: {total_duration/1000:.1f}s")
        print("=" * 60)

        return total_failed == 0

    def save_report(self, filepath: str = "test_report.json"):
        """Save test report to JSON file"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "suites": []
        }

        for suite in self.suites:
            suite_data = {
                "name": suite.name,
                "total": suite.total,
                "passed": suite.passed,
                "failed": suite.failed,
                "duration_ms": suite.duration_ms,
                "tests": []
            }
            for result in suite.results:
                suite_data["tests"].append({
                    "name": result.name,
                    "passed": result.passed,
                    "duration_ms": result.duration_ms,
                    "error": result.error,
                    "details": result.details
                })
            report["suites"].append(suite_data)

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Report saved to: {filepath}")


async def main():
    parser = argparse.ArgumentParser(description="OptiFlow AI Test Runner")
    parser.add_argument("--backend", action="store_true", help="Run backend API tests")
    parser.add_argument("--gateway", action="store_true", help="Run gateway tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--report", type=str, default="test_report.json", help="Report output file")
    args = parser.parse_args()

    # Default to all if no specific tests selected
    if not any([args.backend, args.gateway, args.integration, args.all]):
        args.all = True

    print("=" * 60)
    print("🧪 OptiFlow AI - Automated Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    runner = OptiFlowTestRunner()

    if not await runner.setup():
        print("\n❌ Setup failed. Make sure Docker containers are running.")
        print("   Run: docker-compose up -d")
        sys.exit(1)

    if args.all or args.backend:
        print("\n🔬 Running Backend API Tests...")
        suite = await runner.run_backend_tests()
        runner.suites.append(suite)

    if args.all or args.gateway:
        print("\n🔬 Running Gateway Tests...")
        suite = await runner.run_gateway_tests()
        runner.suites.append(suite)

    if args.all or args.integration:
        print("\n🔬 Running Integration Tests...")
        suite = await runner.run_integration_tests()
        runner.suites.append(suite)

    success = runner.print_summary()
    runner.save_report(args.report)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
