# OptiFlow AI Platform

## Overview

OptiFlow AI is an **Industrial IoT (IIoT) platform with artificial intelligence** designed for real-time monitoring, predictive maintenance, and process optimization in industrial environments.

### Key Features

- **Real-time Data Collection**: Connect to PLCs, RTUs, and sensors using industrial protocols (OPC UA, Modbus, MQTT, S7)
- **Time Series Storage**: Optimized storage with InfluxDB for high-frequency industrial data
- **Interactive Dashboards**: Real-time visualization with WebSocket updates
- **Machine Learning**: ✅ **Trained ML models for anomaly detection** (Isolation Forest, F1=0.4546) with real-time API endpoints
- **Autonomous Agent**: LLM-powered assistant with ML insights for predictive maintenance recommendations
- **Alarm Management**: Comprehensive alarm system with statistics, filtering, and real-time updates
- **Multi-tenant Architecture**: Support for multiple organizations and sites
- **Vertical Solutions**: SmartPort, SmartMine, SmartSteel

## Architecture

```
FIELD (OT) → GATEWAY → BACKEND CORE → DATABASE → FRONTEND
    ↓           ↓            ↓              ↓              ↓
  PLCs      Protocols   APIs REST      InfluxDB       React
 Sensors   Industriais  WebSocket     PostgreSQL      Web App
  RTUs       Buffer      Celery Tasks    Redis         Mobile
  IEDs      Edge AI      ML Service                   Dashboards
```

## Tech Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0 (async)
- **Validation**: Pydantic 2.0+
- **Task Queue**: Celery 5.3+
- **Testing**: pytest + pytest-asyncio

### Gateway
- **Protocols**:
  - asyncua (OPC UA)
  - pymodbus (Modbus TCP/RTU)
  - paho-mqtt (MQTT)
  - python-snap7 (Siemens S7)
  - pycomm3 (EtherNet/IP)

### Frontend
- **Language**: TypeScript 5.0+
- **Framework**: React 18.2+
- **Build Tool**: Vite 5.0+
- **State Management**: Redux Toolkit + RTK Query
- **UI**: TailwindCSS 3.4+
- **Charts**: Recharts + Plotly + D3.js

### Databases
- **PostgreSQL**: 15+ (relational data)
- **InfluxDB**: 2.7+ (time series)
- **Redis**: 7.2+ (cache, sessions, pub/sub)

### ML Stack
- scikit-learn, XGBoost, LightGBM
- pandas, numpy
- MLflow (tracking, registry)

## Project Structure

```
optiflow-platform/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # REST API endpoints
│   │   ├── core/           # Core config, security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── db/             # Database utilities
│   │   ├── websocket/      # WebSocket handlers
│   │   ├── tasks/          # Celery tasks
│   │   └── utils/          # Utilities
│   ├── tests/
│   ├── alembic/            # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── gateway/                # Data collection gateway
│   ├── app/
│   │   ├── protocols/      # Industrial protocols
│   │   ├── core/           # Core functionality
│   │   └── services/       # Services
│   ├── config/             # Device configurations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React frontend
│   ├── src/
│   │   ├── api/            # API client
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── store/          # Redux store
│   │   ├── hooks/          # Custom hooks
│   │   └── utils/          # Utilities
│   ├── package.json
│   └── Dockerfile
├── infrastructure/         # Infrastructure as Code
│   ├── docker/
│   ├── kubernetes/
│   └── terraform/
├── docs/                   # Documentation
└── monitoring/             # Monitoring configs
    ├── prometheus/
    └── grafana/
```

## Quick Start

### Prerequisites

- Docker 24.0+
- Docker Compose 2.20+
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd optiflow-platform
   ```

2. **Configure environment variables**
   ```bash
   cp backend/.env.example backend/.env
   # Edit .env with your configuration
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - **ML Anomaly Detection**: http://localhost:8000/api/v1/analytics/anomalies
   - **Model Info**: http://localhost:8000/api/v1/analytics/model-info
   - InfluxDB UI: http://localhost:8086
   - RabbitMQ Management: http://localhost:15672
   - MLflow UI: http://localhost:5000

5. **Generate historical data (for ML training)**
   ```bash
   docker compose exec backend python scripts/generate_historical_data_simple.py
   ```

6. **Train ML models**
   ```bash
   # Fast training (Isolation Forest, ~30 seconds)
   docker compose exec backend python scripts/train_isolation_fast.py
   
   # Full training (Isolation Forest + LSTM, ~30-60 minutes)
   docker compose exec backend python scripts/train_anomaly_models.py
   ```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Documentation

- [Architecture Documentation](docs/architecture/)
- [**ML API Guide** - Anomaly Detection Endpoints](docs/ML_API_GUIDE.md) ✨ **NEW**
- [API Documentation](docs/api/)
- [Deployment Guide](docs/deployment/)
- [Development Guide](docs/development/)
- [Frontend Implementation Status](docs/FRONTEND_COMPLETE.md)
- [Alarm System Guide](docs/ALARM_SYSTEM.md)

## Roadmap

### Phase 1: MVP Core (6 months)
- Foundation setup
- Core functionality (devices, tags, data collection)
- SmartPort MVP

### Phase 2: ML & Analytics (4 months)
- ML infrastructure
- Predictive maintenance
- Analytics dashboards

### Phase 3: Expansion (4 months)
- SmartMine vertical
- SmartSteel vertical

### Phase 4: Enterprise (6 months)
- Advanced features
- Integrations (SAP, CMMS, BI tools)
- Scale & performance optimization

## Use Cases

- **Operational Monitoring**: Real-time visibility of industrial processes
- **Predictive Maintenance**: Predict equipment failures before they happen
- **Energy Optimization**: Reduce energy consumption by 30-40%
- **Quality Control**: Monitor and improve product quality
- **Performance Analytics**: Data-driven decision making

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

Proprietary - All rights reserved

## Contact

For questions and support, please contact the development team.

---

Built with Claude Code and modern software engineering best practices.
