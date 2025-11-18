# 🔧 PATCH PARA CONECTAR DATASERVICE AO INFLUXDB REAL

## Arquivo: backend/app/services/data_service.py

### 1. Adicionar imports no topo (linha 15):

```python
from influxdb_client import InfluxDBClient
from app.core.config import settings
```

### 2. Modificar __init__ do DataService (linha ~26):

```python
def __init__(self, db: AsyncSession):
    """Initialize with async session and InfluxDB client"""
    self.db = db
    
    # Initialize InfluxDB client
    try:
        self.influx_client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG,
            timeout=10000
        )
        self.query_api = self.influx_client.query_api()
        logger.info("✅ InfluxDB client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize InfluxDB client: {e}")
        self.influx_client = None
        self.query_api = None
```

### 3. Substituir método get_historical_data (linha ~113):

REMOVER TODO O BLOCO DE:
- Linha 113: `async def get_historical_data(`
- Até linha ~230: Final do método (antes de `async def calculate_statistics`)

SUBSTITUIR POR:

```python
async def get_historical_data(
    self, 
    tag_id: str, 
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    duration: str = "1h",
    aggregation: Optional[str] = None,
    interval: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get historical data from InfluxDB (REAL DATA)
    
    Args:
        tag_id: Tag identifier (e.g., "ELEV01_TEMP_C_PV")
        start_time: Start of time range
        end_time: End of time range (default: now)
        duration: Alternative to start_time, e.g. "1h", "24h", "7d"
        aggregation: Aggregation function (mean, max, min, sum, stddev)
        interval: Aggregation interval (e.g., "5m", "1h")
        
    Returns:
        Dict with historical data points from InfluxDB
    """
    try:
        # Calculate time range
        if not end_time:
            end_time = datetime.now()
        
        if not start_time:
            if duration:
                # Parse duration string (e.g., "1h", "24h", "7d")
                value = int(duration[:-1])
                unit = duration[-1]
                if unit == 'h':
                    start_time = end_time - timedelta(hours=value)
                elif unit == 'd':
                    start_time = end_time - timedelta(days=value)
                else:
                    start_time = end_time - timedelta(hours=1)
            else:
                start_time = end_time - timedelta(hours=1)
        
        # Check if InfluxDB client is available
        if not self.query_api:
            logger.warning("⚠️ InfluxDB not available, returning empty data")
            return {
                "tag_id": tag_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "data_points": [],
                "count": 0,
                "error": "InfluxDB not available"
            }
        
        # Build Flux query to get data from InfluxDB
        # Data is stored as: measurement="sensor_data", tag="tag_id", field="value"
        flux_query = f'''
from(bucket: "{settings.INFLUXDB_BUCKET}")
  |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
  |> filter(fn: (r) => r["_measurement"] == "sensor_data")
  |> filter(fn: (r) => r["tag_id"] == "{tag_id}")
  |> filter(fn: (r) => r["_field"] == "value")
  |> sort(columns: ["_time"])
        '''
        
        if aggregation and interval:
            # Apply aggregation if requested (e.g., mean over 5m windows)
            flux_query += f'''
  |> aggregateWindow(every: {interval}, fn: {aggregation}, createEmpty: false)
            '''
        
        logger.info(f"🔍 Querying InfluxDB for {tag_id} from {start_time} to {end_time}")
        
        # Execute query
        result = self.query_api.query(query=flux_query)
        
        data_points = []
        for table in result:
            for record in table.records:
                data_points.append({
                    "timestamp": record.get_time().isoformat(),
                    "value": float(record.get_value()),
                    "quality": record.values.get("quality", "good")
                })
        
        logger.info(f"✅ Retrieved {len(data_points)} points for {tag_id}")
        
        return {
            "tag_id": tag_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "data_points": data_points,
            "count": len(data_points)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting historical data for {tag_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "tag_id": tag_id,
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
            "error": str(e),
            "data_points": [],
            "count": 0
        }
```

### 4. Verificar settings (backend/app/core/config.py):

Confirmar que existem estas variáveis:

```python
# InfluxDB Configuration
INFLUXDB_URL: str = "http://localhost:8086"
INFLUXDB_TOKEN: str = "my-super-secret-influxdb-token"
INFLUXDB_ORG: str = "optiflow"
INFLUXDB_BUCKET: str = "timeseries"
```

### 5. Após fazer as mudanças:

```bash
# Reiniciar backend
docker-compose restart backend

# Ver logs
docker-compose logs -f backend | grep -i "influx\|historical\|agent"

# Testar
python3 scripts/test_agent_api.py
```

---

## Teste Manual com curl:

```bash
# Testar endpoint direto do DataService (se exposto)
curl -X POST http://localhost:8000/api/v1/agent/dashboard/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Qual foi a temperatura média do ELEV01 nas últimas 24 horas?"}'
```

Deve retornar algo como:
```
"Média: 72.45°C"
"Máximo: 85.12°C"
"Mínimo: 60.34°C"
```

Não mais "não há dados disponíveis".

---

## Alternativa Rápida (Se tiver pressa):

Use o script que já criei:

```bash
# Ver o script completo
cat scripts/populate_influxdb_historical.py

# Copiar a lógica de consulta dele e adaptar para DataService
```

A query Flux que funciona:
```flux
from(bucket: "timeseries")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "sensor_data")
  |> filter(fn: (r) => r["tag_id"] == "ELEV01_TEMP_C_PV")
  |> filter(fn: (r) => r["_field"] == "value")
```

---

## Debugging:

Se ainda retornar "no data available":

1. Verificar logs do backend:
```bash
docker-compose logs backend | tail -100
```

2. Testar query diretamente no InfluxDB:
```bash
curl -X POST 'http://localhost:8086/api/v2/query?org=optiflow' \
  -H 'Authorization: Token my-super-secret-influxdb-token' \
  -H 'Content-Type: application/vnd.flux' \
  -d 'from(bucket: "timeseries")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "sensor_data")
  |> filter(fn: (r) => r["tag_id"] == "ELEV01_TEMP_C_PV")
  |> count()'
```

Deve retornar count > 0.

3. Verificar se backend tem acesso ao InfluxDB:
```bash
docker-compose exec backend python -c "
from influxdb_client import InfluxDBClient
client = InfluxDBClient(
    url='http://influxdb:8086',
    token='my-super-secret-influxdb-token',
    org='optiflow'
)
print('Connected:', client.ping())
"
```

---

**Estimativa de tempo:** 30-45 minutos para aplicar patch completo e testar.

**Resultado Esperado:** Agent responderá com dados REAIS do InfluxDB, não mais "não há dados disponíveis".
