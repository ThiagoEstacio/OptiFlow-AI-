#!/bin/bash
# Start all OptiFlow AI services including simulator
# Use this script to start the complete stack

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_ROOT/.env.local"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default configuration
ENABLE_SIMULATOR=${ENABLE_SIMULATOR:-true}
ENABLE_BACKEND=${ENABLE_BACKEND:-true}
ENABLE_FRONTEND=${ENABLE_FRONTEND:-true}

# Load configuration if exists
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         OptiFlow AI - SmartPort Complete Startup             ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to check if Docker is running
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        echo -e "${YELLOW}   Please install Docker first: https://docs.docker.com/get-docker/${NC}"
        return 1
    fi

    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker daemon is not running${NC}"
        echo -e "${YELLOW}   Please start Docker and try again${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ Docker is running${NC}"
    return 0
}

# Function to start Docker services (PostgreSQL, InfluxDB, Redis)
start_backend_services() {
    if [ "$ENABLE_BACKEND" != "true" ]; then
        echo -e "${YELLOW}⏭️  Backend services disabled in configuration${NC}"
        return 0
    fi

    echo -e "\n${BLUE}🐳 Starting backend services (Docker Compose)...${NC}"

    cd "$PROJECT_ROOT"

    if [ ! -f "docker-compose.yml" ]; then
        echo -e "${YELLOW}⚠️  docker-compose.yml not found, skipping${NC}"
        return 0
    fi

    docker compose up -d

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Backend services started${NC}"

        # Wait for services to be ready
        echo -e "${YELLOW}⏳ Waiting for services to be ready (10s)...${NC}"
        sleep 10

        return 0
    else
        echo -e "${RED}❌ Failed to start backend services${NC}"
        return 1
    fi
}

# Function to setup SmartPort tags
setup_smartport_tags() {
    echo -e "\n${BLUE}📋 Setting up SmartPort tags...${NC}"

    cd "$PROJECT_ROOT"

    if [ -f "setup_smartport.sh" ]; then
        bash setup_smartport.sh
        echo -e "${GREEN}✅ SmartPort tags configured${NC}"
    else
        echo -e "${YELLOW}⚠️  setup_smartport.sh not found, skipping${NC}"
    fi
}

# Function to start simulator
start_simulator() {
    if [ "$ENABLE_SIMULATOR" != "true" ]; then
        echo -e "${YELLOW}⏭️  Simulator disabled in configuration${NC}"
        return 0
    fi

    echo -e "\n${BLUE}🏭 Starting SmartPort Bulk Terminal Simulator...${NC}"

    "$SCRIPT_DIR/start-simulator.sh" start

    if [ $? -eq 0 ]; then
        return 0
    else
        echo -e "${YELLOW}⚠️  Simulator failed to start (non-critical)${NC}"
        return 0
    fi
}

# Function to start frontend dev server
start_frontend() {
    if [ "$ENABLE_FRONTEND" != "true" ]; then
        echo -e "${YELLOW}⏭️  Frontend disabled in configuration${NC}"
        return 0
    fi

    echo -e "\n${BLUE}🎨 Starting frontend development server...${NC}"

    cd "$PROJECT_ROOT/frontend"

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
        npm install
    fi

    echo -e "${CYAN}💡 Frontend will be available at: http://localhost:3000${NC}"
    echo -e "${CYAN}💡 Dashboard Builder: http://localhost:3000/dashboard-builder${NC}"
    echo -e "${YELLOW}   (Run 'npm run dev' in frontend/ directory to start)${NC}"
}

# Function to show status
show_status() {
    echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                      Service Status                          ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Docker services
    if command -v docker &> /dev/null && docker info &> /dev/null 2>&1; then
        echo -e "${BLUE}🐳 Docker Services:${NC}"
        docker compose ps 2>/dev/null || echo -e "${YELLOW}   No services running${NC}"
        echo ""
    fi

    # Simulator
    echo -e "${BLUE}🏭 Simulator:${NC}"
    "$SCRIPT_DIR/start-simulator.sh" status
    echo ""

    # URLs
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                      Access URLs                             ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}🌐 Frontend:           http://localhost:3000${NC}"
    echo -e "${GREEN}🎨 Dashboard Builder:  http://localhost:3000/dashboard-builder${NC}"
    echo -e "${GREEN}🔧 Backend API:        http://localhost:8000${NC}"
    echo -e "${GREEN}📊 API Docs:           http://localhost:8000/docs${NC}"
    echo ""

    # Configuration
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                      Configuration                           ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Backend Services:${NC} $([ "$ENABLE_BACKEND" = "true" ] && echo -e "${GREEN}Enabled" || echo -e "${YELLOW}Disabled")${NC}"
    echo -e "${BLUE}Simulator:${NC}        $([ "$ENABLE_SIMULATOR" = "true" ] && echo -e "${GREEN}Enabled" || echo -e "${YELLOW}Disabled")${NC}"
    echo -e "${BLUE}Frontend:${NC}         $([ "$ENABLE_FRONTEND" = "true" ] && echo -e "${GREEN}Enabled" || echo -e "${YELLOW}Disabled")${NC}"
    echo ""
    echo -e "${YELLOW}💡 To change configuration, edit: $CONFIG_FILE${NC}"
    echo ""
}

# Main execution
main() {
    # Check prerequisites
    check_docker || exit 1

    # Start services
    start_backend_services || exit 1
    setup_smartport_tags
    start_simulator
    start_frontend

    # Show status
    show_status

    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              ✅ OptiFlow AI Started Successfully              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}📝 Next steps:${NC}"
    echo -e "   1. Start frontend: ${YELLOW}cd frontend && npm run dev${NC}"
    echo -e "   2. Open Dashboard Builder: ${YELLOW}http://localhost:3000/dashboard-builder${NC}"
    echo -e "   3. Check simulator logs: ${YELLOW}./scripts/start-simulator.sh logs${NC}"
    echo ""
    echo -e "${YELLOW}To stop all services, run: ${BLUE}./scripts/stop-all.sh${NC}"
    echo ""
}

# Run main
main
