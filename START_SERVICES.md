# 🚀 SmartPort Analytics - Service Startup Guide

## Prerequisites

### Backend Requirements
- Python 3.9+
- InfluxDB 2.x running (default: localhost:8086)
- PostgreSQL running (for user/device data)

### Frontend Requirements
- Node.js 16+
- npm or yarn

---

## 1. Start Backend (Terminal 1)

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment (if using venv)
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Start FastAPI server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative: Using Python directly
# python -m uvicorn app.main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using StatReload
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Backend API Docs:** http://localhost:8000/docs

---

## 2. Start Frontend (Terminal 2)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already installed)
npm install
# OR
yarn install

# Start React development server
npm start
# OR
yarn start
```

**Expected Output:**
```
Compiled successfully!

You can now view smartport-frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

**Frontend App:** http://localhost:3000

---

## 3. Verify Services

### Check Backend Health
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

### Check Analytics Endpoints
```bash
# Get available functions
curl http://localhost:8000/api/v1/analytics/functions

# Get query examples
curl http://localhost:8000/api/v1/analytics/examples
```

### Check Frontend
Open browser: http://localhost:3000
- Should see SmartPort dashboard
- Navigate to Analytics page

---

## 4. Access Analytics Features

### Via Web UI:
1. Login at http://localhost:3000
2. Navigate to **Analytics** in sidebar
3. Use Query Builder to create queries
4. Toggle between "Execute Once" and "Stream Live" modes

### Via API:
```bash
# Execute analytics query (one-time)
curl -X POST http://localhost:8000/api/v1/analytics/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["tag1", "tag2"],
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-01T23:59:59Z",
    "aggregations": [
      {"function": "mean", "field": "value", "window": "1h"}
    ]
  }'
```

### Via WebSocket:
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/analytics/ws/stream?token=YOUR_TOKEN');

// Send query
ws.send(JSON.stringify({
  action: 'start',
  query: {
    tags: ['tag1', 'tag2'],
    start: '2024-01-01T00:00:00Z',
    end: '2024-01-01T23:59:59Z',
    aggregations: [
      {function: 'mean', field: 'value', window: '1h'}
    ]
  },
  refresh_interval: 5
}));

// Receive data
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

---

## 5. Environment Configuration

### Backend (.env)
Create `backend/.env` if it doesn't exist:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/smartport
DATABASE_URL_ASYNC=postgresql+asyncpg://user:password@localhost:5432/smartport

# InfluxDB
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-influxdb-token
INFLUXDB_ORG=smartport
INFLUXDB_BUCKET=timeseries

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

### Frontend (.env)
Create `frontend/.env` if it doesn't exist:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

---

## 6. Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Find process using port 8000
lsof -i :8000
# Kill process
kill -9 <PID>
# Or use different port
uvicorn app.main:app --reload --port 8001
```

**InfluxDB connection error:**
- Ensure InfluxDB is running: `systemctl status influxdb` (Linux)
- Verify INFLUXDB_URL and INFLUXDB_TOKEN in .env
- Check InfluxDB is accessible: `curl http://localhost:8086/health`

**Database connection error:**
- Ensure PostgreSQL is running
- Verify DATABASE_URL in .env
- Run migrations: `alembic upgrade head`

### Frontend Issues

**Port 3000 already in use:**
```bash
# Kill process on port 3000
lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9
# Or set different port
PORT=3001 npm start
```

**Module not found errors:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**WebSocket connection failed:**
- Verify backend is running on port 8000
- Check REACT_APP_WS_URL in frontend/.env
- Verify JWT token is valid

---

## 7. Quick Test Commands

Run these after both services are started:

```bash
# Test backend health
curl http://localhost:8000/health

# Test analytics functions endpoint
curl http://localhost:8000/api/v1/analytics/functions | jq

# Test analytics examples endpoint
curl http://localhost:8000/api/v1/analytics/examples | jq

# Test frontend is serving
curl http://localhost:3000

# Run validation script
python test_analytics_validation.py

# Run endpoint tests (if you have auth token)
python test_analytics_endpoints.py
```

---

## 8. Development Workflow

**Hot Reload:**
- Backend: uvicorn auto-reloads on Python file changes
- Frontend: React auto-reloads on JS/TS file changes

**Logs:**
- Backend: Terminal 1 shows FastAPI logs
- Frontend: Terminal 2 shows React build logs
- Browser Console: Shows frontend runtime logs

**Debugging:**
- Backend: Add breakpoints in Python IDE or use `import pdb; pdb.set_trace()`
- Frontend: Use browser DevTools (F12) and React DevTools extension

---

## 9. Production Deployment

For production deployment, see:
- `DEPLOYMENT_GUIDE.md` for full production setup
- Use `gunicorn` for backend instead of uvicorn
- Build frontend: `npm run build`
- Use nginx as reverse proxy
- Enable HTTPS with SSL certificates
- Set production environment variables

---

## Need Help?

- Backend API Docs: http://localhost:8000/docs
- Backend ReDoc: http://localhost:8000/redoc
- Check logs in terminals
- Run validation: `python test_analytics_validation.py`
- Review this guide's Troubleshooting section

---

**Happy Coding! 🚀**
