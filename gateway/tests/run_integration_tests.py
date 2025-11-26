#!/usr/bin/env python3
"""
OptiFlow Gateway - Automated Integration Tests
Comprehensive test suite for all Gateway endpoints
Run against a live gateway instance
"""
import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Configuration
BASE_URL = "http://localhost:8080"
TIMEOUT = 10

# Test results tracking
results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "errors": []
}


def log(message: str, level: str = "INFO"):
    """Print formatted log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    symbols = {"INFO": "ℹ️", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "TEST": "🧪"}
    print(f"[{timestamp}] {symbols.get(level, '•')} {message}")


def test(name: str, condition: bool, details: str = ""):
    """Record test result"""
    if condition:
        results["passed"] += 1
        log(f"{name}: PASSED", "PASS")
    else:
        results["failed"] += 1
        results["errors"].append(f"{name}: {details}")
        log(f"{name}: FAILED - {details}", "FAIL")
    return condition


def api_get(endpoint: str) -> Tuple[int, Any]:
    """Make GET request"""
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=TIMEOUT)
        return response.status_code, response.json() if response.text else None
    except Exception as e:
        return 0, {"error": str(e)}


def api_post(endpoint: str, data: dict) -> Tuple[int, Any]:
    """Make POST request"""
    try:
        response = requests.post(
            f"{BASE_URL}{endpoint}",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        return response.status_code, response.json() if response.text else None
    except Exception as e:
        return 0, {"error": str(e)}


def api_delete(endpoint: str) -> Tuple[int, Any]:
    """Make DELETE request"""
    try:
        response = requests.delete(f"{BASE_URL}{endpoint}", timeout=TIMEOUT)
        return response.status_code, response.json() if response.text else None
    except Exception as e:
        return 0, {"error": str(e)}


# ==================== HEALTH & STATUS TESTS ====================

def test_health_endpoints():
    """Test health and status endpoints"""
    log("Testing Health & Status Endpoints", "TEST")

    # Health check
    status, data = api_get("/health")
    test("GET /health returns 200", status == 200, f"Status: {status}")
    if status == 200:
        test("Health status is healthy", data.get("status") == "healthy", f"Got: {data}")

    # OpenAPI docs
    status, data = api_get("/openapi.json")
    test("GET /openapi.json returns 200", status == 200, f"Status: {status}")
    if status == 200:
        test("OpenAPI has paths", "paths" in data, "Missing paths in OpenAPI spec")


# ==================== ADAPTER TESTS ====================

def test_adapter_endpoints():
    """Test adapter management endpoints"""
    log("Testing Adapter Endpoints", "TEST")

    # List adapters
    status, data = api_get("/api/adapters/")
    test("GET /api/adapters/ returns 200", status == 200, f"Status: {status}")
    if status == 200:
        test("Adapters is a list", isinstance(data, list), f"Got: {type(data)}")
        if len(data) > 0:
            adapter = data[0]
            test("Adapter has adapter_id", "adapter_id" in adapter, "Missing adapter_id")

            # Get specific adapter status
            adapter_id = adapter.get("adapter_id")
            if adapter_id:
                status2, data2 = api_get(f"/api/tags/adapter/{adapter_id}/status")
                test(f"GET /api/tags/adapter/{adapter_id}/status returns 200", status2 == 200, f"Status: {status2}")


# ==================== TAGS REALTIME TESTS ====================

def test_tags_realtime_endpoints():
    """Test real-time tag endpoints"""
    log("Testing Tags Realtime Endpoints", "TEST")

    # Get all realtime values
    status, data = api_get("/api/tags/realtime/all")
    test("GET /api/tags/realtime/all returns 200", status == 200, f"Status: {status}")
    if status == 200:
        test("Response has count", "count" in data, "Missing count")
        test("Response has adapters", "adapters" in data, "Missing adapters")
        test("Response has tags", "tags" in data, "Missing tags")
        test("Response has latency_ms", "latency_ms" in data, "Missing latency_ms")

        # Test single tag if we have any
        if data.get("tags"):
            tag_name = list(data["tags"].keys())[0]
            status2, data2 = api_get(f"/api/tags/realtime/{tag_name}")
            test(f"GET /api/tags/realtime/{tag_name} returns 200", status2 == 200, f"Status: {status2}")
            if status2 == 200:
                test("Single tag has value", "value" in data2, "Missing value")
                test("Single tag has quality", "quality" in data2, "Missing quality")
                test("Single tag has timestamp", "timestamp" in data2, "Missing timestamp")

    # Test batch endpoint
    status, data = api_post("/api/tags/realtime/batch", ["temp_c", "power_kw"])
    test("POST /api/tags/realtime/batch returns 200", status == 200, f"Status: {status}")
    if status == 200:
        test("Batch response has count", "count" in data, "Missing count")
        test("Batch response has tags", "tags" in data, "Missing tags")


# ==================== TAGS LIST TESTS ====================

def test_tags_list_endpoints():
    """Test tag listing endpoints"""
    log("Testing Tags List Endpoints", "TEST")

    # List all tags
    status, data = api_get("/api/tags/list")
    test("GET /api/tags/list returns 200", status == 200, f"Status: {status}")
    if status == 200:
        test("Response has count", "count" in data, "Missing count")
        test("Response has tags", "tags" in data, "Missing tags")
        test("Tags is a list", isinstance(data.get("tags"), list), f"Got: {type(data.get('tags'))}")

        if data.get("tags"):
            tag = data["tags"][0]
            test("Tag has name", "name" in tag, "Missing name")
            test("Tag has address", "address" in tag, "Missing address")
            test("Tag has adapter_id", "adapter_id" in tag, "Missing adapter_id")

    # Search tags
    status, data = api_get("/api/tags/search/temp")
    test("GET /api/tags/search/temp returns 200", status == 200, f"Status: {status}")
    if status == 200:
        test("Search response has count", "count" in data, "Missing count")
        test("Search response has tags", "tags" in data, "Missing tags")


# ==================== TAG MANAGER TESTS ====================

def test_tag_manager_endpoints():
    """Test tag manager endpoints"""
    log("Testing Tag Manager Endpoints", "TEST")

    # List managed tags
    status, data = api_get("/api/tags/")
    test("GET /api/tags/ returns 200", status == 200, f"Status: {status}")
    if status == 200:
        test("Managed tags is a list", isinstance(data, list), f"Got: {type(data)}")

        # If we have managed tags, test getting one
        if len(data) > 0:
            tag_id = data[0].get("tag_id")
            if tag_id:
                status2, data2 = api_get(f"/api/tags/{tag_id}")
                test(f"GET /api/tags/{tag_id} returns 200", status2 == 200, f"Status: {status2}")


# ==================== AUTOMATION TESTS ====================

def test_automation_endpoints():
    """Test automation endpoints (formulas, alarms, events, actions)"""
    log("Testing Automation Endpoints", "TEST")

    # Formula examples
    status, data = api_get("/api/automation/formulas/examples")
    test("GET /api/automation/formulas/examples returns 200", status == 200, f"Status: {status}")
    if status == 200:
        test("Has temperature_conversion example", "temperature_conversion" in data, "Missing example")

    # Test formula
    status, data = api_post("/api/automation/formulas/test", {
        "expression": "tags['TEMP'] * 1.8 + 32",
        "sample_values": {"TEMP": 100}
    })
    test("POST /api/automation/formulas/test returns 200", status == 200, f"Status: {status}")
    if status == 200:
        test("Formula test success", data.get("success") == True, f"Got: {data}")
        test("Formula result is 212", data.get("result") == 212, f"Got: {data.get('result')}")

    # Automation statistics
    status, data = api_get("/api/automation/automation/statistics")
    test("GET /api/automation/automation/statistics returns 200", status == 200, f"Status: {status}")
    if status == 200:
        test("Stats has total_tags", "total_tags" in data, "Missing total_tags")
        test("Stats has automation", "automation" in data, "Missing automation")
        test("Stats has coverage", "coverage" in data, "Missing coverage")


def test_automation_crud():
    """Test CRUD operations for automation (alarm, event, action)"""
    log("Testing Automation CRUD Operations", "TEST")

    # First, get a managed tag to work with
    status, tags = api_get("/api/tags/")

    tag_id = None
    created_tag = False

    if status == 200 and tags and len(tags) > 0:
        tag_id = tags[0].get("tag_id")

    # If no managed tags, create one for testing
    if not tag_id:
        log("No managed tags found, creating test tag...", "INFO")
        # Get first adapter to associate tag with
        status_adp, adapters = api_get("/api/adapters/")
        if status_adp == 200 and adapters:
            adapter_id = adapters[0].get("adapter_id")
            test_tag_data = {
                "tag_name": "TEST_TAG_AUTOMATION",
                "adapter_id": adapter_id,
                "address": "ns=2;i=9999",
                "data_type": "double",
                "engineering_units": "test"
            }
            status_create, data_create = api_post("/api/tags/", test_tag_data)
            if status_create == 200 and data_create:
                tag_id = data_create.get("tag_id")
                created_tag = True
                log(f"Created test tag: {tag_id}", "INFO")

    if not tag_id:
        log("Could not get or create tag for CRUD tests, skipping", "WARN")
        results["skipped"] += 9
        return

    # === TEST ALARM CRUD ===
    log(f"Testing Alarm CRUD on tag {tag_id}", "INFO")

    # Create alarm
    alarm_data = {
        "tag_id": tag_id,
        "alarm_type": "limit",
        "priority": "high",
        "high_limit": 80,
        "low_limit": 20
    }
    status, data = api_post(f"/api/automation/tags/{tag_id}/alarms/advanced", alarm_data)
    test("POST alarm returns 200", status == 200, f"Status: {status}, Data: {data}")

    alarm_id = None
    if status == 200 and data.get("success"):
        alarm_id = data.get("alarm_id")
        test("Alarm created with ID", alarm_id is not None, "No alarm_id returned")

    # List alarms
    status, data = api_get(f"/api/automation/tags/{tag_id}/alarms")
    test("GET alarms returns 200", status == 200, f"Status: {status}")
    if status == 200:
        test("Has advanced_alarms", "advanced_alarms" in data, "Missing advanced_alarms")

    # Delete alarm
    if alarm_id:
        status, data = api_delete(f"/api/automation/tags/{tag_id}/alarms/{alarm_id}")
        test("DELETE alarm returns 200", status == 200, f"Status: {status}")

    # === TEST EVENT CRUD ===
    log(f"Testing Event CRUD on tag {tag_id}", "INFO")

    # Create event
    event_data = {
        "tag_id": tag_id,
        "event_type": "value_change",
        "condition": "value > 50",
        "min_interval_seconds": 60
    }
    status, data = api_post(f"/api/automation/tags/{tag_id}/events", event_data)
    test("POST event returns 200", status == 200, f"Status: {status}, Data: {data}")

    trigger_id = None
    if status == 200 and data.get("success"):
        trigger_id = data.get("trigger_id")
        test("Event created with ID", trigger_id is not None, "No trigger_id returned")

    # List events
    status, data = api_get(f"/api/automation/tags/{tag_id}/events")
    test("GET events returns 200", status == 200, f"Status: {status}")
    if status == 200:
        test("Has event_triggers", "event_triggers" in data, "Missing event_triggers")

    # Delete event
    if trigger_id:
        status, data = api_delete(f"/api/automation/tags/{tag_id}/events/{trigger_id}")
        test("DELETE event returns 200", status == 200, f"Status: {status}")

    # === TEST ACTION CRUD ===
    log(f"Testing Action CRUD on tag {tag_id}", "INFO")

    # Create action
    action_data = {
        "tag_id": tag_id,
        "action_type": "log_message",
        "log_level": "INFO",
        "log_message_template": "Test: {tag_name} = {value}"
    }
    status, data = api_post(f"/api/automation/tags/{tag_id}/actions", action_data)
    test("POST action returns 200", status == 200, f"Status: {status}, Data: {data}")

    action_id = None
    if status == 200 and data.get("success"):
        action_id = data.get("action_id")
        test("Action created with ID", action_id is not None, "No action_id returned")

    # List actions
    status, data = api_get(f"/api/automation/tags/{tag_id}/actions")
    test("GET actions returns 200", status == 200, f"Status: {status}")
    if status == 200:
        test("Has actions", "actions" in data, "Missing actions")

    # Delete action
    if action_id:
        status, data = api_delete(f"/api/automation/tags/{tag_id}/actions/{action_id}")
        test("DELETE action returns 200", status == 200, f"Status: {status}")


# ==================== METRICS TESTS ====================

def test_metrics_endpoints():
    """Test metrics and monitoring endpoints"""
    log("Testing Metrics Endpoints", "TEST")

    # Prometheus metrics
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=TIMEOUT)
        test("GET /metrics returns 200", response.status_code == 200, f"Status: {response.status_code}")
        if response.status_code == 200:
            test("Metrics contains gateway info", "gateway" in response.text.lower() or "optiflow" in response.text.lower() or "python" in response.text.lower(), "No gateway metrics found")
    except Exception as e:
        test("GET /metrics accessible", False, str(e))


# ==================== WEBSOCKET TESTS ====================

def test_websocket_info():
    """Test WebSocket info endpoint (not actual WebSocket connection)"""
    log("Testing WebSocket Info", "TEST")

    # Check if WebSocket endpoints are documented
    status, data = api_get("/openapi.json")
    if status == 200:
        paths = data.get("paths", {})
        ws_paths = [p for p in paths.keys() if "ws" in p.lower()]
        test("WebSocket paths documented", len(ws_paths) > 0, f"Found: {ws_paths}")


# ==================== ERROR HANDLING TESTS ====================

def test_error_handling():
    """Test error handling for invalid requests"""
    log("Testing Error Handling", "TEST")

    # Non-existent tag
    status, data = api_get("/api/tags/realtime/nonexistent_tag_12345")
    test("Non-existent tag returns 404", status == 404, f"Status: {status}")

    # Non-existent adapter
    status, data = api_get("/api/tags/adapter/nonexistent_adapter/status")
    test("Non-existent adapter returns 404", status == 404, f"Status: {status}")

    # Invalid endpoint
    status, data = api_get("/api/invalid/endpoint")
    test("Invalid endpoint returns 404", status == 404, f"Status: {status}")


# ==================== PERFORMANCE TESTS ====================

def test_performance():
    """Test response times"""
    log("Testing Performance", "TEST")

    # Realtime all - should be fast
    start = time.time()
    status, data = api_get("/api/tags/realtime/all")
    elapsed = (time.time() - start) * 1000
    test("GET /api/tags/realtime/all < 100ms", elapsed < 100, f"Took {elapsed:.2f}ms")

    # Tag list
    start = time.time()
    status, data = api_get("/api/tags/list")
    elapsed = (time.time() - start) * 1000
    test("GET /api/tags/list < 200ms", elapsed < 200, f"Took {elapsed:.2f}ms")

    # Health check
    start = time.time()
    status, data = api_get("/health")
    elapsed = (time.time() - start) * 1000
    test("GET /health < 50ms", elapsed < 50, f"Took {elapsed:.2f}ms")


# ==================== MAIN ====================

def run_all_tests():
    """Run all test suites"""
    print("\n" + "=" * 60)
    print("🧪 OptiFlow Gateway - Automated Integration Tests")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    # Check if gateway is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Gateway is not healthy!")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to gateway: {e}")
        sys.exit(1)

    log("Gateway is healthy, starting tests...\n", "PASS")

    # Run test suites
    test_health_endpoints()
    print()

    test_adapter_endpoints()
    print()

    test_tags_realtime_endpoints()
    print()

    test_tags_list_endpoints()
    print()

    test_tag_manager_endpoints()
    print()

    test_automation_endpoints()
    print()

    test_automation_crud()
    print()

    test_metrics_endpoints()
    print()

    test_websocket_info()
    print()

    test_error_handling()
    print()

    test_performance()
    print()

    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    total = results["passed"] + results["failed"] + results["skipped"]
    print(f"✅ Passed:  {results['passed']}")
    print(f"❌ Failed:  {results['failed']}")
    print(f"⏭️  Skipped: {results['skipped']}")
    print(f"📝 Total:   {total}")
    print("-" * 60)

    if results["failed"] > 0:
        print("\n❌ FAILED TESTS:")
        for error in results["errors"]:
            print(f"   • {error}")

    success_rate = (results["passed"] / total * 100) if total > 0 else 0
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    print("=" * 60)

    # Exit code
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    run_all_tests()
