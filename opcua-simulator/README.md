# OptiFlow OPC UA Simulator

Standalone OPC UA server simulating a complete grain terminal.

## Features

- **3 Conveyors (CORR01-03)**: Speed, load, current, power, temperature, vibration, misalignment
- **3 Silos (SILO01-03)**: Level, grain temperature, humidity, weight, pressure
- **2 Elevators (ELEV01-02)**: Speed, current, power, temperature
- **Energy Monitoring**: Total power, energy consumption, power factor, grid voltage

## Connection

```
Endpoint: opc.tcp://opcua-server:4840/optiflow/terminal
Security: None (for development)
Update Rate: 1 second
```

## OPC UA Structure

```
GrainTerminal/
├── Conveyors/
│   ├── CORR01/
│   │   ├── running (bool)
│   │   ├── speed_mps (float)
│   │   ├── load_pct (float)
│   │   ├── current_a (float)
│   │   ├── power_kw (float)
│   │   ├── temp_c (float)
│   │   ├── vibration_mms (float)
│   │   └── misalignment (float)
│   ├── CORR02/ ...
│   └── CORR03/ ...
├── Silos/
│   ├── SILO01/
│   │   ├── level_pct (float)
│   │   ├── temp_grain_c (float)
│   │   ├── humidity_pct (float)
│   │   ├── weight_t (float)
│   │   └── pressure_pa (float)
│   ├── SILO02/ ...
│   └── SILO03/ ...
├── Elevators/
│   ├── ELEV01/
│   │   ├── running (bool)
│   │   ├── bucket_speed_mps (float)
│   │   ├── current_a (float)
│   │   ├── power_kw (float)
│   │   └── temp_c (float)
│   └── ELEV02/ ...
└── Energy/
    ├── grid_power_kw (float)
    ├── total_energy_kwh (float)
    ├── power_factor (float)
    └── grid_voltage_v (float)
```

## Testing

Using **UaExpert** or **Python client**:

```python
from asyncua import Client

async with Client("opc.tcp://localhost:4840/optiflow/terminal") as client:
    node = await client.nodes.root.get_child([
        "0:Objects", 
        "2:GrainTerminal", 
        "2:Conveyors", 
        "2:CORR01", 
        "2:speed_mps"
    ])
    value = await node.read_value()
    print(f"CORR01 Speed: {value} m/s")
```

## Docker Run

```bash
docker build -t optiflow-opcua-simulator .
docker run -p 4840:4840 optiflow-opcua-simulator
```
