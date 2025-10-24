# Getting Started - OptiFlow AI Platform

## Prerequisites

- Docker 24.0+
- Docker Compose 2.20+
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd optiflow-platform
   ```

2. **Configure environment**
   ```bash
   cp backend/.env.example backend/.env
   # Edit .env with your configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - InfluxDB: http://localhost:8086
   - Grafana: http://localhost:3000

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Gateway Development

```bash
cd gateway
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app/main.py
```

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Next Steps

- Read the [Architecture Documentation](../architecture/ARCHITECTURE.md)
- Check the [API Documentation](http://localhost:8000/docs)
- Explore the [Deployment Guide](../deployment/)
