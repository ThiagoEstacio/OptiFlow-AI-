# OptiFlow AI - Developer Guide: Advanced Features

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Service Layer Details](#service-layer-details)
4. [Extending Features](#extending-features)
5. [Adding New Endpoints](#adding-new-endpoints)
6. [Testing Guidelines](#testing-guidelines)
7. [Deployment](#deployment)
8. [Best Practices](#best-practices)

---

## Architecture Overview

The advanced features follow a layered architecture:

```
┌─────────────────────────────────────┐
│        API Endpoints Layer          │  FastAPI routers
├─────────────────────────────────────┤
│        Service Layer                │  Business logic
├─────────────────────────────────────┤
│        Data Access Layer            │  SQLAlchemy ORM
├─────────────────────────────────────┤
│        Database Layer               │  PostgreSQL + InfluxDB
└─────────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns:** API, business logic, and data access are separated
2. **Async/Await:** Full async implementation for scalability
3. **Type Safety:** Pydantic models for request/response validation
4. **Dependency Injection:** Database sessions and services injected via FastAPI
5. **Error Handling:** Consistent error responses across all endpoints

---

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── advanced_features.py  # API endpoints
│   │       └── api.py                    # Router registration
│   ├── services/
│   │   ├── gateway_production_manager.py  # Gateway testing
│   │   ├── ml_failure_predictor.py        # ML predictions
│   │   ├── loading_optimizer.py           # Loading optimization
│   │   └── report_generator.py            # Report generation
│   ├── models/                            # SQLAlchemy models
│   ├── schemas/                           # Pydantic schemas
│   └── core/                              # Core utilities
├── tests/
│   ├── test_gateway_production_manager.py
│   ├── test_ml_failure_predictor.py
│   ├── test_loading_optimizer.py
│   ├── test_report_generator.py
│   └── test_advanced_features_api.py
├── reports/                               # Generated reports
└── models/                                # Trained ML models
```

---

## Service Layer Details

### Gateway Production Manager

**File:** `backend/app/services/gateway_production_manager.py`

**Purpose:** Test, validate, and benchmark industrial gateways.

#### Key Methods:

```python
class GatewayProductionManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def test_gateway_connection(
        self,
        gateway_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Test gateway connection with performance benchmarking.

        Args:
            gateway_config: Gateway configuration dictionary

        Returns:
            Test results with performance metrics
        """

    async def validate_configuration(
        self,
        gateway_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate gateway configuration against best practices.

        Returns:
            Validation results with errors and warnings
        """

    async def benchmark_gateway(
        self,
        gateway_id: int,
        duration_seconds: int = 60
    ) -> Dict[str, Any]:
        """
        Benchmark gateway performance under load.

        Returns:
            Performance metrics (reads/sec, latency, etc.)
        """
```

#### Extending:

To add a new protocol (e.g., EtherNet/IP):

1. Update `create_production_config_template()`:
```python
async def create_production_config_template(self, gateway_type: str) -> Dict[str, Any]:
    # ... existing code ...
    elif gateway_type == "ethernet_ip":
        return {
            "protocol": "ethernet_ip",
            "host": "192.168.1.100",
            "port": 44818,
            "slot": 0,
            "tags": [
                {
                    "name": "Tag_1",
                    "tag": "Program:MainProgram.Tag1",
                    "data_type": "DINT"
                }
            ]
        }
```

2. Update validation logic in `validate_configuration()`

3. Add tests in `tests/test_gateway_production_manager.py`

---

### ML Failure Predictor

**File:** `backend/app/services/ml_failure_predictor.py`

**Purpose:** Train ML models and predict equipment failures.

#### Architecture:

```python
class MLFailurePredictor:
    MODEL_DIR = "models"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def train_model(
        self,
        asset_type: Optional[str] = None,
        training_days: int = 180
    ) -> Dict[str, Any]:
        """Train RandomForest model on historical data."""

    async def predict_failure(
        self,
        asset_id: str,
        prediction_horizon_hours: int = 24
    ) -> Dict[str, Any]:
        """Predict failure probability for specific asset."""

    def _extract_features(self, asset: Asset) -> List[float]:
        """Extract 8 features from asset."""

    def _calculate_risk_level(self, probability: float) -> str:
        """Calculate risk level from probability."""

    def _generate_recommendations(
        self,
        risk_level: str,
        hours_to_failure: float
    ) -> List[str]:
        """Generate actionable recommendations."""
```

#### Current Features:

1. health_score
2. alarm_severity
3. operating_hours_ratio
4. vibration_level
5. temperature
6. load_percentage
7. days_since_maintenance
8. recent_alarm_count

#### Adding New Features:

To add a new feature (e.g., humidity):

1. **Update feature extraction:**
```python
def _extract_features(self, asset: Asset) -> List[float]:
    features = [
        # ... existing features ...
        asset.humidity or 0.0,  # NEW FEATURE
    ]
    return features
```

2. **Update training data collection:**
```python
async def train_model(self, ...):
    # Add humidity to training data collection
    # Update X to include 9 features instead of 8
```

3. **Update documentation:**
   - API docs
   - User manual
   - Feature importance analysis

4. **Retrain all models** with new feature

---

### Loading Optimizer

**File:** `backend/app/services/loading_optimizer.py`

**Purpose:** Optimize berth allocation and loading operations.

#### Key Algorithms:

**1. Berth Allocation (Greedy Algorithm):**

```python
async def optimize_berth_allocation(
    self,
    site_id: int,
    days_ahead: int = 7
) -> Dict[str, Any]:
    """
    Algorithm:
    1. Get all scheduled ships (sorted by arrival time)
    2. Get all available berths
    3. For each ship:
       a. Find berth with earliest availability
       b. Allocate ship to that berth
       c. Update berth availability
    4. Calculate metrics (waiting time, utilization)
    """
```

**2. Loading Sequence Optimization:**

```python
async def optimize_loading_sequence(
    self,
    ship_loading_id: int
) -> Dict[str, Any]:
    """
    Algorithm:
    1. Get ship details (product type, tonnage)
    2. Find available silos with matching product
    3. Sort silos by loading rate (descending)
    4. Greedy selection: use highest rate silos first
    5. Generate timeline
    """
```

**3. Optimal Loading Rate:**

```python
async def calculate_optimal_loading_rate(
    self,
    ship_loading_id: int,
    current_weather: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Algorithm:
    1. Start with base rate (1200 t/h)
    2. Apply weather adjustments:
       - Wind > 60 km/h: -50%
       - Wind 40-60 km/h: -30%
       - Rainfall > 5mm: -20%
    3. Apply product/ship adjustments
    4. Return optimal rate with recommendations
    """
```

#### Extending with Better Algorithms:

**Replace greedy with linear programming:**

```python
from scipy.optimize import linprog

async def optimize_berth_allocation_lp(
    self,
    site_id: int,
    days_ahead: int = 7
) -> Dict[str, Any]:
    """
    Use linear programming for optimal allocation.

    Objective: Minimize total waiting time
    Constraints:
    - Each ship assigned to exactly one berth
    - No berth overlap
    - Ship arrival times
    """

    # Get ships and berths
    ships = await self._get_scheduled_ships(site_id, days_ahead)
    berths = await self._get_available_berths(site_id)

    # Build constraint matrix
    # A_eq, b_eq for equality constraints
    # A_ub, b_ub for inequality constraints

    # Solve
    result = linprog(c, A_eq=A_eq, b_eq=b_eq, A_ub=A_ub, b_ub=b_ub)

    # Parse and return solution
    return self._parse_lp_solution(result, ships, berths)
```

---

### Report Generator

**File:** `backend/app/services/report_generator.py`

**Purpose:** Generate PDF and Excel reports.

#### Technology Stack:

- **PDF:** reportlab (SimpleDocTemplate, Table, Paragraph)
- **Excel:** openpyxl (Workbook, sheets, formatting)

#### Key Methods:

```python
class ReportGenerator:
    REPORTS_DIR = "reports"

    async def generate_daily_operations_pdf(
        self,
        site_id: int,
        operation_date: date
    ) -> str:
        """Generate PDF report for single day."""

    async def generate_daily_operations_excel(
        self,
        site_id: int,
        start_date: date,
        end_date: date
    ) -> str:
        """Generate Excel report for date range."""
```

#### Adding New Report Types:

**Example: Monthly Summary PDF**

```python
async def generate_monthly_summary_pdf(
    self,
    site_id: int,
    year: int,
    month: int
) -> str:
    """Generate monthly summary report."""

    # 1. Collect data
    trucks_monthly = await self._get_monthly_trucks(site_id, year, month)
    ships_monthly = await self._get_monthly_ships(site_id, year, month)

    # 2. Calculate statistics
    stats = self._calculate_monthly_stats(trucks_monthly, ships_monthly)

    # 3. Create PDF
    filename = f"{self.REPORTS_DIR}/monthly_summary_{year}{month:02d}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)

    # 4. Build content
    story = []

    # Title
    story.append(Paragraph(f"Monthly Summary - {year}/{month}", styles['Title']))

    # Statistics table
    stats_data = [
        ["Metric", "Value"],
        ["Total Trucks", stats['total_trucks']],
        ["Total Tonnage", f"{stats['total_tonnage']:,.0f} tons"],
        ["Total Ships", stats['total_ships']],
        ["Avg Trucks/Day", f"{stats['avg_trucks_per_day']:.1f}"],
    ]

    table = Table(stats_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    story.append(table)

    # Charts (if using reportlab-graphics)
    # story.append(self._create_monthly_chart(stats))

    # 5. Build PDF
    doc.build(story)

    return filename
```

---

## Adding New Endpoints

### Step-by-Step Guide

**Example: Add weather integration endpoint**

#### 1. Create Service Method

`backend/app/services/weather_service.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import httpx

class WeatherService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.api_key = "YOUR_API_KEY"  # From config

    async def get_current_weather(
        self,
        site_id: int
    ) -> Dict[str, Any]:
        """Get current weather for site location."""

        # Get site coordinates
        site = await self.db.get(Site, site_id)
        if not site:
            return {"status": "error", "error": "Site not found"}

        # Call weather API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.weather.com/v1/current",
                params={
                    "lat": site.latitude,
                    "lon": site.longitude,
                    "apiKey": self.api_key
                }
            )

        if response.status_code != 200:
            return {"status": "error", "error": "Weather API error"}

        data = response.json()

        return {
            "status": "success",
            "site_id": site_id,
            "temperature_c": data["temperature"],
            "wind_speed_kmh": data["wind_speed"],
            "rainfall_mm": data["rainfall"],
            "humidity_percent": data["humidity"],
            "timestamp": data["timestamp"]
        }
```

#### 2. Create Pydantic Schema

`backend/app/schemas/weather.py`:

```python
from pydantic import BaseModel
from datetime import datetime

class WeatherResponse(BaseModel):
    status: str
    site_id: int
    temperature_c: float
    wind_speed_kmh: float
    rainfall_mm: float
    humidity_percent: float
    timestamp: datetime

    class Config:
        from_attributes = True
```

#### 3. Add API Endpoint

`backend/app/api/v1/endpoints/advanced_features.py`:

```python
from app.services.weather_service import WeatherService
from app.schemas.weather import WeatherResponse

@router.get("/weather/{site_id}", response_model=WeatherResponse)
async def get_site_weather(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current weather for a site."""

    try:
        service = WeatherService(db)
        result = await service.get_current_weather(site_id)
        logger.info(f"Weather fetched for site {site_id}")
        return result
    except Exception as e:
        logger.error(f"Error fetching weather: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### 4. Add Tests

`backend/tests/test_weather_service.py`:

```python
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_get_current_weather(test_db, test_site):
    """Test weather service returns current weather."""

    service = WeatherService(test_db)

    # Mock external API
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "temperature": 25.0,
            "wind_speed": 15.0,
            "rainfall": 0.0,
            "humidity": 65.0,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        mock_get.return_value = mock_response

        result = await service.get_current_weather(test_site.id)

    assert result["status"] == "success"
    assert result["temperature_c"] == 25.0
    assert result["wind_speed_kmh"] == 15.0
```

#### 5. Update Documentation

Add to `docs/API_ADVANCED_FEATURES.md`:

```markdown
### GET /weather/{site_id}

Get current weather conditions for a site.

**Response:**
```json
{
  "status": "success",
  "site_id": 1,
  "temperature_c": 25.0,
  "wind_speed_kmh": 15.0,
  "rainfall_mm": 0.0,
  "humidity_percent": 65.0,
  "timestamp": "2024-01-01T12:00:00Z"
}
```
````

---

## Testing Guidelines

### Test Structure

Follow the existing test pattern:

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, Mock, AsyncMock

# Unit tests
@pytest.mark.asyncio
async def test_service_method_success(test_db: AsyncSession):
    """Test successful operation."""
    service = YourService(test_db)
    result = await service.your_method()
    assert result["status"] == "success"

# Integration tests
@pytest.mark.asyncio
async def test_api_endpoint(client: AsyncClient, auth_headers):
    """Test API endpoint returns correct response."""
    response = await client.get(
        "/api/v1/advanced/your-endpoint",
        headers=auth_headers
    )
    assert response.status_code == 200
```

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_ml_failure_predictor.py

# Specific test
pytest tests/test_ml_failure_predictor.py::test_predict_failure_success

# With coverage
pytest --cov=app --cov-report=html

# Parallel execution
pytest -n auto
```

### Test Coverage Requirements

- **Minimum:** 80% coverage for all new code
- **Service Layer:** 90%+ coverage
- **API Endpoints:** 100% coverage (all status codes)
- **Critical paths:** 100% coverage (payments, security, etc.)

---

## Deployment

### Environment Variables

Add to `.env`:

```bash
# ML Settings
ML_MODEL_DIR=models
ML_MIN_TRAINING_SAMPLES=100
ML_DEFAULT_TRAINING_DAYS=180

# Report Settings
REPORTS_DIR=reports
REPORTS_MAX_DATE_RANGE_DAYS=30

# Weather API (if integrated)
WEATHER_API_KEY=your_api_key
WEATHER_API_URL=https://api.weather.com/v1

# Performance
GATEWAY_BENCHMARK_MAX_DURATION=300
LOADING_OPTIMIZER_CACHE_TTL=3600
```

### Dependencies

Update `requirements.txt`:

```txt
# Existing dependencies...

# Report generation
reportlab==4.0.7
openpyxl==3.1.2

# ML (already included)
scikit-learn==1.3.2

# Optional: Better optimization
scipy==1.11.4  # For linear programming
```

### Database Migrations

If you add new models:

```bash
# Create migration
alembic revision --autogenerate -m "Add weather data model"

# Review migration file
# backend/alembic/versions/xxx_add_weather_data_model.py

# Apply migration
alembic upgrade head
```

### Docker Deployment

Update `Dockerfile` if needed:

```dockerfile
# Install system dependencies for reportlab
RUN apt-get update && apt-get install -y \
    libpq-dev \
    libjpeg-dev \  # For PDF images
    && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /app/reports /app/models
RUN chmod 777 /app/reports /app/models
```

---

## Best Practices

### Code Style

1. **Follow PEP 8:** Use black formatter
2. **Type hints:** All function signatures
3. **Docstrings:** Google style
4. **Async/await:** Use consistently

```python
async def example_function(
    param1: int,
    param2: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Brief description of function.

    Args:
        param1: Description of param1
        param2: Description of param2
        db: Database session

    Returns:
        Dictionary containing result data

    Raises:
        ValueError: If param1 is negative
        HTTPException: If database error occurs
    """
    pass
```

### Error Handling

```python
# Good: Specific exceptions, proper logging
try:
    result = await service.method()
except ValueError as e:
    logger.warning(f"Invalid input: {str(e)}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")

# Bad: Catching all exceptions without logging
try:
    result = await service.method()
except:
    return {"error": "Something went wrong"}
```

### Performance

1. **Use async/await** throughout
2. **Batch database queries** when possible
3. **Cache expensive operations:**

```python
from functools import lru_cache
from datetime import datetime, timedelta

class OptimizationCache:
    def __init__(self):
        self._cache = {}

    async def get_berth_allocation(
        self,
        site_id: int,
        days_ahead: int
    ) -> Optional[Dict]:
        """Get cached result if fresh."""
        cache_key = f"berth_{site_id}_{days_ahead}"

        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            # Cache valid for 1 hour
            if datetime.utcnow() - timestamp < timedelta(hours=1):
                return result

        return None

    async def set_berth_allocation(
        self,
        site_id: int,
        days_ahead: int,
        result: Dict
    ):
        """Cache result."""
        cache_key = f"berth_{site_id}_{days_ahead}"
        self._cache[cache_key] = (result, datetime.utcnow())
```

### Security

1. **Always require authentication:**

```python
@router.get("/sensitive-data")
async def get_data(
    current_user: User = Depends(get_current_user)  # Required
):
    pass
```

2. **Validate all inputs:**

```python
from pydantic import BaseModel, validator

class GatewayConfig(BaseModel):
    host: str
    port: int

    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be 1-65535')
        return v
```

3. **Sanitize user input** before logging or displaying

4. **Don't expose internal errors** to API responses

---

## Useful Resources

### Documentation

- **FastAPI:** https://fastapi.tiangolo.com/
- **SQLAlchemy:** https://docs.sqlalchemy.org/
- **Pydantic:** https://docs.pydantic.dev/
- **pytest:** https://docs.pytest.org/

### Tools

- **Black:** Code formatter
- **mypy:** Static type checker
- **pytest-cov:** Coverage reporting
- **Postman:** API testing

### Internal Links

- [API Documentation](./API_ADVANCED_FEATURES.md)
- [User Manual](./USER_MANUAL_ADVANCED_FEATURES.md)
- [Architecture Docs](./ARCHITECTURE.md)
- [Contributing Guide](./CONTRIBUTING.md)

---

## Support

For development questions:
- **Slack:** #optiflow-dev
- **Email:** dev@optiflow.ai
- **Wiki:** https://wiki.optiflow.ai

---

**Version:** 1.0
**Last Updated:** January 2024
**© 2024 OptiFlow AI. All rights reserved.**
