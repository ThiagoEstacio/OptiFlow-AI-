# OptiFlow AI Platform - Getting Started Guide

Complete guide to get the OptiFlow AI Platform running locally.

---

## 🚀 Quick Start (5 minutes)

### Prerequisites

- **Docker** 24.0+ and **Docker Compose** 2.20+
- **Node.js** 18+ (for frontend development)
- **Python** 3.11+ (optional, for backend development)

### 1. Clone Repository

```bash
git clone <repository-url>
cd optiflow-platform
```

### 2. Configure Environment

```bash
# Copy environment example
cp .env.example .env

# Edit .env if needed (default values work for development)
nano .env
```

### 3. Start All Services

```bash
# Start backend, databases, and all services
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Start Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

### 5. Access Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090

**Default credentials**: admin / password

---

## 📦 What Gets Started

### Services Running in Docker:

1. **PostgreSQL** (Port 5432)
   - Relational database
   - User management, organizations, devices

2. **InfluxDB** (Port 8086)
   - Time series database
   - Sensor data storage

3. **Redis** (Port 6379)
   - Cache and pub/sub
   - WebSocket support

4. **RabbitMQ** (Port 5672, 15672)
   - Message queue
   - Celery task broker

5. **Backend API** (Port 8000)
   - FastAPI application
   - REST APIs and WebSocket

6. **Celery Worker**
   - Background tasks
   - Data processing

7. **Celery Beat**
   - Task scheduler
   - Periodic jobs

8. **MLflow** (Port 5000)
   - ML model tracking
   - Model registry

9. **Prometheus** (Port 9090)
   - Metrics collection
   - Monitoring

10. **Grafana** (Port 3000)
    - Dashboards
    - Visualization

### Frontend (Separate Process):

- **React App** (Port 5173)
  - Vite dev server
  - Hot reload enabled

---

## 🎯 Verify Installation

### Backend Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

### Database Connection

```bash
# PostgreSQL
docker exec -it optiflow-postgres psql -U optiflow -d optiflow -c "SELECT version();"

# InfluxDB
docker exec -it optiflow-influxdb influx ping
```

### WebSocket Connection

Open browser console at http://localhost:5173 and check for:
```
✅ WebSocket connected
```

---

## 📊 Test the Platform

### 1. Access Frontend

Open http://localhost:5173

You should see the login page.

### 2. Login

```
Username: admin
Password: password
```

### 3. View Dashboard

After login, you'll see:
- Real-time charts
- Statistics panels
- Anomaly detection
- Stat cards

### 4. Test Real-time Data

The dashboard should show:
- Live WebSocket connection indicator
- Updating charts
- Real-time metrics

### 5. Explore API Documentation

Visit http://localhost:8000/docs to:
- Browse all API endpoints
- Test APIs interactively
- View request/response schemas

---

## 🔧 Development Workflow

### Backend Development

```bash
# Access backend container
docker exec -it optiflow-backend bash

# Run tests
pytest

# Check code style
black app/ --check
flake8 app/

# Type checking
mypy app/
```

### Frontend Development

```bash
cd frontend

# Start dev server (with hot reload)
npm run dev

# Run tests
npm test

# Type checking
npm run type-check

# Lint code
npm run lint

# Format code
npm run format
```

### Database Migrations

```bash
# Create new migration
docker exec -it optiflow-backend alembic revision --autogenerate -m "description"

# Apply migrations
docker exec -it optiflow-backend alembic upgrade head

# Rollback one migration
docker exec -it optiflow-backend alembic downgrade -1
```

---

## 🐛 Troubleshooting

### Problem: Services won't start

**Solution:**
```bash
# Stop all services
docker-compose down

# Remove volumes (⚠️ deletes all data)
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Start again
docker-compose up -d
```

### Problem: Frontend can't connect to backend

**Check:**
1. Backend is running: `curl http://localhost:8000/health`
2. CORS is configured: Check `CORS_ORIGINS` in `.env`
3. Network tab in browser for errors

**Solution:**
```bash
# Restart backend
docker-compose restart backend

# Check logs
docker-compose logs backend
```

### Problem: WebSocket not connecting

**Check:**
1. Redis is running: `docker ps | grep redis`
2. WebSocket URL correct in frontend/.env
3. JWT token is valid

**Solution:**
```bash
# Restart Redis
docker-compose restart redis

# Check Redis logs
docker-compose logs redis
```

### Problem: Database connection errors

**Solution:**
```bash
# Wait for databases to be ready
docker-compose ps

# Check PostgreSQL
docker exec -it optiflow-postgres pg_isready -U optiflow

# Check InfluxDB
docker exec -it optiflow-influxdb influx ping
```

### Problem: Port already in use

**Check which ports are in use:**
```bash
# Linux/Mac
lsof -i :8000
lsof -i :5173

# Windows
netstat -ano | findstr :8000
```

**Solution:**
Change ports in docker-compose.yml or stop conflicting services.

---

## 📝 Useful Commands

### Docker

```bash
# View all containers
docker-compose ps

# View logs
docker-compose logs -f [service_name]

# Restart service
docker-compose restart [service_name]

# Stop all
docker-compose down

# Start specific service
docker-compose up -d backend

# Rebuild service
docker-compose build backend
```

### Backend

```bash
# Run Python shell
docker exec -it optiflow-backend python

# Access PostgreSQL
docker exec -it optiflow-postgres psql -U optiflow -d optiflow

# View Celery tasks
docker exec -it optiflow-celery-worker celery -A app.tasks.celery_app inspect active
```

### Frontend

```bash
# Install dependency
npm install <package>

# Update dependencies
npm update

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 🔑 Default Credentials

### Application
- **Username**: admin
- **Password**: password

### Databases
- **PostgreSQL**: optiflow / optiflow_password
- **InfluxDB**: admin / adminpassword
- **Redis**: optiflow_redis_password
- **RabbitMQ**: optiflow / optiflow_password

### Monitoring
- **Grafana**: admin / admin
- **Prometheus**: No authentication

---

## 📚 Next Steps

### For Users:
1. Read [Frontend Integration Guide](./api/FRONTEND_INTEGRATION.md)
2. Explore [API Documentation](http://localhost:8000/docs)
3. Check [Roadmap Status](./ROADMAP_STATUS.md)

### For Developers:
1. Review [Architecture Documentation](./architecture/ARCHITECTURE.md)
2. Read [Development Guide](./development/GETTING_STARTED.md)
3. Check [Production Deployment Guide](./deployment/PRODUCTION_DEPLOYMENT.md)

### To Test Features:
1. **Real-time Monitoring**: Open dashboard, watch live charts
2. **Analytics**: Check statistics panel and anomaly detection
3. **WebSocket**: Open browser console, see connection messages
4. **API**: Visit /docs, try interactive API calls
5. **Export**: Use export endpoints to download data

---

## 🎉 Success Checklist

- [ ] All Docker containers running
- [ ] Frontend loads at http://localhost:5173
- [ ] Can login successfully
- [ ] Dashboard shows real-time charts
- [ ] WebSocket connected (green indicator)
- [ ] API docs accessible at /docs
- [ ] No errors in browser console
- [ ] No errors in Docker logs

If all checked, congratulations! You're ready to use OptiFlow AI! 🚀

---

## 🆘 Still Having Issues?

1. **Check logs**: `docker-compose logs -f`
2. **Verify environment**: Review `.env` and `frontend/.env`
3. **Restart everything**: `docker-compose down && docker-compose up -d`
4. **Clean install**: `docker-compose down -v && docker-compose up -d`

**Need help?**
- Check [GitHub Issues](https://github.com/your-org/optiflow-platform/issues)
- Review [Troubleshooting Guide](./TROUBLESHOOTING.md)
- Contact: support@optiflow.ai

---

**Happy coding! 🎉**
