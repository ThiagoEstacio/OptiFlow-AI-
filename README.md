# OptiFlow AI Platform

## Overview

OptiFlow AI is an **Industrial IoT (IIoT) platform with artificial intelligence** designed for real-time monitoring, predictive maintenance, and process optimization in industrial environments.

### Key Features

- **Real-time Data Collection**: Connect to PLCs, RTUs, and sensors using industrial protocols (OPC UA, Modbus, MQTT, S7)
- **Time Series Storage**: Optimized storage with InfluxDB for high-frequency industrial data
- **Interactive Dashboards**: Real-time visualization with WebSocket updates
- **Machine Learning**: Predictive maintenance, anomaly detection, and demand forecasting
- **Multi-tenant Architecture**: Support for multiple organizations and sites
- **Vertical Solutions**: SmartPort, SmartMine, SmartSteel

## Architecture

### Modular Monolith Design

OptiFlow AI uses a **Modular Monolith** architecture - a single deployable application organized into clear, independent modules with well-defined boundaries. This provides the simplicity and performance of a monolith with the organization and maintainability of microservices.

```
┌─────────────────────────────────────────────────────────────┐
│                    OptiFlow AI Platform                      │
│                    (Modular Monolith)                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ OptiFlow Core│  │  SmartPort   │  │  ML Engine   │      │
│  │              │  │              │  │              │      │
│  │ • Devices    │  │ • Vessels    │  │ • Predictive │      │
│  │ • Tags       │  │ • Berths     │  │ • Anomaly    │      │
│  │ • Timeseries │  │ • Loading    │  │ • Forecast   │      │
│  │ • Alarms     │  │ • Routes     │  │ • Optimize   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ AI Insights  │  │ Integrations │  │ Core Utils   │      │
│  │              │  │              │  │              │      │
│  │ • Patterns   │  │ • GBM API    │  │ • Database   │      │
│  │ • Trends     │  │ • Webhooks   │  │ • Cache      │      │
│  │ • RCA        │  │ • Sync       │  │ • Security   │      │
│  │ • NLG        │  │              │  │ • Logging    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────┴─────────────────┐
        ↓                                   ↓
  ┌──────────┐                      ┌──────────┐
  │ Gateway  │                      │ Frontend │
  │          │                      │          │
  │ Protocols│                      │  React   │
  │ Devices  │                      │  TypeScript│
  └──────────┘                      └──────────┘
```

**Benefits:**
- ✅ **Zero latency** between modules (direct function calls, no network overhead)
- ✅ **Shared transactions** across modules (ACID guarantees)
- ✅ **Simple deployment** (single container/process)
- ✅ **Clear boundaries** (organized by domain, easy to understand)
- ✅ **Easy testing** (modules can be tested independently)
- ✅ **Migration path** (can extract to microservices later if needed)

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
OptiFlow-AI/
├── backend/                 # FastAPI backend (Modular Monolith)
│   ├── app/
│   │   ├── core/           # ⭐ Core utilities
│   │   │   ├── config.py          # Application configuration
│   │   │   ├── database.py        # Database connections
│   │   │   ├── security.py        # Authentication/authorization
│   │   │   ├── cache.py           # Redis cache utilities
│   │   │   └── logging.py         # Structured logging
│   │   │
│   │   ├── optiflow/       # ⭐ OptiFlow Core Module (reusable base)
│   │   │   ├── api/               # Devices, Tags, Timeseries, Alarms
│   │   │   ├── models/            # SQLAlchemy models
│   │   │   ├── schemas/           # Pydantic schemas
│   │   │   ├── services/          # Business logic
│   │   │   └── websocket/         # Real-time updates
│   │   │
│   │   ├── port/           # ⭐ SmartPort Module (vertical)
│   │   │   ├── api/               # Vessels, Loading, Berths
│   │   │   ├── models/            # Vessel, Commodity, Routes
│   │   │   ├── schemas/           # Pydantic schemas
│   │   │   └── services/          # Port-specific logic
│   │   │
│   │   ├── ml/             # ⭐ ML Engine Module
│   │   │   ├── models/            # Failure, Anomaly, Forecast
│   │   │   ├── features/          # Feature engineering
│   │   │   ├── training/          # Model training
│   │   │   └── api/               # ML predictions API
│   │   │
│   │   ├── ai/             # ⭐ AI Insights Engine Module
│   │   │   ├── insights/          # Pattern detection, RCA
│   │   │   ├── nlp/               # Text generation, chatbot
│   │   │   ├── models/            # AI models
│   │   │   └── api/               # Insights API
│   │   │
│   │   ├── integrations/   # ⭐ External Integrations
│   │   │   ├── gbm/               # GBM partner integration
│   │   │   └── api/               # Webhooks
│   │   │
│   │   ├── tasks/          # Celery background tasks
│   │   ├── db/             # Database session management
│   │   └── main.py         # FastAPI application entry point
│   │
│   ├── tests/              # Organized tests by module
│   │   ├── optiflow/
│   │   ├── port/
│   │   ├── ml/
│   │   └── ai/
│   ├── alembic/            # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
│
├── gateway/                # Data collection gateway
│   ├── app/
│   │   ├── protocols/      # OPC UA, Modbus, MQTT, S7, EtherNet/IP
│   │   ├── core/           # Core functionality
│   │   └── services/       # Services
│   ├── config/
│   │   └── devices.yaml    # Device configurations
│   └── requirements.txt
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── api/            # API clients
│   │   │   ├── optiflow/          # OptiFlow APIs
│   │   │   └── port/              # SmartPort APIs
│   │   ├── pages/
│   │   │   ├── optiflow/          # OptiFlow pages
│   │   │   └── port/              # SmartPort pages
│   │   ├── components/
│   │   │   ├── common/            # Shared components
│   │   │   ├── optiflow/          # OptiFlow components
│   │   │   └── port/              # SmartPort components
│   │   ├── store/          # Redux store
│   │   │   └── slices/
│   │   │       ├── optiflow/
│   │   │       └── port/
│   │   └── hooks/          # Custom React hooks
│   ├── package.json
│   └── Dockerfile
│
├── docs/                   # Documentation
│   ├── architecture/       # Architecture docs
│   ├── api/                # API documentation
│   │   ├── optiflow/
│   │   ├── port/
│   │   └── ml/
│   ├── deployment/         # Deployment guides
│   └── development/        # Development guides
│
├── infrastructure/         # Infrastructure as Code
│   ├── docker/
│   ├── kubernetes/
│   └── terraform/
│
└── monitoring/             # Monitoring configs
    └── prometheus/
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
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - InfluxDB UI: http://localhost:8086
   - RabbitMQ Management: http://localhost:15672

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
- [API Documentation](docs/api/)
- [Deployment Guide](docs/deployment/)
- [Development Guide](docs/development/)

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
