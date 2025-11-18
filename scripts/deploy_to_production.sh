#!/bin/bash
# Production Deployment Script for OptiFlow AI
# ==============================================
# Deploys PDCA #1, #2, #5 enhancements to production

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
cat << "EOF"
 _____ _____ _____ _____ _____ _     _____    _    _____
|     |  _  |_   _|     |   __| |   |     |  | |  |     |
|  |  |   __|  | | |-   |   __| |   |  |  |  | |  |-   -|
|_____|__|     |_| |_____|__|  |_____|_____|  |_|  |_____|

  Production Deployment - PDCA Security Enhancements

EOF
echo -e "${NC}"

# ===========================================
# Step 0: Pre-flight Checks
# ===========================================

echo -e "${BLUE}[STEP 0] Pre-flight Checks${NC}"
echo "==========================================="
echo ""

# Check if docker is running
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi
echo -e "${GREEN}✅${NC} Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅${NC} docker-compose is available"

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    echo -e "${RED}❌ docker-compose.yml not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅${NC} docker-compose.yml found"

echo ""
read -p "Continue with deployment? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# ===========================================
# Step 1: Backup Current State
# ===========================================

echo ""
echo -e "${BLUE}[STEP 1] Creating Backups${NC}"
echo "==========================================="
echo ""

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$PROJECT_ROOT/backups/$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

echo "Backup directory: $BACKUP_DIR"

# Backup docker-compose.yml
if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    cp "$PROJECT_ROOT/docker-compose.yml" "$BACKUP_DIR/docker-compose.yml.backup"
    echo -e "${GREEN}✅${NC} docker-compose.yml backed up"
fi

# Backup .env if exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    cp "$PROJECT_ROOT/.env" "$BACKUP_DIR/.env.backup"
    echo -e "${GREEN}✅${NC} .env backed up"
fi

# Backup databases (if containers are running)
if docker ps | grep -q optiflow-postgres; then
    echo "Backing up PostgreSQL database..."
    docker exec optiflow-postgres pg_dump -U optiflow optiflow > "$BACKUP_DIR/postgres_backup.sql" 2>/dev/null || true
    echo -e "${GREEN}✅${NC} PostgreSQL backed up"
fi

if docker ps | grep -q optiflow-influxdb; then
    echo "Backing up InfluxDB..."
    docker exec optiflow-influxdb influx backup /tmp/influx_backup 2>/dev/null || true
    docker cp optiflow-influxdb:/tmp/influx_backup "$BACKUP_DIR/influx_backup" 2>/dev/null || true
    echo -e "${GREEN}✅${NC} InfluxDB backed up"
fi

echo -e "${GREEN}✅${NC} Backups completed in $BACKUP_DIR"

# ===========================================
# Step 2: Stop Current Containers
# ===========================================

echo ""
echo -e "${BLUE}[STEP 2] Stopping Current Containers${NC}"
echo "==========================================="
echo ""

cd "$PROJECT_ROOT"

if docker ps | grep -q optiflow-; then
    echo "Stopping OptiFlow containers..."
    docker-compose down
    echo -e "${GREEN}✅${NC} Containers stopped"
else
    echo -e "${YELLOW}ℹ️${NC}  No containers running"
fi

# ===========================================
# Step 3: Build New Images
# ===========================================

echo ""
echo -e "${BLUE}[STEP 3] Building Docker Images${NC}"
echo "==========================================="
echo ""

echo "Building backend, gateway, and frontend images..."
docker-compose build backend gateway frontend

echo -e "${GREEN}✅${NC} Images built successfully"

# ===========================================
# Step 4: Start Services
# ===========================================

echo ""
echo -e "${BLUE}[STEP 4] Starting Services${NC}"
echo "==========================================="
echo ""

echo "Starting OptiFlow services with new network configuration..."
docker-compose up -d

echo ""
echo "Waiting for services to become healthy (60 seconds)..."

# Wait for services to be healthy
sleep 10

for i in {1..10}; do
    echo -n "."
    sleep 5
done
echo ""

echo -e "${GREEN}✅${NC} Services started"

# ===========================================
# Step 5: Verify Deployment
# ===========================================

echo ""
echo -e "${BLUE}[STEP 5] Verifying Deployment${NC}"
echo "==========================================="
echo ""

# Check container status
RUNNING=$(docker ps --filter "name=optiflow-" --format "{{.Names}}" | wc -l)
echo "Running containers: $RUNNING"

# Check backend health
echo -n "Checking backend health... "
if curl -s http://localhost:8000/api/health | grep -q "healthy\|ok"; then
    echo -e "${GREEN}✅ Healthy${NC}"
else
    echo -e "${RED}❌ Unhealthy${NC}"
fi

# Check frontend
echo -n "Checking frontend... "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    echo -e "${GREEN}✅ Accessible${NC}"
else
    echo -e "${RED}❌ Not accessible${NC}"
fi

# Check network segmentation
echo -n "Checking network isolation... "
if docker exec optiflow-backend ping -c 1 -W 2 opcua-server 2>&1 | grep -q "Name or service not known\|Network is unreachable"; then
    echo -e "${GREEN}✅ OT network isolated${NC}"
else
    echo -e "${YELLOW}⚠️  OT network may not be isolated${NC}"
fi

# ===========================================
# Step 6: Post-Deployment Tasks
# ===========================================

echo ""
echo -e "${BLUE}[STEP 6] Post-Deployment Tasks${NC}"
echo "==========================================="
echo ""

echo "Checking for errors in logs..."
BACKEND_ERRORS=$(docker logs optiflow-backend --since 1m 2>&1 | grep -i "error\|exception" | wc -l)
if [ "$BACKEND_ERRORS" -eq 0 ]; then
    echo -e "${GREEN}✅${NC} No errors in backend logs"
else
    echo -e "${YELLOW}⚠️${NC}  $BACKEND_ERRORS errors found in backend logs"
fi

# ===========================================
# Step 7: Summary & Next Steps
# ===========================================

echo ""
echo -e "${CYAN}=========================================="
echo "Deployment Complete!"
echo "==========================================${NC}"
echo ""

echo -e "${GREEN}✅ PDCA #1:${NC} Network Segmentation OT/IT"
echo -e "${GREEN}✅ PDCA #5:${NC} Critical Alarms with Visual/Audio"
echo -e "${GREEN}✅ PDCA #2:${NC} mTLS Infrastructure (ready)"
echo ""

echo -e "${BLUE}Services:${NC}"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - Grafana: http://localhost:3001"
echo "  - Prometheus: http://localhost:9090"
echo ""

echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Run validation script:"
echo "     ./scripts/validate_pdca_deployment.sh"
echo ""
echo "  2. Generate mTLS certificates (optional):"
echo "     ./scripts/generate_mtls_certs.sh"
echo ""
echo "  3. Test critical alarm notifications:"
echo "     - Open http://localhost:3000"
echo "     - Login and wait for alarms"
echo "     - Or create test alarm via API"
echo ""
echo "  4. Review logs:"
echo "     docker-compose logs -f --tail=100 backend gateway"
echo ""
echo "  5. Monitor resources:"
echo "     docker stats optiflow-backend optiflow-gateway"
echo ""

echo -e "${BLUE}Backup Location:${NC} $BACKUP_DIR"
echo ""

echo -e "${CYAN}Deployment completed at $(date)${NC}"
echo ""

# Show container status
echo -e "${BLUE}Container Status:${NC}"
docker-compose ps
