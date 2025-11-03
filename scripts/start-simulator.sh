#!/bin/bash
# Start SmartPort Bulk Terminal Simulator
# This script manages the simulator lifecycle

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SIMULATOR_PATH="$PROJECT_ROOT/simulators/smartport_bulk_terminal_simulator.py"
PID_FILE="$PROJECT_ROOT/tmp/simulator.pid"
LOG_FILE="$PROJECT_ROOT/logs/simulator.log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create necessary directories
mkdir -p "$(dirname "$PID_FILE")"
mkdir -p "$(dirname "$LOG_FILE")"

# Function to check if simulator is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Function to start simulator
start_simulator() {
    echo -e "${BLUE}Starting SmartPort Bulk Terminal Simulator...${NC}"

    if is_running; then
        echo -e "${YELLOW}Simulator is already running (PID: $(cat "$PID_FILE"))${NC}"
        return 0
    fi

    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is not installed${NC}"
        exit 1
    fi

    # Check if simulator file exists
    if [ ! -f "$SIMULATOR_PATH" ]; then
        echo -e "${RED}Error: Simulator not found at $SIMULATOR_PATH${NC}"
        exit 1
    fi

    # Start simulator in background
    cd "$PROJECT_ROOT/simulators"
    nohup python3 smartport_bulk_terminal_simulator.py > "$LOG_FILE" 2>&1 &
    local pid=$!

    # Save PID
    echo $pid > "$PID_FILE"

    # Wait a bit and check if it's still running
    sleep 2
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Simulator started successfully (PID: $pid)${NC}"
        echo -e "${BLUE}📋 Log file: $LOG_FILE${NC}"
        return 0
    else
        echo -e "${RED}❌ Simulator failed to start${NC}"
        echo -e "${YELLOW}Check log file: $LOG_FILE${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to stop simulator
stop_simulator() {
    echo -e "${BLUE}Stopping SmartPort Bulk Terminal Simulator...${NC}"

    if ! is_running; then
        echo -e "${YELLOW}Simulator is not running${NC}"
        rm -f "$PID_FILE"
        return 0
    fi

    local pid=$(cat "$PID_FILE")
    echo -e "${YELLOW}Stopping simulator (PID: $pid)...${NC}"

    # Try graceful shutdown first
    kill $pid 2>/dev/null

    # Wait up to 5 seconds for graceful shutdown
    for i in {1..5}; do
        if ! ps -p $pid > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Simulator stopped successfully${NC}"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done

    # Force kill if still running
    echo -e "${YELLOW}Force stopping simulator...${NC}"
    kill -9 $pid 2>/dev/null
    rm -f "$PID_FILE"
    echo -e "${GREEN}✅ Simulator stopped (forced)${NC}"
}

# Function to restart simulator
restart_simulator() {
    stop_simulator
    sleep 1
    start_simulator
}

# Function to show status
status_simulator() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo -e "${GREEN}✅ Simulator is running (PID: $pid)${NC}"

        # Show recent log lines
        if [ -f "$LOG_FILE" ]; then
            echo -e "\n${BLUE}Recent log entries:${NC}"
            tail -n 10 "$LOG_FILE"
        fi
    else
        echo -e "${RED}❌ Simulator is not running${NC}"
        rm -f "$PID_FILE"
    fi
}

# Function to show logs
logs_simulator() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo -e "${YELLOW}No log file found${NC}"
    fi
}

# Main command handler
case "${1:-start}" in
    start)
        start_simulator
        ;;
    stop)
        stop_simulator
        ;;
    restart)
        restart_simulator
        ;;
    status)
        status_simulator
        ;;
    logs)
        logs_simulator
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the simulator"
        echo "  stop    - Stop the simulator"
        echo "  restart - Restart the simulator"
        echo "  status  - Show simulator status"
        echo "  logs    - Follow simulator logs"
        exit 1
        ;;
esac
