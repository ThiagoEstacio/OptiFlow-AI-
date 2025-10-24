# OptiFlow AI Platform - Architecture

## Overview

This document describes the architecture of the OptiFlow AI Platform.

## System Components

### 1. Backend Core
- **Technology**: FastAPI + Python 3.11+
- **Purpose**: REST API, WebSocket, Business Logic
- **Database**: PostgreSQL (relational), InfluxDB (time series), Redis (cache)

### 2. Gateway
- **Technology**: Python 3.11+
- **Purpose**: Industrial protocol connectivity
- **Protocols**: OPC UA, Modbus TCP/RTU, MQTT, S7, EtherNet/IP

### 3. Frontend
- **Technology**: React 18 + TypeScript + Vite
- **Purpose**: User interface and data visualization
- **Features**: Real-time dashboards, analytics, configuration

### 4. ML Engine
- **Technology**: scikit-learn, XGBoost, MLflow
- **Purpose**: Predictive maintenance, anomaly detection, optimization

## Data Flow

```
FIELD → Gateway → Backend API → Database → Frontend
  |         |          |            |          |
PLCs    Protocols   REST/WS     InfluxDB   React
              |          |        PostgreSQL   |
           Buffer    Celery       Redis      Web
```

## Security

- JWT authentication
- Role-based access control (RBAC)
- HTTPS/WSS encryption
- API rate limiting

## Scalability

- Horizontal scaling for backend
- Multiple gateways per site
- Database replication
- Redis clustering

For more details, see the complete architecture documentation.
