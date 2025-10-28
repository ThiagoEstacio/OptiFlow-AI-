#!/bin/bash
#
# SmartPort - Run All Tests
# Master script to run complete test suite
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
LOAD_TEST_DIR="$PROJECT_ROOT/load-testing"

# Test results
UNIT_TESTS_PASSED=false
INTEGRATION_TESTS_PASSED=false
SMOKE_TEST_PASSED=false
LOAD_TEST_PASSED=false
FAILOVER_TEST_PASSED=false

log_header() {
    echo ""
    echo "========================================="
    echo "$1"
    echo "========================================="
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

log_skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
}

# Parse arguments
RUN_UNIT=true
RUN_INTEGRATION=true
RUN_SMOKE=true
RUN_LOAD=false  # Optional, takes time
RUN_FAILOVER=false  # Optional, disruptive

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-unit)
            RUN_UNIT=false
            shift
            ;;
        --no-integration)
            RUN_INTEGRATION=false
            shift
            ;;
        --no-smoke)
            RUN_SMOKE=false
            shift
            ;;
        --with-load)
            RUN_LOAD=true
            shift
            ;;
        --with-failover)
            RUN_FAILOVER=true
            shift
            ;;
        --all)
            RUN_UNIT=true
            RUN_INTEGRATION=true
            RUN_SMOKE=true
            RUN_LOAD=true
            RUN_FAILOVER=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--no-unit] [--no-integration] [--no-smoke] [--with-load] [--with-failover] [--all]"
            exit 1
            ;;
    esac
done

log_header "SmartPort Test Suite"
log_info "Starting comprehensive test execution..."
log_info ""
log_info "Test Configuration:"
log_info "  Unit Tests: $RUN_UNIT"
log_info "  Integration Tests: $RUN_INTEGRATION"
log_info "  Smoke Tests: $RUN_SMOKE"
log_info "  Load Tests: $RUN_LOAD"
log_info "  Failover Tests: $RUN_FAILOVER"

# Test 1: Unit Tests
if [ "$RUN_UNIT" = true ]; then
    log_header "1. Unit Tests (pytest)"

    cd "$BACKEND_DIR"

    if command -v pytest &> /dev/null; then
        log_info "Running unit tests..."

        if pytest tests/ -v --tb=short -m "not integration" 2>&1 | tee /tmp/unit-test.log; then
            UNIT_TESTS_PASSED=true
            log_pass "Unit tests PASSED"
        else
            log_fail "Unit tests FAILED"
            log_info "See /tmp/unit-test.log for details"
        fi
    else
        log_skip "pytest not installed, skipping unit tests"
    fi

    cd "$PROJECT_ROOT"
else
    log_skip "Skipping unit tests"
fi

# Test 2: Integration Tests
if [ "$RUN_INTEGRATION" = true ]; then
    log_header "2. Integration Tests (pytest)"

    cd "$BACKEND_DIR"

    if command -v pytest &> /dev/null; then
        log_info "Running integration tests..."

        if pytest tests/integration/ -v --tb=short 2>&1 | tee /tmp/integration-test.log; then
            INTEGRATION_TESTS_PASSED=true
            log_pass "Integration tests PASSED"
        else
            log_fail "Integration tests FAILED"
            log_info "See /tmp/integration-test.log for details"
        fi
    else
        log_skip "pytest not installed, skipping integration tests"
    fi

    cd "$PROJECT_ROOT"
else
    log_skip "Skipping integration tests"
fi

# Test 3: Smoke Test
if [ "$RUN_SMOKE" = true ]; then
    log_header "3. Smoke Tests"

    if [ -f "$SCRIPT_DIR/smoke-test.sh" ]; then
        log_info "Running smoke tests..."

        if bash "$SCRIPT_DIR/smoke-test.sh" 2>&1 | tee /tmp/smoke-test.log; then
            SMOKE_TEST_PASSED=true
            log_pass "Smoke tests PASSED"
        else
            log_fail "Smoke tests FAILED"
            log_info "See /tmp/smoke-test.log for details"
        fi
    else
        log_skip "smoke-test.sh not found"
    fi
else
    log_skip "Skipping smoke tests"
fi

# Test 4: Load Tests
if [ "$RUN_LOAD" = true ]; then
    log_header "4. Load Tests (K6)"

    if command -v k6 &> /dev/null; then
        log_info "Running load tests (this will take ~20 minutes)..."

        cd "$LOAD_TEST_DIR"

        if k6 run load-test.js 2>&1 | tee /tmp/load-test.log; then
            LOAD_TEST_PASSED=true
            log_pass "Load tests PASSED"
        else
            log_fail "Load tests FAILED"
            log_info "See /tmp/load-test.log for details"
        fi

        cd "$PROJECT_ROOT"
    else
        log_skip "K6 not installed, skipping load tests"
        log_info "Install K6: https://k6.io/docs/getting-started/installation"
    fi
else
    log_skip "Skipping load tests (use --with-load to enable)"
fi

# Test 5: Failover Tests
if [ "$RUN_FAILOVER" = true ]; then
    log_header "5. Failover Tests"

    log_info "WARNING: Failover tests will restart services"
    read -p "Continue? (y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "$SCRIPT_DIR/failover-test.sh" ]; then
            log_info "Running failover tests..."

            if bash "$SCRIPT_DIR/failover-test.sh" 2>&1 | tee /tmp/failover-test.log; then
                FAILOVER_TEST_PASSED=true
                log_pass "Failover tests PASSED"
            else
                log_fail "Failover tests FAILED"
                log_info "See /tmp/failover-test.log for details"
            fi
        else
            log_skip "failover-test.sh not found"
        fi
    else
        log_skip "Failover tests cancelled by user"
    fi
else
    log_skip "Skipping failover tests (use --with-failover to enable)"
fi

# Summary
log_header "Test Summary"

echo ""
if [ "$RUN_UNIT" = true ]; then
    if [ "$UNIT_TESTS_PASSED" = true ]; then
        log_pass "Unit Tests: PASSED"
    else
        log_fail "Unit Tests: FAILED"
    fi
fi

if [ "$RUN_INTEGRATION" = true ]; then
    if [ "$INTEGRATION_TESTS_PASSED" = true ]; then
        log_pass "Integration Tests: PASSED"
    else
        log_fail "Integration Tests: FAILED"
    fi
fi

if [ "$RUN_SMOKE" = true ]; then
    if [ "$SMOKE_TEST_PASSED" = true ]; then
        log_pass "Smoke Tests: PASSED"
    else
        log_fail "Smoke Tests: FAILED"
    fi
fi

if [ "$RUN_LOAD" = true ]; then
    if [ "$LOAD_TEST_PASSED" = true ]; then
        log_pass "Load Tests: PASSED"
    else
        log_fail "Load Tests: FAILED"
    fi
fi

if [ "$RUN_FAILOVER" = true ]; then
    if [ "$FAILOVER_TEST_PASSED" = true ]; then
        log_pass "Failover Tests: PASSED"
    else
        log_fail "Failover Tests: FAILED"
    fi
fi

echo ""
log_info "Test logs saved in /tmp/"
log_info "  - /tmp/unit-test.log"
log_info "  - /tmp/integration-test.log"
log_info "  - /tmp/smoke-test.log"
log_info "  - /tmp/load-test.log"
log_info "  - /tmp/failover-test.log"

# Exit code
ALL_PASSED=true

if [ "$RUN_UNIT" = true ] && [ "$UNIT_TESTS_PASSED" = false ]; then
    ALL_PASSED=false
fi
if [ "$RUN_INTEGRATION" = true ] && [ "$INTEGRATION_TESTS_PASSED" = false ]; then
    ALL_PASSED=false
fi
if [ "$RUN_SMOKE" = true ] && [ "$SMOKE_TEST_PASSED" = false ]; then
    ALL_PASSED=false
fi
if [ "$RUN_LOAD" = true ] && [ "$LOAD_TEST_PASSED" = false ]; then
    ALL_PASSED=false
fi
if [ "$RUN_FAILOVER" = true ] && [ "$FAILOVER_TEST_PASSED" = false ]; then
    ALL_PASSED=false
fi

echo ""
if [ "$ALL_PASSED" = true ]; then
    log_pass "ALL TESTS PASSED ✓"
    exit 0
else
    log_fail "SOME TESTS FAILED ✗"
    exit 1
fi
