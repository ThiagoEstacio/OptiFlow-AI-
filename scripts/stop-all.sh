#!/bin/bash
# Stop all OptiFlow AI services

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         OptiFlow AI - Stopping All Services                  ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Stop simulator
echo -e "${BLUE}🏭 Stopping simulator...${NC}"
"$SCRIPT_DIR/start-simulator.sh" stop

# Stop Docker services
echo -e "\n${BLUE}🐳 Stopping Docker services...${NC}"
cd "$PROJECT_ROOT"
if [ -f "docker-compose.yml" ]; then
    docker compose down
    echo -e "${GREEN}✅ Docker services stopped${NC}"
else
    echo -e "${YELLOW}⚠️  docker-compose.yml not found${NC}"
fi

# Note about frontend
echo -e "\n${YELLOW}📝 Note: Frontend dev server must be stopped manually (Ctrl+C)${NC}"

echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✅ All Services Stopped                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
