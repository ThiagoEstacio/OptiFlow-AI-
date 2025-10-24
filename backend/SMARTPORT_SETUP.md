# 🚢 SmartPort MVP - Setup Guide

Complete guide for setting up and running the SmartPort MVP backend with demo data for client presentations.

---

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 14+ (running and accessible)
- Redis (optional, for caching)
- InfluxDB 2.x (optional, for time series data)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy and configure the environment file:

```bash
cp .env.example .env
```

Update `.env` with your database credentials:

```env
# Database
DATABASE_URL=postgresql+asyncpg://your_user:your_password@localhost:5432/smartport_dev
```

### 3. Run Database Migrations

Initialize the database schema with Alembic:

```bash
# Run migrations to create all tables
alembic upgrade head
```

This will create:
- ✅ Core tables (organizations, sites, users, devices, tags)
- ✅ SmartPort tables (vessels, berths, loading_operations, cargos, equipment)
- ✅ All indexes and foreign key constraints

### 4. Seed Demo Data

Load realistic demo data for client presentations:

```bash
python scripts/seed_smartport_demo.py
```

This creates:
- ✅ 1 demo organization ("Terminal Santos Grãos S.A.")
- ✅ 1 port site ("Terminal Santos - Cais Principal")
- ✅ 2 berths (B1 - occupied, B2 - available)
- ✅ 4 vessels (different statuses for complete demo)
- ✅ 3 loading operations (1 in progress @ 65%, 2 completed)
- ✅ 8 port equipment items (conveyors, elevators, shiploaders)
- ✅ Multiple cargos (soybean, corn, sugar)
- ✅ Operation events for timeline
- ✅ Maintenance records for predictive demo

### 5. Start the API Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Access API Documentation

Open your browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📊 Demo Data Overview

### Organization & Site
```yaml
Organization: Terminal Santos Grãos S.A.
Site: Terminal Santos - Cais Principal
Location: Santos, São Paulo, Brasil
Coordinates: -23.9575, -46.3328
```

### Berths
| Code | Name | Type | Status | Capacity | Shiploaders |
|------|------|------|--------|----------|-------------|
| B1 | Berço 1 - Graneleiro Principal | BULK | OCCUPIED | 3,500 t/h | 3 |
| B2 | Berço 2 - Graneleiro Secundário | BULK | AVAILABLE | 2,500 t/h | 2 |

### Vessels
| Name | IMO | Status | Location | Cargo |
|------|-----|--------|----------|-------|
| MV GRAIN CARRIER | IMO9876543 | LOADING | B1 | Soybean (65% done) |
| MV BULK EXPLORER | IMO9765432 | ANCHORED | Anchorage | Waiting for berth |
| MV EXPORT CHAMPION | IMO9654321 | DEPARTED | - | Completed |
| MV OCEAN LIBERTY | IMO9543210 | SCHEDULED | ETA +2 days | Scheduled |

### Operations
| Number | Vessel | Status | Progress | Commodity | Quantity |
|--------|--------|--------|----------|-----------|----------|
| OP-2025-001-SANTOS | MV GRAIN CARRIER | IN_PROGRESS | 65% | Soybean | 48,750 / 75,000 t |
| OP-2025-002-SANTOS | MV EXPORT CHAMPION | COMPLETED | 100% | Soybean | 94,850 t |
| OP-2025-003-SANTOS | (Historical) | COMPLETED | 100% | Corn | 61,890 t |

### Equipment
| Code | Type | Status | Health | Failure Risk | Location |
|------|------|--------|--------|--------------|----------|
| TC4515 | Conveyor | OPERATING | 92.5% | 8.5% | B1 |
| **TC2521** | Conveyor | OPERATING | **73.0%** | **27.0%** ⚠️ | B1 |
| EL4511 | Elevator | OPERATING | 88.5% | 11.5% | B1 |
| SL01 | Shiploader | OPERATING | 95.0% | 5.0% | B1 |
| SL02 | Shiploader | IDLE | 91.0% | 9.0% | B2 |
| WS101 | Weighing Scale | OPERATING | 96.5% | 3.5% | B1 |

**Note**: TC2521 is intentionally configured with lower health for **predictive maintenance demo**.

---

## 🔌 API Endpoints

### SmartPort APIs (under `/api/v1/port/`)

#### Vessels
```
GET    /port/vessels              - List vessels with filtering
POST   /port/vessels              - Create vessel
GET    /port/vessels/{id}         - Get vessel details
PUT    /port/vessels/{id}         - Update vessel
DELETE /port/vessels/{id}         - Delete vessel
GET    /port/vessels/{id}/operations - Get vessel operations
PATCH  /port/vessels/{id}/status  - Update status
```

#### Berths
```
GET    /port/berths               - List berths
POST   /port/berths               - Create berth
GET    /port/berths/{id}          - Get berth details
GET    /port/berths/{id}/status   - Get current status
GET    /port/berths/{id}/occupancy - Get occupancy timeline
GET    /port/berths/{id}/capacity  - Get capacity info
```

#### Operations
```
GET    /port/operations           - List operations
POST   /port/operations           - Create operation
GET    /port/operations/{id}      - Get operation details
GET    /port/operations/{id}/progress - Get real-time progress
POST   /port/operations/{id}/start - Start operation
POST   /port/operations/{id}/pause - Pause operation
POST   /port/operations/{id}/complete - Complete operation
POST   /port/operations/{id}/delay - Report delay
```

#### Analytics
```
GET    /port/analytics/kpis       - Port operational KPIs
GET    /port/analytics/performance - Performance metrics
GET    /port/analytics/equipment/{id} - Equipment performance
GET    /port/analytics/commodity-breakdown - Commodity analytics
GET    /port/analytics/trends     - Trend data
```

---

## 🎬 Demo Scenarios for Clients

### Scenario 1: Real-Time Operation Monitoring

**Show active loading operation:**
```bash
GET /port/operations/{operation_id}/progress
```

**Highlights:**
- ✅ Real-time progress (65% complete)
- ✅ Current loading rate (1,850 t/h)
- ✅ Estimated completion time
- ✅ Efficiency metrics (91.5%)
- ✅ Equipment status

### Scenario 2: Predictive Maintenance (AI/ML Feature)

**Show equipment with maintenance risk:**
```bash
GET /port/analytics/equipment/{TC2521_id}
```

**Highlights:**
- ⚠️ Equipment TC2521 has 73% health score
- ⚠️ 27% failure probability (HIGH RISK)
- 💰 ROI of preventive vs corrective maintenance
- 📊 Historical maintenance records
- 🔮 AI prediction of failure within 24-48h

### Scenario 3: Port Performance Dashboard

**Get comprehensive KPIs:**
```bash
GET /port/analytics/kpis?from_date=2025-01-01&to_date=2025-01-31
```

**Highlights:**
- 📈 Total throughput: 204,490 tons
- ⚡ Average loading rate: 1,825 t/h
- 🎯 Average efficiency: 95.2%
- 🚢 Vessels processed: 3 completed, 1 active
- ⏱️ Average turnaround time: 40.7 hours

### Scenario 4: Vessel Tracking

**Track vessel journey:**
```bash
GET /port/vessels/{vessel_id}
```

**Highlights:**
- 📍 Current location and status
- ⏰ ETA, ATA, ETB, ATB, ETC, ETD (complete timeline)
- 📦 Current cargo details
- 📊 Operation progress
- 📝 Event timeline

---

## 🧪 Testing the APIs

### Example 1: List All Active Operations

```bash
curl -X GET "http://localhost:8000/api/v1/port/operations?status=in_progress" \
  -H "accept: application/json"
```

### Example 2: Get Operation Progress

```bash
curl -X GET "http://localhost:8000/api/v1/port/operations/{operation_id}/progress" \
  -H "accept: application/json"
```

### Example 3: Get Port KPIs

```bash
curl -X GET "http://localhost:8000/api/v1/port/analytics/kpis?from_date=2025-01-01T00:00:00&to_date=2025-01-31T23:59:59" \
  -H "accept: application/json"
```

### Example 4: List Berth Occupancy

```bash
curl -X GET "http://localhost:8000/api/v1/port/berths/{berth_id}/occupancy" \
  -H "accept: application/json"
```

---

## 🔄 Database Migrations

### Create a New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migration
alembic upgrade head
```

### Rollback Migration

```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Rollback all
alembic downgrade base
```

### View Migration History

```bash
# Show current version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic upgrade --sql head
```

---

## 🗄️ Database Schema

### Core Tables
- `organizations` - Multi-tenant organizations
- `sites` - Physical sites/ports
- `users` - System users
- `devices` - Industrial equipment/PLCs
- `tags` - Data points/sensors

### SmartPort Tables
- `vessels` - Ships/vessels
- `berths` - Port berths/terminals
- `loading_operations` - Cargo operations
- `cargos` - Commodity details
- `operation_events` - Timeline tracking
- `port_equipment` - Port handling equipment
- `maintenance_records` - Maintenance history

---

## 📈 Performance Optimization

### Database Indexes

All SmartPort tables have optimized indexes:
- ✅ Foreign key columns (site_id, vessel_id, berth_id, etc.)
- ✅ Status columns for filtering
- ✅ Date/time columns for range queries
- ✅ Unique identifiers (IMO, operation_number, equipment_code)

### Query Performance Tips

1. **Use filters**: Always filter by `site_id` for multi-tenant queries
2. **Pagination**: Use `skip` and `limit` parameters
3. **Date ranges**: Limit queries to specific date ranges
4. **Select specific fields**: Use `DetailResponse` schemas only when needed

---

## 🐛 Troubleshooting

### Issue: "table already exists" error

```bash
# Drop all tables and recreate
alembic downgrade base
alembic upgrade head
python scripts/seed_smartport_demo.py
```

### Issue: Connection refused to PostgreSQL

```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL (Ubuntu/Debian)
sudo service postgresql start

# Start PostgreSQL (macOS with Homebrew)
brew services start postgresql
```

### Issue: Import errors in migration

Make sure all models are imported in `alembic/env.py`:
```python
from app.models.port.vessel import Vessel
from app.models.port.berth import Berth
# ... etc
```

---

## 🎯 Next Steps

1. **Frontend Development** (Week 3-8):
   - Dashboard components
   - Real-time operation monitoring
   - Vessel management UI
   - Analytics visualizations

2. **ML Integration** (Week 5):
   - Train predictive maintenance models
   - Implement SHAP explanations
   - Real-time predictions

3. **Reports & Export** (Week 7):
   - PDF generation
   - Excel exports
   - Custom report builder

4. **WebSocket Support**:
   - Real-time progress updates
   - Equipment status streaming
   - Alarm notifications

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Alembic Docs**: https://alembic.sqlalchemy.org/
- **SQLAlchemy Async**: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **FastAPI Docs**: https://fastapi.tiangolo.com/

---

## 🤝 Support

For issues or questions:
1. Check API documentation at `/docs`
2. Review logs in console output
3. Check database connection settings in `.env`

---

**🚢 Happy sailing with SmartPort!**

---

*Generated with Claude Code*
*https://claude.com/claude-code*
