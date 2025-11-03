# Advanced Features API Documentation

## Overview

This document provides comprehensive documentation for the Advanced Features API endpoints implemented in OptiFlow AI. These endpoints provide production-ready tools for gateway testing, ML-based failure prediction, loading optimization, report generation, and mobile access.

**Base URL:** `/api/v1/advanced`

**Authentication:** All endpoints require Bearer token authentication.

---

## Table of Contents

1. [Gateway Production Tools](#gateway-production-tools)
2. [ML Failure Prediction](#ml-failure-prediction)
3. [Loading Optimization](#loading-optimization)
4. [Report Generation](#report-generation)
5. [Mobile Endpoints](#mobile-endpoints)
6. [Error Handling](#error-handling)

---

## Gateway Production Tools

Test and validate industrial gateway configurations before deploying to production.

### POST /gateway/test

Test a gateway connection with performance benchmarking.

**Request Body:**
```json
{
  "name": "Production Gateway 1",
  "protocol": "opcua",
  "host": "192.168.1.100",
  "port": 4840,
  "tags": [
    {
      "name": "Temperature",
      "node_id": "ns=2;s=Temperature",
      "data_type": "FLOAT"
    }
  ]
}
```

**Response (Success):**
```json
{
  "status": "success",
  "connection_successful": true,
  "performance": {
    "connection_time_ms": 125,
    "average_read_time_ms": 45,
    "reads_per_second": 22,
    "success_rate": 100
  },
  "reliability": {
    "reconnection_successful": true,
    "reconnection_time_ms": 85
  }
}
```

**Response (Failure):**
```json
{
  "status": "error",
  "connection_successful": false,
  "error": "Connection refused: host unreachable"
}
```

---

### POST /gateway/validate

Validate gateway configuration against best practices.

**Request Body:**
```json
{
  "name": "Gateway Name",
  "protocol": "modbus_tcp",
  "host": "192.168.1.100",
  "port": 502,
  "tags": [
    {
      "name": "Pressure",
      "address": "40001",
      "data_type": "FLOAT"
    }
  ]
}
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Security is not enabled. Consider enabling authentication for production use.",
    "No timeout configured. Consider setting connection timeout."
  ],
  "tag_count": 1,
  "best_practices": {
    "security_enabled": false,
    "timeout_configured": false,
    "retry_policy": false
  }
}
```

**Validation Rules:**
- Required fields: name, protocol, host, port
- Valid protocols: opcua, modbus_tcp, siemens_s7, rockwell
- Port range: 1-65535
- Tags must have unique names

---

### GET /gateway/benchmark/{gateway_id}

Benchmark an existing gateway's performance under load.

**Query Parameters:**
- `duration_seconds` (optional, default=60): Duration of benchmark test (30-300)

**Response:**
```json
{
  "status": "success",
  "gateway_id": 123,
  "benchmark_duration_seconds": 60,
  "read_count": 1320,
  "success_rate": 98.5,
  "average_read_time_ms": 42,
  "min_read_time_ms": 35,
  "max_read_time_ms": 125,
  "reads_per_second": 22
}
```

---

### GET /gateway/template/{gateway_type}

Get a production-ready configuration template.

**Path Parameters:**
- `gateway_type`: opcua | modbus_tcp | siemens_s7 | rockwell

**Response (OPC-UA):**
```json
{
  "name": "OPC-UA Gateway Template",
  "protocol": "opcua",
  "host": "192.168.1.100",
  "port": 4840,
  "security": {
    "enabled": true,
    "mode": "SignAndEncrypt",
    "policy": "Basic256Sha256"
  },
  "tags": [
    {
      "name": "Temperature_1",
      "node_id": "ns=2;s=Temperature",
      "data_type": "FLOAT",
      "scan_rate_ms": 1000
    }
  ],
  "connection": {
    "timeout_ms": 5000,
    "retry_attempts": 3,
    "retry_delay_ms": 1000
  }
}
```

---

## ML Failure Prediction

Predict equipment failures using machine learning models.

### POST /ml/train

Train an ML model using historical data.

**Query Parameters:**
- `asset_type` (optional): Filter training data by asset type (conveyor, silo, loader, etc.)
- `training_days` (optional, default=180): Days of historical data to use (30-365)

**Response:**
```json
{
  "status": "success",
  "asset_type": "conveyor",
  "training_days": 180,
  "train_accuracy": 0.92,
  "test_accuracy": 0.88,
  "model_file": "models/failure_predictor_conveyor_20240101.pkl",
  "training_samples": 1250,
  "features_used": 8,
  "trained_at": "2024-01-01T12:00:00Z"
}
```

**Features Used:**
1. health_score
2. alarm_severity
3. operating_hours_ratio
4. vibration_level
5. temperature
6. load_percentage
7. days_since_maintenance
8. recent_alarm_count

---

### GET /ml/predict/{asset_id}

Predict if an asset will fail within the specified time horizon.

**Path Parameters:**
- `asset_id`: UUID or asset identifier

**Query Parameters:**
- `prediction_horizon_hours` (optional, default=24): Time horizon for prediction (1-168)

**Response:**
```json
{
  "status": "success",
  "asset_id": "CONV-001",
  "asset_name": "Conveyor Belt 1",
  "prediction_horizon_hours": 24,
  "failure_probability": 0.72,
  "will_fail": true,
  "confidence": 0.88,
  "risk_level": "high",
  "estimated_hours_to_failure": 18,
  "recommendations": [
    "Schedule maintenance within the next 24 hours",
    "Reduce operating load by 30%",
    "Monitor vibration levels closely",
    "Prepare replacement parts"
  ],
  "contributing_factors": {
    "high_vibration": 0.35,
    "low_health_score": 0.25,
    "overdue_maintenance": 0.20,
    "recent_alarms": 0.15,
    "high_load": 0.05
  }
}
```

**Risk Levels:**
- **critical** (≥80%): Immediate action required
- **high** (≥60%): Schedule maintenance within 24 hours
- **medium** (≥40%): Monitor closely, plan maintenance
- **low** (<40%): Continue normal operations

---

## Loading Optimization

Optimize ship loading operations for maximum efficiency.

### GET /optimize/berths/{site_id}

Optimize berth allocation for scheduled ships using greedy algorithm.

**Query Parameters:**
- `days_ahead` (optional, default=7): Number of days to optimize (1-30)

**Response:**
```json
{
  "status": "success",
  "site_id": 1,
  "days_ahead": 7,
  "allocations": [
    {
      "ship_id": "abc-123",
      "ship_name": "MV Atlantic",
      "berth_id": 1,
      "berth_name": "Berth 1",
      "scheduled_arrival": "2024-01-05T08:00:00Z",
      "allocated_start": "2024-01-05T08:00:00Z",
      "allocated_end": "2024-01-06T14:00:00Z",
      "estimated_duration_hours": 30,
      "waiting_hours": 0
    },
    {
      "ship_id": "def-456",
      "ship_name": "MV Pacific",
      "berth_id": 1,
      "berth_name": "Berth 1",
      "scheduled_arrival": "2024-01-05T12:00:00Z",
      "allocated_start": "2024-01-06T14:00:00Z",
      "allocated_end": "2024-01-07T18:00:00Z",
      "estimated_duration_hours": 28,
      "waiting_hours": 26
    }
  ],
  "total_waiting_hours": 26,
  "berth_utilization_percent": 78.5,
  "optimization_algorithm": "greedy"
}
```

---

### GET /optimize/loading/{ship_loading_id}

Optimize loading sequence (silo selection, order, timeline).

**Response:**
```json
{
  "status": "success",
  "ship_loading_id": "abc-123",
  "ship_name": "MV Atlantic",
  "product_type": "soybean",
  "total_tonnage": 50000,
  "loading_sequence": [
    {
      "sequence": 1,
      "silo_id": 3,
      "silo_name": "Silo 3",
      "tonnage": 8000,
      "loading_rate_tons_per_hour": 1200,
      "estimated_hours": 6.67,
      "start_time": "2024-01-05T08:00:00Z",
      "end_time": "2024-01-05T14:40:00Z"
    },
    {
      "sequence": 2,
      "silo_id": 1,
      "silo_name": "Silo 1",
      "tonnage": 10000,
      "loading_rate_tons_per_hour": 1100,
      "estimated_hours": 9.09,
      "start_time": "2024-01-05T14:40:00Z",
      "end_time": "2024-01-05T23:45:00Z"
    }
  ],
  "total_estimated_hours": 42.5,
  "timeline": {
    "start": "2024-01-05T08:00:00Z",
    "end": "2024-01-07T02:30:00Z"
  },
  "optimization_criteria": "maximize_loading_rate"
}
```

---

### POST /optimize/loading-rate/{ship_loading_id}

Calculate optimal loading rate based on current conditions.

**Request Body (Optional):**
```json
{
  "wind_speed_kmh": 45.0,
  "rainfall_mm": 2.0,
  "temperature_c": 25.0,
  "visibility_km": 8.0
}
```

**Response:**
```json
{
  "status": "success",
  "ship_loading_id": "abc-123",
  "base_loading_rate": 1200,
  "optimal_loading_rate": 840,
  "reduction_percent": 30,
  "adjustments": [
    "Wind speed 45 km/h: -30% reduction",
    "Rainfall 2mm: No adjustment (threshold not exceeded)"
  ],
  "limiting_factors": [
    "Wind speed (moderate)"
  ],
  "safe_to_load": true,
  "recommendations": [
    "Reduce loading rate to 840 tons/hour",
    "Monitor wind conditions continuously",
    "Be prepared to pause if wind exceeds 60 km/h"
  ]
}
```

**Weather Adjustments:**
- Wind > 60 km/h: -50%
- Wind 40-60 km/h: -30%
- Rainfall > 5mm: -20%

---

## Report Generation

Generate professional PDF and Excel reports.

### GET /reports/daily-pdf

Generate daily operations PDF report.

**Query Parameters:**
- `site_id` (required): Site identifier
- `operation_date` (required): Date in ISO format (YYYY-MM-DD)

**Response:**
```json
{
  "status": "success",
  "filename": "reports/daily_operations_20240105.pdf",
  "file_size_bytes": 45678,
  "generation_time_ms": 1250,
  "report_date": "2024-01-05",
  "sections": [
    "Summary",
    "Truck Entries",
    "Ship Loadings"
  ]
}
```

**PDF Contents:**
- Header with site name and date
- Summary table (total trucks, tonnage, ships)
- Detailed truck entries table
- Detailed ship loadings table
- Professional formatting with borders and colors

---

### GET /reports/operations-excel

Generate multi-sheet operations Excel report for date range.

**Query Parameters:**
- `site_id` (required): Site identifier
- `start_date` (required): Start date in ISO format
- `end_date` (required): End date in ISO format

**Response:**
```json
{
  "status": "success",
  "filename": "reports/operations_20240101_20240107.xlsx",
  "file_size_bytes": 128456,
  "generation_time_ms": 2100,
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-07"
  },
  "sheets": [
    "Summary",
    "Caminhões",
    "Navios"
  ],
  "total_records": {
    "trucks": 245,
    "ships": 12
  }
}
```

**Excel Sheets:**
1. **Summary:** Daily aggregated data
2. **Caminhões:** Detailed truck entry records
3. **Navios:** Detailed ship loading records

---

## Mobile Endpoints

Lightweight endpoints optimized for mobile devices.

### GET /mobile/summary/{site_id}

Get mobile-optimized dashboard summary.

**Response:**
```json
{
  "site_id": 1,
  "site_name": "Santos Port Terminal",
  "timestamp": "2024-01-05T14:30:00Z",
  "trucks": {
    "active": 12,
    "completed_today": 45,
    "total_tonnage_today": 1350000
  },
  "ships": {
    "loading": 2,
    "scheduled": 3,
    "completed_today": 0
  },
  "alerts": {
    "critical": 1,
    "warning": 3
  },
  "weather": {
    "wind_kmh": 25,
    "rainfall_mm": 0,
    "status": "good"
  }
}
```

---

### GET /mobile/ship-status/{ship_loading_id}

Get mobile-optimized ship loading status.

**Response:**
```json
{
  "ship_id": "abc-123",
  "ship_name": "MV Atlantic",
  "status": "loading",
  "progress_percent": 65,
  "estimated_tonnage": 50000,
  "loaded_tonnage": 32500,
  "remaining_tonnage": 17500,
  "loading_rate_current": 1050,
  "eta_completion": "2024-01-06T14:30:00Z",
  "hours_remaining": 16.5,
  "current_silo": "Silo 2",
  "alerts": []
}
```

---

## Error Handling

All endpoints follow a consistent error response format.

### Standard Error Response

```json
{
  "status": "error",
  "error": "Error message description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-05T14:30:00Z"
}
```

### HTTP Status Codes

- **200 OK:** Request successful
- **400 Bad Request:** Invalid request parameters
- **401 Unauthorized:** Authentication required or failed
- **404 Not Found:** Resource not found
- **422 Unprocessable Entity:** Validation error
- **500 Internal Server Error:** Server error
- **501 Not Implemented:** Feature requires additional dependencies

### Common Error Codes

- `INVALID_CONFIGURATION`: Gateway configuration validation failed
- `MODEL_NOT_FOUND`: ML model not trained yet
- `ASSET_NOT_FOUND`: Asset ID does not exist
- `SHIP_NOT_FOUND`: Ship loading ID not found
- `NO_BERTHS_AVAILABLE`: No berths available at site
- `DEPENDENCY_MISSING`: Required library not installed (e.g., scikit-learn)

---

## Rate Limiting

All endpoints are subject to rate limiting:
- **Default:** 100 requests per minute per user
- **Heavy operations** (training, reports): 10 requests per minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1641398400
```

---

## Examples

### Example 1: Complete ML Prediction Workflow

```bash
# 1. Train the model
curl -X POST "https://api.example.com/api/v1/advanced/ml/train?training_days=180" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. Predict failure for specific asset
curl -X GET "https://api.example.com/api/v1/advanced/ml/predict/CONV-001?prediction_horizon_hours=24" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Example 2: Optimize Loading Operations

```bash
# 1. Optimize berth allocation
curl -X GET "https://api.example.com/api/v1/advanced/optimize/berths/1?days_ahead=7" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. Optimize loading sequence for ship
curl -X GET "https://api.example.com/api/v1/advanced/optimize/loading/abc-123" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. Calculate optimal loading rate with weather
curl -X POST "https://api.example.com/api/v1/advanced/optimize/loading-rate/abc-123" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"wind_speed_kmh": 45, "rainfall_mm": 0}'
```

### Example 3: Generate Reports

```bash
# 1. Generate daily PDF
curl -X GET "https://api.example.com/api/v1/advanced/reports/daily-pdf?site_id=1&operation_date=2024-01-05" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. Generate weekly Excel
curl -X GET "https://api.example.com/api/v1/advanced/reports/operations-excel?site_id=1&start_date=2024-01-01&end_date=2024-01-07" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Support

For API support:
- Email: support@optiflow.ai
- Documentation: https://docs.optiflow.ai
- GitHub Issues: https://github.com/your-org/optiflow/issues
