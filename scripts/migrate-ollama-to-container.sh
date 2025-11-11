#!/bin/bash
# Migrate Ollama from host to Docker container

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     OptiFlow AI - Migrate Ollama to Container               ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Ollama is running on host
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}📍 Ollama is running on host (localhost:11434)${NC}"
    
    # List current models
    echo -e "${BLUE}Current models:${NC}"
    curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; [print(f'  - {m[\"name\"]}') for m in json.load(sys.stdin).get('models',[])]" 2>/dev/null
    
    echo ""
    echo -e "${YELLOW}⚠️  To use Ollama in OptiFlow container, we need to:${NC}"
    echo -e "   1. Stop host Ollama service"
    echo -e "   2. Start Ollama container"
    echo -e "   3. Pull models inside container"
    echo ""
    
    read -p "Continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Migration cancelled${NC}"
        exit 1
    fi
    
    # Stop host Ollama
    echo -e "${YELLOW}🛑 Stopping host Ollama...${NC}"
    if systemctl is-active --quiet ollama; then
        sudo systemctl stop ollama
        echo -e "${GREEN}✅ Systemd service stopped${NC}"
    elif pgrep -x "ollama" > /dev/null; then
        pkill ollama
        echo -e "${GREEN}✅ Ollama process killed${NC}"
    else
        echo -e "${GREEN}✅ No Ollama service to stop${NC}"
    fi
    
    sleep 2
else
    echo -e "${GREEN}✅ Port 11434 is free${NC}"
fi

# Start Ollama container
echo -e "${BLUE}🚀 Starting Ollama container...${NC}"
docker compose up -d ollama

# Wait for Ollama to be ready
echo -e "${YELLOW}⏳ Waiting for Ollama to start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Ollama container is ready!${NC}"
        break
    fi
    sleep 1
    echo -n "."
done
echo ""

# Pull llama3.1 model
echo -e "${BLUE}📥 Pulling llama3.1:8b model (this may take a while)...${NC}"
docker compose exec ollama ollama pull llama3.1:8b

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     ✅ Migration Complete!                                    ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  🐳 Ollama is now running in Docker container"
echo -e "  🌐 Available at: ${BLUE}http://localhost:11434${NC}"
echo -e "  🤖 Backend can access via: ${BLUE}http://ollama:11434${NC}"
echo ""
echo -e "${YELLOW}Quick commands:${NC}"
echo -e "  List models:   ${BLUE}docker compose exec ollama ollama list${NC}"
echo -e "  Pull model:    ${BLUE}docker compose exec ollama ollama pull mistral${NC}"
echo -e "  Chat test:     ${BLUE}docker compose exec ollama ollama run llama3.1:8b${NC}"
echo -e "  View logs:     ${BLUE}docker compose logs ollama${NC}"
echo ""
echo -e "${GREEN}Now restart backend to connect to Ollama:${NC}"
echo -e "  ${BLUE}docker compose restart backend${NC}"
echo ""
