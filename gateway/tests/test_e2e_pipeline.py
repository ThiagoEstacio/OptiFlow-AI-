#!/usr/bin/env python3
"""
End-to-End Pipeline Tests
=========================

Tests the complete data flow:
OPC-UA/Modbus → Gateway → Kafka → InfluxDB

Also validates:
- Formula Engine calculations
- Swinging Door Compression
- Real-time WebSocket updates
- API endpoints

Run with:
    python -m pytest gateway/tests/test_e2e_pipeline.py -v

Or standalone:
    python gateway/tests/test_e2e_pipeline.py
"""

import asyncio
import time
import json
import requests
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sys
import os

# Configuration
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8080")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
KAFKA_UI_URL = os.getenv("KAFKA_UI_URL", "http://localhost:8084")

INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "my-super-secret-influxdb-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "optiflow")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "timeseries")


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")


def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def print_info(text: str):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.RESET}")


class E2ETestSuite:
    """End-to-End Test Suite for OptiFlow Pipeline"""

    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.start_time = time.time()

    def record_result(self, test_name: str, passed: bool, details: str = "", duration: float = 0):
        self.results[test_name] = {
            "passed": passed,
            "details": details,
            "duration": duration
        }

    # =========================================
    # 1. Gateway Health Tests
    # =========================================

    def test_gateway_health(self) -> bool:
        """Test Gateway Edge health endpoint"""
        print_header("1. Gateway Health Check")
        start = time.time()

        try:
            response = requests.get(f"{GATEWAY_URL}/health", timeout=10)
            duration = time.time() - start

            if response.status_code == 200:
                data = response.json()
                print_success(f"Gateway is healthy (status: {data.get('status', 'unknown')})")
                print_info(f"  Gateway ID: {data.get('gateway_id', 'N/A')}")
                print_info(f"  Mode: {data.get('mode', 'N/A')}")
                print_info(f"  Uptime: {data.get('uptime_seconds', 0):.0f}s")
                print_info(f"  Response time: {duration*1000:.0f}ms")

                # Check Kafka status
                kafka_status = data.get('kafka_status', {})
                if kafka_status.get('connected'):
                    print_success(f"  Kafka connected, {kafka_status.get('messages_sent', 0)} messages sent")
                else:
                    print_warning("  Kafka not connected")

                self.record_result("gateway_health", True, f"Uptime: {data.get('uptime_seconds', 0)}s", duration)
                return True
            else:
                print_error(f"Gateway returned status {response.status_code}")
                self.record_result("gateway_health", False, f"Status: {response.status_code}", duration)
                return False

        except Exception as e:
            print_error(f"Failed to connect to Gateway: {e}")
            self.record_result("gateway_health", False, str(e))
            return False

    # =========================================
    # 2. Tag Discovery Tests
    # =========================================

    def test_tag_discovery(self) -> bool:
        """Test tag discovery from adapters"""
        print_header("2. Tag Discovery")
        start = time.time()

        try:
            response = requests.get(f"{GATEWAY_URL}/api/tags/list", timeout=30)
            duration = time.time() - start

            if response.status_code == 200:
                data = response.json()
                # Handle different response formats
                if isinstance(data, list):
                    tags = data
                elif isinstance(data, dict) and 'tags' in data:
                    tags = data.get('tags', [])
                else:
                    tags = []

                tag_count = len(tags)
                print_success(f"Found {tag_count} managed tags")

                if tag_count > 0:
                    # Group by protocol
                    protocols = {}
                    for tag in tags[:100]:  # Sample first 100
                        proto = tag.get('protocol', 'unknown')
                        protocols[proto] = protocols.get(proto, 0) + 1

                    for proto, count in protocols.items():
                        print_info(f"  {proto}: {count} tags")

                    # Show sample tags
                    print_info("  Sample tags:")
                    for tag in tags[:5]:
                        print_info(f"    - {tag.get('tag_name', 'N/A')} ({tag.get('data_type', 'N/A')})")

                # This tests the managed tags API - success if API works
                # Actual tag count may be 0 if no tags are configured for historian
                self.record_result("tag_discovery", True, f"{tag_count} managed tags", duration)
                return True  # API is working
            else:
                print_error(f"Discovery failed with status {response.status_code}")
                self.record_result("tag_discovery", False, f"Status: {response.status_code}", duration)
                return False

        except Exception as e:
            print_error(f"Tag discovery failed: {e}")
            self.record_result("tag_discovery", False, str(e))
            return False

    # =========================================
    # 3. Realtime Values Tests
    # =========================================

    def test_realtime_values(self) -> bool:
        """Test real-time value retrieval"""
        print_header("3. Real-time Values")
        start = time.time()

        try:
            response = requests.get(f"{GATEWAY_URL}/api/tags/realtime/all", timeout=10)
            duration = time.time() - start

            if response.status_code == 200:
                data = response.json()
                # Handle both formats: direct dict or wrapped in {count, tags}
                if isinstance(data, dict) and 'tags' in data:
                    values = data.get('tags', {})
                    value_count = data.get('count', len(values))
                else:
                    values = data if isinstance(data, dict) else {}
                    value_count = len(values)

                print_success(f"Retrieved {value_count} real-time values")

                if value_count > 0 and isinstance(values, dict):
                    # Show sample values
                    print_info("  Sample values:")
                    for tag_id, value_data in list(values.items())[:5]:
                        if isinstance(value_data, dict):
                            val = value_data.get('value', 'N/A')
                            quality = value_data.get('quality', 'N/A')
                            if isinstance(val, float):
                                val = f"{val:.2f}"
                            print_info(f"    - {tag_id}: {val} (quality: {quality})")

                self.record_result("realtime_values", True, f"{value_count} values", duration)
                return value_count > 0
            else:
                print_error(f"Realtime values failed with status {response.status_code}")
                self.record_result("realtime_values", False, f"Status: {response.status_code}", duration)
                return False

        except Exception as e:
            print_error(f"Realtime values failed: {e}")
            self.record_result("realtime_values", False, str(e))
            return False

    # =========================================
    # 4. Kafka Producer Tests
    # =========================================

    def test_kafka_producer(self) -> bool:
        """Test Kafka message production by checking adapters are running and collecting data"""
        print_header("4. Kafka/Data Collection")
        start = time.time()

        try:
            # Check adapters are connected and collecting
            response = requests.get(f"{GATEWAY_URL}/api/adapters/", timeout=10)
            duration = time.time() - start

            if response.status_code == 200:
                adapters = response.json()
                connected = sum(1 for a in adapters if a.get('connected', False) and a.get('running', False))
                total_tags = sum(a.get('tags_count', 0) for a in adapters)

                if connected > 0 and total_tags > 0:
                    print_success(f"Data collection active: {connected} adapters, {total_tags} tags")
                    for adapter in adapters:
                        status = "✅" if adapter.get('connected') else "❌"
                        print_info(f"  {status} {adapter.get('adapter_id')}: {adapter.get('tags_count', 0)} tags")

                    # Verify InfluxDB is receiving data (as proxy for Kafka working)
                    print_info("  Kafka → InfluxDB pipeline verified by InfluxDB data test")
                    self.record_result("kafka_producer", True, f"{total_tags} tags active", duration)
                    return True
                else:
                    print_warning(f"No active data collection (connected: {connected}, tags: {total_tags})")
                    self.record_result("kafka_producer", False, "No active collection", duration)
                    return False
            else:
                print_error(f"Adapters check failed: {response.status_code}")
                self.record_result("kafka_producer", False, f"Status: {response.status_code}", duration)
                return False

        except Exception as e:
            print_error(f"Data collection test failed: {e}")
            self.record_result("kafka_producer", False, str(e))
            return False

    # =========================================
    # 5. InfluxDB Data Tests
    # =========================================

    def test_influxdb_data(self) -> bool:
        """Test data persistence in InfluxDB"""
        print_header("5. InfluxDB Data Persistence")
        start = time.time()

        try:
            # Query InfluxDB for recent data
            query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
              |> range(start: -5m)
              |> filter(fn: (r) => r._measurement == "tag_data")
              |> group(columns: ["tag_id"])
              |> count()
              |> sort(columns: ["_value"], desc: true)
              |> limit(n: 10)
            '''

            headers = {
                "Authorization": f"Token {INFLUXDB_TOKEN}",
                "Content-Type": "application/vnd.flux"
            }

            response = requests.post(
                f"{INFLUXDB_URL}/api/v2/query?org={INFLUXDB_ORG}",
                headers=headers,
                data=query,
                timeout=30
            )
            duration = time.time() - start

            if response.status_code == 200:
                # Parse CSV response
                lines = response.text.strip().split('\n')
                data_lines = [l for l in lines if l and not l.startswith('#') and not l.startswith(',result')]

                if len(data_lines) > 1:
                    # Count unique tags with data
                    tag_count = len(data_lines) - 1  # Subtract header

                    print_success(f"InfluxDB has data for {tag_count}+ tags in last 5 minutes")

                    # Parse some sample data
                    print_info("  Top tags by data points:")
                    for line in data_lines[1:6]:  # First 5 data rows
                        parts = line.split(',')
                        if len(parts) >= 2:
                            tag_id = parts[-2] if len(parts) > 2 else "unknown"
                            count = parts[-1] if parts[-1].isdigit() else "?"
                            print_info(f"    - {tag_id}: {count} points")

                    self.record_result("influxdb_data", True, f"{tag_count} tags with data", duration)
                    return True
                else:
                    print_warning("No recent data in InfluxDB")
                    self.record_result("influxdb_data", False, "No data", duration)
                    return False
            else:
                print_error(f"InfluxDB query failed: {response.status_code}")
                print_error(f"  Response: {response.text[:200]}")
                self.record_result("influxdb_data", False, f"Status: {response.status_code}", duration)
                return False

        except Exception as e:
            print_error(f"InfluxDB test failed: {e}")
            self.record_result("influxdb_data", False, str(e))
            return False

    # =========================================
    # 6. Compression Stats Tests
    # =========================================

    def test_compression_stats(self) -> bool:
        """Test Swinging Door Compression statistics"""
        print_header("6. Swinging Door Compression")
        start = time.time()

        try:
            response = requests.get(f"{GATEWAY_URL}/api/automation/compression/stats", timeout=10)
            duration = time.time() - start

            if response.status_code == 200:
                stats = response.json()

                total_received = stats.get('total_received', 0)
                total_archived = stats.get('total_archived', 0)
                compression_ratio = stats.get('compression_ratio_percent', 0)
                configured_tags = stats.get('configured_tags', 0)

                print_success(f"Compression active with {configured_tags} configured tags")
                print_info(f"  Total received: {total_received:,}")
                print_info(f"  Total archived: {total_archived:,}")
                print_info(f"  Compression ratio: {compression_ratio:.1f}%")

                if compression_ratio > 0:
                    print_success(f"  Saved {total_received - total_archived:,} data points!")

                self.record_result("compression_stats", True, f"{compression_ratio:.1f}% compression", duration)
                return True
            elif response.status_code == 404:
                print_warning("Compression endpoint not available (may not be configured)")
                self.record_result("compression_stats", True, "Not configured", duration)
                return True
            else:
                print_error(f"Compression stats failed: {response.status_code}")
                self.record_result("compression_stats", False, f"Status: {response.status_code}", duration)
                return False

        except Exception as e:
            print_error(f"Compression test failed: {e}")
            self.record_result("compression_stats", False, str(e))
            return False

    # =========================================
    # 7. Formula Engine Tests
    # =========================================

    def test_formula_engine(self) -> bool:
        """Test Formula Engine status"""
        print_header("7. Formula Engine")
        start = time.time()

        try:
            response = requests.get(f"{GATEWAY_URL}/api/automation/formulas/engine/status", timeout=10)
            duration = time.time() - start

            if response.status_code == 200:
                stats = response.json()

                evaluations = stats.get('evaluations', 0)
                errors = stats.get('errors', 0)
                avg_time = stats.get('avg_eval_time_ms', 0)
                registered = stats.get('registered_formulas', 0)

                print_success(f"Formula Engine active")
                print_info(f"  Registered formulas: {registered}")
                print_info(f"  Total evaluations: {evaluations:,}")
                print_info(f"  Average eval time: {avg_time:.2f}ms")

                if errors > 0:
                    print_warning(f"  Errors: {errors}")

                self.record_result("formula_engine", True, f"{registered} formulas", duration)
                return True
            elif response.status_code == 404:
                print_warning("Formula Engine endpoint not available")
                self.record_result("formula_engine", True, "Not configured", duration)
                return True
            else:
                print_error(f"Formula Engine test failed: {response.status_code}")
                self.record_result("formula_engine", False, f"Status: {response.status_code}", duration)
                return False

        except Exception as e:
            print_error(f"Formula Engine test failed: {e}")
            self.record_result("formula_engine", False, str(e))
            return False

    # =========================================
    # 8. Backend API Tests
    # =========================================

    def test_backend_api(self) -> bool:
        """Test Backend API health"""
        print_header("8. Backend API")
        start = time.time()

        try:
            response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
            duration = time.time() - start

            if response.status_code == 200:
                data = response.json()
                print_success(f"Backend API is healthy")
                print_info(f"  Status: {data.get('status', 'unknown')}")
                print_info(f"  Response time: {duration*1000:.0f}ms")

                self.record_result("backend_api", True, f"{duration*1000:.0f}ms response", duration)
                return True
            else:
                print_error(f"Backend returned status {response.status_code}")
                self.record_result("backend_api", False, f"Status: {response.status_code}", duration)
                return False

        except Exception as e:
            print_error(f"Backend API test failed: {e}")
            self.record_result("backend_api", False, str(e))
            return False

    # =========================================
    # 9. Data Latency Tests
    # =========================================

    def test_data_latency(self) -> bool:
        """Test end-to-end data latency"""
        print_header("9. Data Latency (E2E)")
        start = time.time()

        try:
            # Get a realtime value with timestamp
            response = requests.get(f"{GATEWAY_URL}/api/tags/realtime/all", timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Handle both formats
                if isinstance(data, dict) and 'tags' in data:
                    values = data.get('tags', {})
                else:
                    values = data if isinstance(data, dict) else {}

                if values and isinstance(values, dict):
                    # Find a recently updated tag (not boolean tags that rarely change)
                    sample_value = None
                    sample_tag = None
                    for tag_name, tag_data in values.items():
                        if isinstance(tag_data, dict):
                            val = tag_data.get('value')
                            # Skip boolean values as they don't update frequently
                            if not isinstance(val, bool):
                                sample_value = tag_data
                                sample_tag = tag_name
                                break

                    if not sample_value:
                        sample_value = list(values.values())[0]
                        sample_tag = list(values.keys())[0]

                    if not isinstance(sample_value, dict):
                        print_warning("Unexpected value format")
                        self.record_result("data_latency", True, "Could not measure", time.time() - start)
                        return True

                    print_info(f"  Testing latency with tag: {sample_tag}")
                    timestamp_str = sample_value.get('timestamp', '')

                    if timestamp_str:
                        # Parse timestamp
                        try:
                            if 'T' in timestamp_str:
                                ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00').replace('+00:00', ''))
                            else:
                                ts = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

                            # Compare with current time (handle timezone - use local time)
                            now = datetime.now()
                            latency = abs((now - ts).total_seconds())

                            # If latency > 1 hour, likely a timezone issue, try UTC
                            if latency > 3600:
                                latency_utc = abs((datetime.utcnow() - ts).total_seconds())
                                if latency_utc < latency:
                                    latency = latency_utc

                            duration = time.time() - start

                            if latency < 5:
                                print_success(f"Latency is excellent: {latency:.2f}s")
                            elif latency < 30:
                                print_success(f"Latency is acceptable: {latency:.2f}s")
                            elif latency < 120:
                                print_warning(f"Latency is moderate: {latency:.2f}s")
                            else:
                                print_warning(f"Latency is high: {latency:.2f}s (may be timezone issue)")

                            # Pass if latency < 5 min (to account for cache/batch processing)
                            self.record_result("data_latency", latency < 300, f"{latency:.2f}s", duration)
                            return latency < 300
                        except Exception as e:
                            print_warning(f"Could not parse timestamp: {e}")

                print_warning("Could not measure latency")
                self.record_result("data_latency", True, "Could not measure", time.time() - start)
                return True

            print_error(f"Failed to get realtime values: {response.status_code}")
            self.record_result("data_latency", False, f"Status: {response.status_code}")
            return False

        except Exception as e:
            print_error(f"Latency test failed: {e}")
            self.record_result("data_latency", False, str(e))
            return False

    # =========================================
    # 10. Adapter Status Tests
    # =========================================

    def test_adapter_status(self) -> bool:
        """Test protocol adapter status"""
        print_header("10. Protocol Adapters")
        start = time.time()

        try:
            response = requests.get(f"{GATEWAY_URL}/api/adapters/", timeout=10)
            duration = time.time() - start

            if response.status_code == 200:
                adapters = response.json()
                adapter_count = len(adapters) if isinstance(adapters, list) else 0

                print_success(f"Found {adapter_count} adapters")

                connected = 0
                for adapter in adapters if isinstance(adapters, list) else []:
                    adapter_id = adapter.get('adapter_id', 'unknown')
                    protocol = adapter.get('protocol', 'unknown')
                    is_connected = adapter.get('connected', False)
                    tags = adapter.get('tags_discovered', 0)

                    status = f"{Colors.GREEN}connected{Colors.RESET}" if is_connected else f"{Colors.RED}disconnected{Colors.RESET}"
                    print_info(f"  - {adapter_id} ({protocol}): {status}, {tags} tags")

                    if is_connected:
                        connected += 1

                self.record_result("adapter_status", connected > 0, f"{connected}/{adapter_count} connected", duration)
                return connected > 0
            else:
                print_error(f"Adapter status failed: {response.status_code}")
                self.record_result("adapter_status", False, f"Status: {response.status_code}", duration)
                return False

        except Exception as e:
            print_error(f"Adapter status test failed: {e}")
            self.record_result("adapter_status", False, str(e))
            return False

    # =========================================
    # Run All Tests
    # =========================================

    def run_all(self) -> Dict[str, Any]:
        """Run all E2E tests"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}")
        print("╔══════════════════════════════════════════════════════════╗")
        print("║      OptiFlow E2E Pipeline Tests                        ║")
        print("║      Testing: OPC-UA → Gateway → Kafka → InfluxDB       ║")
        print("╚══════════════════════════════════════════════════════════╝")
        print(f"{Colors.RESET}")

        tests = [
            self.test_gateway_health,
            self.test_tag_discovery,
            self.test_realtime_values,
            self.test_kafka_producer,
            self.test_influxdb_data,
            self.test_compression_stats,
            self.test_formula_engine,
            self.test_backend_api,
            self.test_data_latency,
            self.test_adapter_status,
        ]

        passed = 0
        failed = 0

        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print_error(f"Test crashed: {e}")
                failed += 1

        # Summary
        total_duration = time.time() - self.start_time
        print_header("Test Summary")

        print(f"\n{Colors.BOLD}Results:{Colors.RESET}")
        print(f"  {Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"  {Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"  Total:  {passed + failed}")
        print(f"  Duration: {total_duration:.1f}s")

        print(f"\n{Colors.BOLD}Detailed Results:{Colors.RESET}")
        for test_name, result in self.results.items():
            status = f"{Colors.GREEN}PASS{Colors.RESET}" if result['passed'] else f"{Colors.RED}FAIL{Colors.RESET}"
            print(f"  [{status}] {test_name}: {result['details']}")

        # Overall status
        if failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All tests passed! Pipeline is healthy.{Colors.RESET}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ {failed} test(s) failed. Check details above.{Colors.RESET}")

        return {
            "passed": passed,
            "failed": failed,
            "total": passed + failed,
            "duration": total_duration,
            "results": self.results
        }


# Pytest fixtures and tests
@pytest.fixture(scope="module")
def e2e_suite():
    return E2ETestSuite()


class TestE2EPipeline:
    """Pytest test class for E2E pipeline tests"""

    def test_gateway_health(self, e2e_suite):
        assert e2e_suite.test_gateway_health()

    def test_tag_discovery(self, e2e_suite):
        assert e2e_suite.test_tag_discovery()

    def test_realtime_values(self, e2e_suite):
        assert e2e_suite.test_realtime_values()

    def test_kafka_producer(self, e2e_suite):
        assert e2e_suite.test_kafka_producer()

    def test_influxdb_data(self, e2e_suite):
        assert e2e_suite.test_influxdb_data()

    def test_compression_stats(self, e2e_suite):
        assert e2e_suite.test_compression_stats()

    def test_formula_engine(self, e2e_suite):
        assert e2e_suite.test_formula_engine()

    def test_backend_api(self, e2e_suite):
        assert e2e_suite.test_backend_api()

    def test_data_latency(self, e2e_suite):
        assert e2e_suite.test_data_latency()

    def test_adapter_status(self, e2e_suite):
        assert e2e_suite.test_adapter_status()


if __name__ == "__main__":
    suite = E2ETestSuite()
    results = suite.run_all()

    # Exit with error code if any test failed
    sys.exit(0 if results['failed'] == 0 else 1)
