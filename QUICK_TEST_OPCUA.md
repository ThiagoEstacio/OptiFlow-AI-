# 🚀 Quick Test Guide - OPC-UA Server

## ✅ Server Status Check

### 1. Check if server is running
```bash
lsof -i:4840
```
Expected: Port 4840 is LISTENING

### 2. Check server logs
```bash
tail -f opcua_server_final.log
```
Expected: Only "aiokafka not installed" warning, NO BadTypeMismatch errors

### 3. Test connection
```bash
python test_opcua_minimal.py
```
Expected: "✅ Conectado com sucesso!"

---

## 🔧 Start/Stop Server

### Start Server
```bash
/home/thiestacio/anaconda3/envs/optiflow/bin/python backend/scripts/run_opcua_server.py > opcua_server.log 2>&1 &
```

### Stop Server
```bash
pkill -f "run_opcua_server.py"
```

### Restart Server
```bash
pkill -f "run_opcua_server.py" && sleep 2
/home/thiestacio/anaconda3/envs/optiflow/bin/python backend/scripts/run_opcua_server.py > opcua_server.log 2>&1 &
```

---

## 🔍 OPC-UA Server Details

**Endpoint**: `opc.tcp://localhost:4840/optiflow/terminal`

**Namespaces**:
- `0`: http://opcfoundation.org/UA/
- `1`: urn:freeopcua:python:server
- `2`: http://optiflow.com/terminal (OptiFlow custom)

**Main Structure**:
```
Root
└── Objects
    └── TEAG (Terminal Exportador)
        ├── SYSTEM.RUNNING.PV
        ├── ARZ (Armazém)
        │   ├── GATES (10 vazadores)
        │   └── CORRIDORS (3 correias)
        ├── ELV (Elevador)
        ├── BAL (Balança)
        ├── SLD (Shiploader)
        ├── KPIs (Totalizadores)
        ├── CONTROL (Controle)
        ├── INTERLOCKS (Intertravamentos)
        ├── ALARMES (Sistema de alarmes)
        ├── MANUTENCAO (Manutenção preditiva)
        └── ENERGIA (Gestão energética)
```

**Total Variables**: ~60-80 process variables

---

## 🧪 Testing Options

### Option 1: Minimal Test (Current Working)
```bash
python test_opcua_minimal.py
```
- Tests basic connection
- Lists namespaces
- Browses TEAG node
- Shows all children

### Option 2: Full Discovery Test
First install dependencies:
```bash
conda activate optiflow
pip install pymodbus
```

Then run:
```bash
cd gateway
python test_opcua_discovery.py opc.tcp://localhost:4840/optiflow/terminal
```

### Option 3: Via REST API
```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@optiflow.com&password=admin123" \
  | jq -r '.access_token')

# 2. Run discovery
curl -X POST http://localhost:8000/api/v1/opcua-discovery/discover \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "server": {
      "endpoint": "opc.tcp://localhost:4840/optiflow/terminal",
      "device_name": "Simulador Terminal TEAG"
    },
    "save_to_database": true
  }' | jq

# 3. Check statistics
curl -X GET http://localhost:8000/api/v1/opcua-discovery/statistics \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## 🐛 Troubleshooting

### Problem: Connection timeout
```bash
# Check if server is running
ps aux | grep "run_opcua_server" | grep -v grep

# Check if port is listening
lsof -i:4840

# Check server logs
tail -50 opcua_server.log | grep ERROR
```

### Problem: BadTypeMismatch errors
This was fixed! If you see this error:
- Make sure you're running the latest code (commit 0501a2b or later)
- Restart the server
- Check that the fix is in the files:
```bash
grep "0.0" backend/app/services/opcua_server_extensions.py | grep -E "INTERLOCKS_ACTIVE_COUNT|ALARMS_TOTAL|MAINT_"
```

### Problem: High CPU usage
- Check for errors in logs: `tail -100 opcua_server.log | grep ERROR`
- If BadTypeMismatch errors, restart server with latest code
- Normal CPU: 5-10%, High CPU: >50% indicates problem

---

## 📊 Expected Process Variables

### Warehouse (ARZ)
- Inventory level (tons)
- Warehouse level (%)

### Gates (10 units)
- GATE01-GATE10 each with:
  - Position PV/SP (%)
  - Flow PV (t/h)
  - Plugged alarm (bool)

### Belts/Corridors (3 units)
- CORR01, CORR02, CORR03 each with:
  - Running status (bool)
  - RPM, Speed (m/s), Flow (t/h)
  - Current (A), Power (kW)
  - Temperatures (bearing, belt, drum °C)
  - Underspeed warnings/alarms
  - Chute level (%) and plugged alarm

### Elevator (ELV01)
- Running, Speed, Flow
- Current, Power
- Motor/Gearbox temperatures
- Belt slip detection

### Balance (BAL01)
- Running, Weight, Target
- Cycle count
- Total mass (t)
- Average flow (t/h)
- Cycle state (idle/filling/settling/dumping)

### Shiploader (SLD01)
- Running
- Flow PV/SP (t/h)
- Power (kW)
- Dust level

### KPIs
- Total kWh consumed
- Total mass processed (t)
- kWh per ton
- Cost (BRL)

### Advanced Systems
- **Interlocks**: Active count, top 10 active interlocks
- **Alarms**: Total, Critical, High, Medium, Unacknowledged counts
- **Maintenance**: Avg health, Equipment health scores, Running hours, Vibration, Oil temps
- **Energy**: Real-time power, PF, Demand, Consumption, Cost

---

## ✅ Success Indicators

Server is working correctly if:
- ✅ Port 4840 is LISTENING
- ✅ Logs show NO "BadTypeMismatch" errors
- ✅ Connection test succeeds in <2 seconds
- ✅ Can browse all 13 TEAG children
- ✅ CPU usage is <20%

---

**Last Updated**: 2025-11-10 (after type mismatch fix)
**Commit**: 0501a2b
**Status**: ✅ Production Ready
