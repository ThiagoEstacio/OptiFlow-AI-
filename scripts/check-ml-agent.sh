#!/bin/bash
# OptiFlow AI - ML & Agent Status Checker
# Verifica status de MLflow, Ollama e Autonomous Agent

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     OptiFlow AI - ML & Agent Status Diagnostic              ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. MLflow Status
echo -e "${CYAN}━━━ MLflow Status ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if docker compose ps mlflow | grep -q "Up"; then
    echo -e "  ✅ ${GREEN}MLflow container: Running${NC}"
    
    # Check if MLflow is accessible
    if docker compose exec mlflow curl -s http://127.0.0.1:5000/health > /dev/null 2>&1; then
        echo -e "  ✅ ${GREEN}MLflow server: Healthy${NC}"
        echo -e "  ⚠️  ${YELLOW}Note: MLflow is only accessible inside the container${NC}"
        echo -e "  💡 ${YELLOW}Reason: Binds to 127.0.0.1 instead of 0.0.0.0${NC}"
    else
        echo -e "  ❌ ${RED}MLflow server: Not responding${NC}"
    fi
    
    # Check experiments
    echo -n "  📊 Experiments: "
    EXP_COUNT=$(docker compose exec mlflow ls -1 /app/mlruns 2>/dev/null | wc -l)
    echo -e "${CYAN}$EXP_COUNT${NC}"
else
    echo -e "  ❌ ${RED}MLflow container: Not running${NC}"
fi

# 2. Ollama Status
echo ""
echo -e "${CYAN}━━━ Ollama AI Status ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "  ✅ ${GREEN}Ollama server: Running${NC}"
    
    # List models
    MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; models=json.load(sys.stdin).get('models',[]); print(len(models))" 2>/dev/null || echo "0")
    if [ "$MODELS" -gt 0 ]; then
        echo -e "  ✅ ${GREEN}Models loaded: $MODELS${NC}"
        curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; [print(f'    - {m[\"name\"]}') for m in json.load(sys.stdin).get('models',[])]" 2>/dev/null
    else
        echo -e "  ⚠️  ${YELLOW}Models loaded: 0${NC}"
        echo -e "  💡 Install with: ${CYAN}ollama pull llama2${NC}"
    fi
else
    echo -e "  ❌ ${RED}Ollama server: Not running${NC}"
    echo -e "  💡 Start with: ${CYAN}ollama serve${NC}"
    echo -e "  📦 Install: ${CYAN}https://ollama.ai${NC}"
fi

# 3. Agent Status
echo ""
echo -e "${CYAN}━━━ Autonomous Agent Status ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if curl -s http://localhost:8000/api/v1/agent/health > /dev/null 2>&1; then
    AGENT_STATUS=$(curl -s http://localhost:8000/api/v1/agent/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))" 2>/dev/null)
    
    if [ "$AGENT_STATUS" = "healthy" ]; then
        echo -e "  ✅ ${GREEN}Agent API: Healthy${NC}"
        curl -s http://localhost:8000/api/v1/agent/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'    Ollama: {\"✓\" if d.get(\"ollama_available\") else \"✗\"}'); print(f'    Model: {\"✓\" if d.get(\"model_loaded\") else \"✗\"}')"  2>/dev/null
    else
        echo -e "  ⚠️  ${YELLOW}Agent API: $AGENT_STATUS${NC}"
        MESSAGE=$(curl -s http://localhost:8000/api/v1/agent/health | python3 -c "import sys,json; print(json.load(sys.stdin).get('message',''))" 2>/dev/null)
        echo -e "    ${YELLOW}$MESSAGE${NC}"
    fi
else
    echo -e "  ❌ ${RED}Agent API: Not accessible${NC}"
fi

# Check background monitoring
echo ""
echo -e "${CYAN}━━━ Background Monitoring ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
AGENT_LOGS=$(docker compose logs backend 2>&1 | grep -i "autonomous.*complete\|monitoring cycle" | tail -3)
if [ -n "$AGENT_LOGS" ]; then
    echo -e "  ✅ ${GREEN}Autonomous monitoring: Active${NC}"
    echo "$AGENT_LOGS" | while read line; do
        echo "    $(echo $line | grep -o 'Monitoring cycle.*\|insights:.*')"
    done
else
    echo -e "  ⚠️  ${YELLOW}Autonomous monitoring: No recent activity${NC}"
fi

# 4. ML Models
echo ""
echo -e "${CYAN}━━━ ML Models & Training ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if curl -s http://localhost:8000/api/v1/advanced/ml/train > /dev/null 2>&1; then
    echo -e "  ✅ ${GREEN}ML Training API: Available${NC}"
else
    echo -e "  ⚠️  ${YELLOW}ML Training API: Requires authentication${NC}"
fi

# Check model files
MODEL_COUNT=$(find /home/thiestacio/OptiFlow-AI-/backend/app/ml_models -name "*.pkl" 2>/dev/null | wc -l || echo "0")
echo -e "  📦 Trained models: ${CYAN}$MODEL_COUNT${NC} .pkl files"

# 5. InfluxDB Integration
echo ""
echo -e "${CYAN}━━━ InfluxDB Integration ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if curl -s http://localhost:8086/health > /dev/null 2>&1; then
    echo -e "  ✅ ${GREEN}InfluxDB: Running${NC}"
    
    # Check data
    TAG_DISCOVER=$(docker compose logs backend 2>&1 | grep "Auto-discovered.*tags" | tail -1)
    if [ -n "$TAG_DISCOVER" ]; then
        TAG_COUNT=$(echo "$TAG_DISCOVER" | grep -o '[0-9]\+ tags' | grep -o '[0-9]\+')
        echo -e "  📊 Tags discovered: ${CYAN}$TAG_COUNT${NC}"
    fi
else
    echo -e "  ❌ ${RED}InfluxDB: Not accessible${NC}"
fi

# 6. Summary & Recommendations
echo ""
echo -e "${BLUE}━━━ Summary & Recommendations ━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check what needs to be fixed
NEEDS_FIX=0

if ! docker compose ps mlflow | grep -q "Up"; then
    echo -e "  ❌ ${RED}MLflow not running${NC}"
    echo -e "     Fix: ${CYAN}docker compose up -d mlflow${NC}"
    NEEDS_FIX=1
fi

if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "  ❌ ${RED}Ollama not running${NC}"
    echo -e "     Fix: ${CYAN}ollama serve${NC} (in another terminal)"
    echo -e "     Or install: ${CYAN}curl https://ollama.ai/install.sh | sh${NC}"
    NEEDS_FIX=1
fi

MODELS=$(curl -s http://localhost:11434/api/tags 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('models',[])))" 2>/dev/null || echo "0")
if [ "$MODELS" -eq 0 ]; then
    echo -e "  ⚠️  ${YELLOW}No AI models loaded${NC}"
    echo -e "     Fix: ${CYAN}ollama pull llama2${NC} or ${CYAN}ollama pull mistral${NC}"
fi

if [ $NEEDS_FIX -eq 0 ]; then
    echo -e "  ✅ ${GREEN}All core ML/AI services are running!${NC}"
    echo -e "  📊 Agent is monitoring with synthetic data (no real process data yet)"
fi

echo ""
echo -e "${BLUE}━━━ Quick Access ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  🤖 Agent Health:  ${CYAN}curl http://localhost:8000/api/v1/agent/health${NC}"
echo -e "  🧪 MLflow:        ${CYAN}docker compose exec mlflow mlflow ui --host 0.0.0.0${NC}"
echo -e "  🦙 Ollama Models: ${CYAN}ollama list${NC}"
echo ""
