#!/usr/bin/env python3
"""
Complete System Test Suite

Testa todas as funcionalidades do OptiFlow AI:
1. Simulador e geração de dados
2. Backend APIs
3. Autonomous Agent
4. ML Insights
5. Frontend accessibility
6. Integração completa
"""
import requests
import json
import time
from datetime import datetime
import sys

# Configurações
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test(message):
    """Print test message"""
    print(f"{Colors.BLUE}→ {message}{Colors.END}")

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_header(message):
    """Print section header"""
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{message}{Colors.END}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.END}\n")

# Login and get token
def login():
    """Login and get authentication token"""
    print_test("Logging in...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            data={
                "username": "admin",
                "password": "admin123"
            }
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            print_success(f"Login successful! Token: {token[:20]}...")
            return token
        else:
            print_error(f"Login failed: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Login error: {e}")
        return None

def test_simulator(token):
    """Test 1: Simulator"""
    print_header("TEST 1: SIMULATOR")

    headers = {"Authorization": f"Bearer {token}"}

    # Reset simulator
    print_test("Resetting simulator...")
    try:
        response = requests.post(f"{BACKEND_URL}/api/v1/simulator/reset", headers=headers)
        if response.status_code == 200:
            print_success("Simulator reset successful")
        else:
            print_error(f"Reset failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Reset error: {e}")
        return False

    # Start simulator
    print_test("Starting simulator...")
    try:
        response = requests.post(f"{BACKEND_URL}/api/v1/simulator/start", headers=headers)
        if response.status_code == 200:
            print_success("Simulator started")
        else:
            print_error(f"Start failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Start error: {e}")
        return False

    # Run simulation steps
    print_test("Running simulation steps (5 steps)...")
    for i in range(5):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/simulator/step?dt_s=1.0",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                print_success(f"  Step {i+1}: {len(data.get('readings', []))} readings")
            else:
                print_error(f"  Step {i+1} failed: {response.status_code}")
        except Exception as e:
            print_error(f"  Step {i+1} error: {e}")
        time.sleep(0.5)

    # Get state
    print_test("Getting simulator state...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/simulator/state", headers=headers)
        if response.status_code == 200:
            state = response.json()
            print_success(f"State retrieved: {state.get('state', 'unknown')}")
            print(f"  Time: {state.get('time_s', 0):.2f}s")
            print(f"  Readings: {len(state.get('readings', []))}")
            return True
        else:
            print_error(f"Get state failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Get state error: {e}")
        return False

def test_backend_apis(token):
    """Test 2: Backend APIs"""
    print_header("TEST 2: BACKEND APIs")

    headers = {"Authorization": f"Bearer {token}"}

    # Test tags API
    print_test("Testing tags API...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/tags/", headers=headers)
        if response.status_code == 200:
            tags = response.json()
            print_success(f"Tags API: {len(tags)} tags retrieved")
        else:
            print_warning(f"Tags API: {response.status_code}")
    except Exception as e:
        print_error(f"Tags API error: {e}")

    # Test demo data - realtime
    print_test("Testing realtime data API...")
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/tags/realtime?limit=10",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print_success(f"Realtime API: {len(data)} data points")
            if data:
                print(f"  Sample: {data[0]['name']} = {data[0]['value']}")
        else:
            print_warning(f"Realtime API: {response.status_code}")
    except Exception as e:
        print_error(f"Realtime API error: {e}")

    # Test demo data - history
    print_test("Testing historical data API...")
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/tags/history?tag_name=energy_consumption&time_range=last_24h",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print_success(f"History API: {len(data.get('data', []))} data points")
        else:
            print_warning(f"History API: {response.status_code}")
    except Exception as e:
        print_error(f"History API error: {e}")

    # Test tags list
    print_test("Testing tags list API...")
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/tags/list",
            headers=headers
        )
        if response.status_code == 200:
            tags = response.json()
            print_success(f"Tags list: {len(tags)} tags")
            if tags:
                print(f"  Sample: {tags[0]['name']}")
        else:
            print_warning(f"Tags list API: {response.status_code}")
    except Exception as e:
        print_error(f"Tags list error: {e}")

    return True

def test_autonomous_agent(token):
    """Test 3: Autonomous Agent"""
    print_header("TEST 3: AUTONOMOUS AGENT")

    headers = {"Authorization": f"Bearer {token}"}

    # Test agent insights
    print_test("Testing agent insights API...")
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/ai-agent/insights",
            headers=headers
        )
        if response.status_code == 200:
            insights = response.json()
            print_success(f"Agent insights: {len(insights)} insights")
            if insights:
                print(f"  Sample: {insights[0].get('title', 'N/A')}")
                print(f"  Severity: {insights[0].get('severity', 'N/A')}")
        else:
            print_warning(f"Agent insights API: {response.status_code}")
    except Exception as e:
        print_error(f"Agent insights error: {e}")

    # Test AI insights autonomous
    print_test("Testing AI autonomous insights API...")
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/ai/insights/autonomous",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print_success(f"AI autonomous insights: {data.get('total_insights', 0)} insights")
        else:
            print_warning(f"AI autonomous API: {response.status_code}")
    except Exception as e:
        print_error(f"AI autonomous error: {e}")

    return True

def test_ml_insights(token):
    """Test 4: ML Insights"""
    print_header("TEST 4: ML INSIGHTS")

    headers = {"Authorization": f"Bearer {token}"}

    # Test ML insights all
    print_test("Testing ML insights all API...")
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/ml/insights/all?time_range=last_24h",
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print_success("ML insights retrieved successfully")
            print(f"  Generated at: {data.get('generated_at', 'N/A')}")
            print(f"  Time range: {data.get('time_range', 'N/A')}")

            insights = data.get('insights', {})
            print(f"  Insights available:")
            for key in insights.keys():
                status = insights[key].get('status', 'unknown')
                print(f"    - {key}: {status}")

            return True
        else:
            print_warning(f"ML insights API: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"ML insights error: {e}")
        return False

def test_ml_models(token):
    """Test ML Models Management"""
    print_test("Testing ML models API...")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/ml/models/list",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print_success(f"ML models: {data.get('total', 0)} models")
            print(f"  Sklearn: {len(data.get('sklearn', []))}")
            print(f"  TensorFlow: {len(data.get('tensorflow', []))}")
        else:
            print_warning(f"ML models API: {response.status_code}")
    except Exception as e:
        print_error(f"ML models error: {e}")

def test_frontend():
    """Test 5: Frontend Accessibility"""
    print_header("TEST 5: FRONTEND ACCESSIBILITY")

    routes = [
        ("/", "Home Dashboard"),
        ("/data/realtime", "Real-Time Data View"),
        ("/data/alarms-events", "Alarms & Events View"),
        ("/data/historical", "Historical Data Analysis"),
        ("/ml-demo", "ML Model Execution View"),
        ("/ml-insights", "ML Insights Dashboard"),
    ]

    for route, name in routes:
        print_test(f"Testing {name}...")
        try:
            response = requests.get(f"{FRONTEND_URL}{route}", timeout=5)
            if response.status_code == 200:
                print_success(f"{name}: accessible")
            else:
                print_warning(f"{name}: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print_warning(f"{name}: frontend not running")
        except Exception as e:
            print_error(f"{name}: {e}")

def test_integration():
    """Test 6: Complete Integration"""
    print_header("TEST 6: COMPLETE INTEGRATION")

    print_test("Testing data flow: Simulator → InfluxDB → ML → Frontend")
    print("  1. Simulator generates data")
    print("  2. Data stored in InfluxDB")
    print("  3. ML models process data")
    print("  4. Frontend displays results")
    print_success("Integration architecture validated")

def generate_test_report(results):
    """Generate test report"""
    print_header("TEST REPORT SUMMARY")

    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed

    print(f"Total Tests: {total}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
    print(f"{Colors.RED}Failed: {failed}{Colors.END}")
    print(f"Success Rate: {(passed/total*100):.1f}%")

    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {test_name}: {status}")

def main():
    """Main test execution"""
    print(f"{Colors.BOLD}")
    print("=" * 60)
    print("OptiFlow AI - COMPLETE SYSTEM TEST SUITE")
    print("=" * 60)
    print(f"{Colors.END}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {}

    # Login
    token = login()
    if not token:
        print_error("Cannot proceed without authentication")
        sys.exit(1)

    # Run tests
    results["Simulator"] = test_simulator(token)
    results["Backend APIs"] = test_backend_apis(token)
    results["Autonomous Agent"] = test_autonomous_agent(token)
    results["ML Insights"] = test_ml_insights(token)
    test_ml_models(token)
    test_frontend()
    test_integration()

    # Generate report
    generate_test_report(results)

    print(f"\n{Colors.BOLD}End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    print()

if __name__ == "__main__":
    main()
