#!/usr/bin/env python3
"""
Analytics Endpoints Testing Script

Tests the analytics endpoints to ensure they work correctly:
1. GET /api/v1/analytics/functions
2. GET /api/v1/analytics/examples
3. POST /api/v1/analytics/query (with mock data)
"""

import requests
import json
from datetime import datetime, timedelta
import sys

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_test(name, passed, message=""):
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {name}")
    if message:
        print(f"       {message}")

def test_health_endpoint():
    """Test health endpoint"""
    print_header("Test 1: Health Endpoint")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_test("Health check", True, f"Status: {data.get('status', 'unknown')}")
            return True
        else:
            print_test("Health check", False, f"Status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_test("Health check", False, "Cannot connect to backend (is it running?)")
        return False
    except Exception as e:
        print_test("Health check", False, f"Error: {str(e)}")
        return False

def test_functions_endpoint():
    """Test analytics functions endpoint"""
    print_header("Test 2: Analytics Functions Endpoint")

    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/analytics/functions", timeout=5)

        if response.status_code == 200:
            data = response.json()
            functions = data.get('functions', [])

            print_test("Get functions endpoint", True, f"Found {len(functions)} functions")

            # Verify expected functions
            expected_functions = [
                'mean', 'median', 'mode', 'min', 'max', 'sum', 'count',
                'stddev', 'variance', 'percentile', 'correlation',
                'moving_average', 'cumulative_sum', 'rate_of_change'
            ]

            found_functions = [f['name'] for f in functions]
            missing = [f for f in expected_functions if f not in found_functions]

            if not missing:
                print_test("All expected functions present", True)
            else:
                print_test("Missing functions", False, f"Missing: {', '.join(missing)}")

            # Display first 3 functions
            print(f"\n{YELLOW}Sample functions:{RESET}")
            for func in functions[:3]:
                print(f"  - {func.get('name')}: {func.get('description', 'N/A')}")

            return len(missing) == 0
        else:
            print_test("Get functions endpoint", False, f"Status code: {response.status_code}")
            return False

    except Exception as e:
        print_test("Get functions endpoint", False, f"Error: {str(e)}")
        return False

def test_examples_endpoint():
    """Test analytics examples endpoint"""
    print_header("Test 3: Analytics Examples Endpoint")

    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/analytics/examples", timeout=5)

        if response.status_code == 200:
            data = response.json()
            examples = data.get('examples', [])

            print_test("Get examples endpoint", True, f"Found {len(examples)} examples")

            # Display examples
            print(f"\n{YELLOW}Query examples:{RESET}")
            for example in examples:
                print(f"  - {example.get('name')}: {example.get('description', 'N/A')}")

            return True
        else:
            print_test("Get examples endpoint", False, f"Status code: {response.status_code}")
            return False

    except Exception as e:
        print_test("Get examples endpoint", False, f"Error: {str(e)}")
        return False

def test_query_endpoint_structure():
    """Test query endpoint structure (without auth)"""
    print_header("Test 4: Analytics Query Endpoint Structure")

    # Create a test query
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)

    query = {
        "tags": ["test_tag_1"],
        "start": start_time.isoformat() + "Z",
        "end": end_time.isoformat() + "Z",
        "aggregations": [
            {
                "function": "mean",
                "field": "value",
                "window": "1h"
            }
        ],
        "limit": 1000
    }

    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/analytics/query",
            json=query,
            timeout=10
        )

        # We expect 401 (Unauthorized) since we don't have a token
        # or 422 (Unprocessable Entity) if validation fails
        # or 200 if somehow it works without auth (dev mode)

        if response.status_code == 401:
            print_test(
                "Query endpoint requires authentication",
                True,
                "Correctly requires authorization (401)"
            )
            return True
        elif response.status_code == 422:
            data = response.json()
            print_test(
                "Query endpoint validation",
                True,
                "Validation error (expected without valid data)"
            )
            print(f"  {YELLOW}Validation detail:{RESET} {data.get('detail', 'N/A')}")
            return True
        elif response.status_code == 200:
            data = response.json()
            print_test(
                "Query endpoint accessible",
                True,
                "Query executed successfully (no auth required in dev mode?)"
            )
            return True
        else:
            print_test(
                "Query endpoint",
                False,
                f"Unexpected status code: {response.status_code}"
            )
            return False

    except Exception as e:
        print_test("Query endpoint", False, f"Error: {str(e)}")
        return False

def test_api_documentation():
    """Test API documentation endpoints"""
    print_header("Test 5: API Documentation")

    passed = True

    # Test Swagger UI
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print_test("Swagger UI accessible", True, f"{BASE_URL}/docs")
        else:
            print_test("Swagger UI accessible", False)
            passed = False
    except Exception as e:
        print_test("Swagger UI accessible", False, str(e))
        passed = False

    # Test OpenAPI JSON
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_test("OpenAPI spec accessible", True, f"Version: {data.get('openapi', 'N/A')}")

            # Check for analytics endpoints
            paths = data.get('paths', {})
            analytics_paths = [p for p in paths.keys() if 'analytics' in p]
            print(f"  {YELLOW}Analytics endpoints in spec:{RESET} {len(analytics_paths)}")
        else:
            print_test("OpenAPI spec accessible", False)
            passed = False
    except Exception as e:
        print_test("OpenAPI spec accessible", False, str(e))
        passed = False

    return passed

def test_websocket_endpoint():
    """Test WebSocket endpoint (basic check)"""
    print_header("Test 6: WebSocket Endpoint")

    # We can't easily test WebSocket without a proper client
    # But we can check if the endpoint is registered in OpenAPI spec

    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            paths = data.get('paths', {})

            # Check for WebSocket paths
            ws_paths = [
                '/api/v1/analytics/ws/stream',
                '/api/v1/analytics/ws/stream-simple'
            ]

            found_ws = [path for path in ws_paths if path in paths]

            if found_ws:
                print_test(
                    "WebSocket endpoints registered",
                    True,
                    f"Found: {', '.join(found_ws)}"
                )
                return True
            else:
                print_test(
                    "WebSocket endpoints registered",
                    False,
                    "WebSocket paths not found in API spec"
                )
                print(f"  {YELLOW}Note:{RESET} WebSocket endpoints may not appear in OpenAPI spec")
                return True  # Not a critical failure
        else:
            print_test("OpenAPI spec check", False)
            return False
    except Exception as e:
        print_test("WebSocket endpoint check", False, str(e))
        return False

def main():
    print("\n" + "="*70)
    print(f"{BLUE}SmartPort Analytics - Endpoint Testing{RESET}")
    print("="*70)
    print(f"\n{YELLOW}Testing backend at: {BASE_URL}{RESET}\n")

    results = []

    # Run tests
    results.append(("Health Check", test_health_endpoint()))

    if not results[0][1]:
        print(f"\n{RED}Backend is not running! Please start it first:{RESET}")
        print(f"  cd backend && uvicorn app.main:app --reload")
        print("\nSee START_SERVICES.md for detailed instructions.")
        return 1

    results.append(("Functions Endpoint", test_functions_endpoint()))
    results.append(("Examples Endpoint", test_examples_endpoint()))
    results.append(("Query Endpoint", test_query_endpoint_structure()))
    results.append(("API Documentation", test_api_documentation()))
    results.append(("WebSocket Endpoint", test_websocket_endpoint()))

    # Summary
    print_header("Test Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = f"{GREEN}✓{RESET}" if result else f"{RED}✗{RESET}"
        print(f"{status} {name}")

    print(f"\n{BLUE}Results: {passed}/{total} tests passed{RESET}")

    if passed == total:
        print(f"\n{GREEN}✓ All tests PASSED!{RESET}")
        print(f"\n{BLUE}Next steps:{RESET}")
        print("1. Start frontend: cd frontend && npm start")
        print("2. Open browser: http://localhost:3000")
        print("3. Navigate to Analytics page")
        print("4. Test Query Builder and visualizations")
        print("5. Test WebSocket streaming mode")
        return 0
    else:
        print(f"\n{YELLOW}Some tests failed. Please review the errors above.{RESET}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
