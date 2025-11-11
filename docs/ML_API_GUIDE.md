# ML Anomaly Detection API Guide

## Overview
OptiFlow AI now includes real-time ML-based anomaly detection powered by Isolation Forest models trained on 30 days of historical industrial data.

## Trained Models

### Isolation Forest
- **Status**: ✅ Ready (trained on 200k samples)
- **Performance**: F1-Score = 0.4546, Precision = 0.4655, Recall = 0.4443
- **Model Type**: Isolation Forest (100 estimators, contamination=1.5%)
- **Features**: 10 industrial tags (motor current/speed/vibration, temperatures, pressures, level, energy, production)
- **Location**: `/app/models/isolation_forest_fast.joblib`

## API Endpoints

### 1. Get Model Information
```bash
GET /api/v1/analytics/model-info
```

**Response:**
```json
{
  "model_type": "Isolation Forest",
  "n_estimators": 100,
  "contamination": 0.015,
  "features": [
    "MOTOR_01_CURRENT",
    "MOTOR_01_SPEED",
    "MOTOR_01_VIBRATION",
    "TEMP_SENSOR_01",
    "TEMP_SENSOR_02",
    "PRESSURE_01",
    "PRESSURE_02",
    "LEVEL_TANK_01",
    "POWER_CONSUMPTION",
    "PRODUCTION_RATE"
  ],
  "status": "ready"
}
```

### 2. Detect Anomalies
```bash
GET /api/v1/analytics/anomalies
```

**Parameters:**
- `start_date` (optional): Start date in YYYY-MM-DD format (default: 7 days ago)
- `end_date` (optional): End date in YYYY-MM-DD format (default: now)
- `tag_id` (optional): Filter by specific tag (e.g., "MOTOR_01_CURRENT")
- `model_type` (optional): Model to use (default: "isolation_forest")
- `limit` (optional): Max data points to analyze (default: 1000, max: 100000)

**Example Requests:**

```bash
# Get anomalies from last 7 days
curl "http://localhost:8000/api/v1/analytics/anomalies"

# Get anomalies for specific date range
curl "http://localhost:8000/api/v1/analytics/anomalies?start_date=2025-10-10&end_date=2025-10-25&limit=1000"

# Filter by specific tag
curl "http://localhost:8000/api/v1/analytics/anomalies?tag_id=MOTOR_01_VIBRATION&start_date=2025-10-15&end_date=2025-10-20"

# Large dataset analysis
curl "http://localhost:8000/api/v1/analytics/anomalies?start_date=2025-10-01&end_date=2025-10-31&limit=10000"
```

**Response:**
```json
{
  "total_points": 1000,
  "anomalies_detected": 13,
  "anomaly_rate": 0.013,
  "model_used": "isolation_forest",
  "time_range": {
    "start": "2025-10-10T00:00:00",
    "end": "2025-10-25T00:00:00"
  },
  "anomalies": [
    {
      "timestamp": "2025-10-21T03:07:36.097670",
      "tag_id": "MOTOR_01_CURRENT",
      "value": 0.0,
      "anomaly_score": 0.516,
      "is_anomaly": true,
      "anomaly_type": "outlier"
    }
  ]
}
```

## Anomaly Score Interpretation

- **0.0 - 0.3**: Minor anomaly (borderline)
- **0.3 - 0.5**: Moderate anomaly (investigate)
- **0.5 - 0.7**: High anomaly (immediate attention)
- **0.7 - 1.0**: Critical anomaly (urgent action required)

Higher scores indicate more unusual behavior compared to historical patterns.

## Performance Considerations

1. **Query Time**: ~2-5 seconds for 1000 points, ~10-30 seconds for 10k+ points
2. **Data Sampling**: If dataset exceeds `limit`, random sampling is applied
3. **Feature Engineering**: All tag values are normalized using StandardScaler
4. **NaN Handling**: Missing values are filled with 0.0

## Training Details

### Data Source
- **InfluxDB Bucket**: `timeseries`
- **Measurement**: `tag_values`
- **Historical Period**: 30 days (Oct 1-31, 2025)
- **Total Points**: 432,000 (10 tags × 43,200 points)
- **Injected Anomalies**: 6,568 (~1.5%)

### Training Parameters
```python
IsolationForest(
    contamination=0.015,  # Expected anomaly rate
    n_estimators=100,     # Number of trees
    random_state=42,
    n_jobs=-1            # Use all CPU cores
)
```

### Feature Scaling
StandardScaler with parameters learned from training data:
- Mean normalization
- Standard deviation scaling
- Preserves relative distances

## Retraining Models

To retrain with latest data:

```bash
# Fast training (Isolation Forest only, ~30 seconds)
docker compose exec backend python scripts/train_isolation_fast.py

# Full training (Isolation Forest + LSTM, ~30-60 minutes)
docker compose exec backend python scripts/train_anomaly_models.py
```

New models are automatically saved to `/app/models/` and loaded on next API call.

## Integration Examples

### Python
```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/analytics/anomalies",
    params={
        "start_date": "2025-10-15",
        "end_date": "2025-10-20",
        "limit": 1000
    }
)
data = response.json()
print(f"Detected {data['anomalies_detected']} anomalies")
```

### JavaScript/TypeScript
```typescript
const response = await fetch(
  'http://localhost:8000/api/v1/analytics/anomalies?' +
  new URLSearchParams({
    start_date: '2025-10-15',
    end_date: '2025-10-20',
    limit: '1000'
  })
);
const data = await response.json();
console.log(`Detected ${data.anomalies_detected} anomalies`);
```

### cURL with jq
```bash
curl -s "http://localhost:8000/api/v1/analytics/anomalies?limit=1000" | \
  jq '{total: .total_points, detected: .anomalies_detected, rate: .anomaly_rate}'
```

## Troubleshooting

### No anomalies detected
- Check date range matches historical data period (Oct 1-31, 2025)
- Verify InfluxDB contains data: check bucket "timeseries"
- Try increasing `limit` parameter

### Slow queries
- Reduce `limit` parameter (start with 1000)
- Narrow date range (max 7-14 days recommended)
- Consider creating indices in InfluxDB

### Model not ready
- Run training script: `docker compose exec backend python scripts/train_isolation_fast.py`
- Check logs: `docker compose logs backend | grep -i "model"`
- Verify model files exist in `/app/models/`

## Next Steps

1. **Frontend Integration**: Create visualization page for anomalies
2. **Agent Context**: Add ML insights to autonomous agent prompts
3. **LSTM Training**: Train temporal model for better sequence anomaly detection
4. **Alert Integration**: Trigger alarms for high-score anomalies
5. **Real-time Detection**: Stream live data through model for immediate alerts

## References

- Training Scripts: `scripts/train_anomaly_models.py`, `scripts/train_isolation_fast.py`
- API Implementation: `backend/app/api/v1/endpoints/analytics.py`
- Data Generation: `scripts/generate_historical_data_simple.py`
