#!/bin/bash
# ============================================================================
# OptiFlow Gateway - Docker Entrypoint
# ============================================================================
#
# Handles startup in different modes:
# - development: Uvicorn with auto-reload
# - production: Gunicorn with multiple workers
# - standalone: Single worker for edge devices
#
# Environment Variables:
#   MODE: development|production|standalone (default: development)
#   HOST: Bind address (default: 0.0.0.0)
#   PORT: Port number (default: 8080)
#   WORKERS: Number of worker processes (default: 4)
#   LOG_LEVEL: info|debug|warning|error (default: info)
# ============================================================================

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}OptiFlow Gateway Edge - Starting...${NC}"
echo -e "${GREEN}======================================${NC}"

# Default values
MODE=${MODE:-development}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8080}
WORKERS=${WORKERS:-4}
LOG_LEVEL=${LOG_LEVEL:-info}

echo -e "${YELLOW}Mode:${NC} $MODE"
echo -e "${YELLOW}Host:${NC} $HOST:$PORT"
echo -e "${YELLOW}Gateway ID:${NC} ${GATEWAY_ID:-gateway-001}"
echo -e "${YELLOW}Gateway Name:${NC} ${GATEWAY_NAME:-OptiFlow Gateway Edge}"

# Validate configuration files
if [ ! -f "/app/config/adapters_config.yaml" ]; then
    echo -e "${YELLOW}⚠️  Warning: No adapters_config.yaml found${NC}"
    echo -e "${YELLOW}   Using default configuration${NC}"
fi

# Check if data directory is writable
if [ ! -w "/app/data" ]; then
    echo -e "${RED}❌ Error: /app/data is not writable${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configuration validated${NC}"
echo ""

# Start based on mode
case "$MODE" in
    production)
        echo -e "${GREEN}Starting in PRODUCTION mode with Gunicorn...${NC}"
        echo -e "${YELLOW}Workers:${NC} $WORKERS"

        exec gunicorn app.main_hybrid:app \
            --workers $WORKERS \
            --worker-class uvicorn.workers.UvicornWorker \
            --bind $HOST:$PORT \
            --timeout 120 \
            --graceful-timeout 30 \
            --keep-alive 5 \
            --access-logfile - \
            --error-logfile - \
            --log-level $LOG_LEVEL \
            --preload \
            --max-requests 10000 \
            --max-requests-jitter 1000
        ;;

    standalone)
        echo -e "${GREEN}Starting in STANDALONE mode (single worker)...${NC}"

        exec uvicorn app.main_hybrid:app \
            --host $HOST \
            --port $PORT \
            --log-level $LOG_LEVEL \
            --no-access-log \
            --timeout-keep-alive 30
        ;;

    development|*)
        echo -e "${GREEN}Starting in DEVELOPMENT mode with Uvicorn...${NC}"
        echo -e "${YELLOW}⚠️  Auto-reload enabled (not for production!)${NC}"

        exec uvicorn app.main_hybrid:app \
            --host $HOST \
            --port $PORT \
            --reload \
            --log-level $LOG_LEVEL \
            --access-log
        ;;
esac
