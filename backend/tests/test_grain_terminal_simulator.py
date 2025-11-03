"""
Unit tests for Grain Terminal Simulator
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.grain_terminal_simulator import GrainTerminalSimulator, Config


def test_simulator_initialization():
    """Test that simulator initializes correctly"""
    sim = GrainTerminalSimulator()

    # Check initial state
    assert sim.time_s == 0.0
    assert sim.running == False
    assert sim.emergency_stop == False

    # Check warehouse
    assert sim.warehouse_inventory_t == Config.WAREHOUSE_INITIAL_INVENTORY_T
    assert sim.warehouse_level_pct > 0

    # Check gates
    assert len(sim.gates) == Config.GATES_COUNT
    assert sim.gates[0].id == 1
    assert sim.gates[9].id == 10

    # First 4 gates should be initialized
    assert sim.gates[0].open_pct_sp == Config.PI_INITIAL_OPEN_PCT
    assert sim.gates[1].open_pct_sp == Config.PI_INITIAL_OPEN_PCT
    assert sim.gates[2].open_pct_sp == Config.PI_INITIAL_OPEN_PCT
    assert sim.gates[3].open_pct_sp == Config.PI_INITIAL_OPEN_PCT
    assert sim.gates[4].open_pct_sp == 0.0

    # Check belts
    assert 'CORR01' in sim.belts
    assert 'CORR02' in sim.belts
    assert 'CORR03' in sim.belts

    # Check elevator
    assert sim.elevator.id == 'ELV01'
    assert sim.elevator.running == False

    # Check balance
    assert sim.balance.id == 'BAL01'
    assert sim.balance.target_kg == 4500.0

    # Check shiploader
    assert sim.shiploader.id == 'SLD01'
    assert sim.shiploader.flow_sp_tph == 1500.0

    # Check PI controller
    assert sim.pi_controller.active_gates == [1, 2, 3, 4]

    # Check energy
    assert sim.total_kWh == 0.0
    assert sim.total_mass_t == 0.0

    print("✅ Initialization test passed")


def test_simulator_start_stop():
    """Test start/stop functionality"""
    sim = GrainTerminalSimulator()

    # Start
    sim.start()
    assert sim.running == True
    assert sim.shiploader.running == True
    assert sim.belts['CORR01'].running == True
    assert sim.elevator.running == True
    assert sim.balance.running == True

    # Stop
    sim.stop()
    assert sim.running == False
    assert sim.shiploader.running == False
    assert sim.belts['CORR01'].running == False

    # Gates should close
    for gate in sim.gates:
        if gate.id <= 4:
            assert gate.open_pct_sp == 0.0

    print("✅ Start/Stop test passed")


def test_simulator_step():
    """Test single simulation step"""
    sim = GrainTerminalSimulator()
    sim.start()

    initial_time = sim.time_s

    # Step once
    sim.step(dt_s=1.0)

    assert sim.time_s == initial_time + 1.0

    # Check that gates have flow
    total_flow = sum(g.flow_tph for g in sim.gates)
    assert total_flow > 0, "Gates should have flow"

    # Belt should receive flow
    assert sim.belts['CORR01'].flow_tph > 0

    print(f"✅ Step test passed - Total gate flow: {total_flow:.2f} t/h")


def test_simulator_multiple_steps():
    """Test running simulation for multiple steps"""
    sim = GrainTerminalSimulator()
    sim.start()

    print("\n🚀 Running simulation for 10 steps...")

    for i in range(10):
        sim.step(dt_s=1.0)

        print(f"\n  Step {i+1}:")
        print(f"    Time: {sim.time_s:.1f} s")
        print(f"    Warehouse: {sim.warehouse_inventory_t:.1f} t ({sim.warehouse_level_pct:.1f}%)")

        # Gates
        total_gate_flow = sum(g.flow_tph for g in sim.gates)
        print(f"    Total Gate Flow: {total_gate_flow:.2f} t/h")

        # Belts
        print(f"    CORR01 Flow: {sim.belts['CORR01'].flow_tph:.2f} t/h, Load: {sim.belts['CORR01'].load_pct:.1f}%")
        print(f"    CORR01 Temp: {sim.belts['CORR01'].temp_bearing_C:.1f}°C")

        # Elevator
        print(f"    ELV01 Flow: {sim.elevator.flow_tph:.2f} t/h")

        # Shiploader
        print(f"    Shiploader SP: {sim.shiploader.flow_sp_tph:.0f} t/h, PV: {sim.shiploader.flow_pv_tph:.2f} t/h")

        # PI Controller
        print(f"    PI Error: {sim.pi_controller.error:.2f} t/h, Output: {sim.pi_controller.output:.2f}")

        # Energy
        print(f"    Energy: {sim.total_kWh:.3f} kWh, Mass: {sim.total_mass_t:.3f} t")

        # Check some invariants
        assert sim.warehouse_inventory_t >= 0, "Warehouse inventory should not be negative"
        assert sim.warehouse_level_pct >= 0, "Warehouse level should not be negative"

    print("\n✅ Multiple steps test passed")

    # Final checks
    assert sim.total_kWh > 0, "Should have consumed some energy"
    assert sim.total_mass_t >= 0, "Should have produced some mass"


def test_simulator_pi_control():
    """Test PI controller behavior"""
    sim = GrainTerminalSimulator()
    sim.start()

    # Run for 30 seconds to let PI stabilize
    print("\n🎯 Testing PI Controller stabilization...")

    errors = []
    for i in range(30):
        sim.step(dt_s=1.0)
        errors.append(abs(sim.pi_controller.error))

        if i % 10 == 9:
            print(f"  t={i+1}s: Error={sim.pi_controller.error:.2f} t/h, PV={sim.shiploader.flow_pv_tph:.2f} t/h")

    # Error should decrease over time (PI control working)
    assert errors[-1] < errors[5], "PI controller should reduce error over time"

    print("✅ PI control test passed")


def test_simulator_setpoints():
    """Test setting setpoints"""
    sim = GrainTerminalSimulator()

    # Set shiploader setpoint
    sim.set_shiploader_setpoint(1200.0)
    assert sim.shiploader.flow_sp_tph == 1200.0

    # Set gate manual
    sim.set_gate_manual(1, 80.0)
    assert sim.gates[0].open_pct_sp == 80.0

    # Test limits
    sim.set_shiploader_setpoint(2000.0)  # Above max
    assert sim.shiploader.flow_sp_tph == 1650.0  # Should be clamped

    sim.set_shiploader_setpoint(-100.0)  # Below min
    assert sim.shiploader.flow_sp_tph == 0.0  # Should be clamped

    print("✅ Setpoints test passed")


def test_simulator_tag_values():
    """Test getting tag values"""
    sim = GrainTerminalSimulator()
    sim.start()
    sim.step()

    # Test various tag reads
    tags_to_test = [
        'GATE01_POSITION',
        'GATE01_FLOW',
        'CORR01_RPM',
        'CORR01_FLOW',
        'CORR01_CURRENT',
        'CORR01_POWER',
        'CORR01_TEMP_BEARING',
        'ELV01_FLOW',
        'ELV01_TEMP_MOTOR',
        'BAL01_WEIGHT',
        'BAL01_CYCLES',
        'SLD01_FLOW_SP',
        'SLD01_FLOW_PV',
        'WAREHOUSE_INVENTORY',
        'WAREHOUSE_LEVEL',
        'TOTAL_KWH',
        'TOTAL_MASS',
        'SYSTEM_RUNNING'
    ]

    print("\n📊 Testing tag values:")
    for tag in tags_to_test:
        value = sim.get_tag_value(tag)
        assert value is not None, f"Tag {tag} should return a value"
        print(f"  {tag}: {value}")

    print("✅ Tag values test passed")


def test_simulator_thermal_model():
    """Test thermal model (heating/cooling)"""
    sim = GrainTerminalSimulator()
    sim.start()

    initial_temp = sim.belts['CORR01'].temp_bearing_C

    # Run with load for 60 seconds
    for _ in range(60):
        sim.step(dt_s=1.0)

    loaded_temp = sim.belts['CORR01'].temp_bearing_C

    # Temperature should increase under load
    assert loaded_temp > initial_temp, "Temperature should rise under load"

    print(f"\n🌡️  Thermal model test:")
    print(f"  Initial temp: {initial_temp:.1f}°C")
    print(f"  After 60s load: {loaded_temp:.1f}°C")
    print(f"  Delta: +{loaded_temp - initial_temp:.1f}°C")

    # Stop and cool down
    sim.stop()
    for _ in range(60):
        sim.step(dt_s=1.0)

    cooled_temp = sim.belts['CORR01'].temp_bearing_C

    # Temperature should decrease when stopped
    assert cooled_temp < loaded_temp, "Temperature should drop when stopped"

    print(f"  After 60s stopped: {cooled_temp:.1f}°C")
    print(f"  Delta: {cooled_temp - loaded_temp:.1f}°C")

    print("✅ Thermal model test passed")


def test_simulator_state_export():
    """Test state export to dict"""
    sim = GrainTerminalSimulator()
    sim.start()
    sim.step()

    state_dict = sim.get_state_dict()

    # Check structure
    assert 'time_s' in state_dict
    assert 'running' in state_dict
    assert 'gates' in state_dict
    assert 'belts' in state_dict
    assert 'elevator' in state_dict
    assert 'balance' in state_dict
    assert 'shiploader' in state_dict
    assert 'energy' in state_dict

    # Check gates
    assert len(state_dict['gates']) == 10

    # Check belts
    assert 'CORR01' in state_dict['belts']
    assert 'flow_tph' in state_dict['belts']['CORR01']

    # Check energy
    assert 'total_kWh' in state_dict['energy']
    assert 'kWh_per_ton' in state_dict['energy']
    assert 'cost_BRL' in state_dict['energy']

    print("✅ State export test passed")


if __name__ == "__main__":
    print("=" * 70)
    print("  Grain Terminal Simulator - Unit Tests")
    print("=" * 70)

    try:
        test_simulator_initialization()
        test_simulator_start_stop()
        test_simulator_step()
        test_simulator_setpoints()
        test_simulator_tag_values()
        test_simulator_multiple_steps()
        test_simulator_pi_control()
        test_simulator_thermal_model()
        test_simulator_state_export()

        print("\n" + "=" * 70)
        print("  ✅ ALL TESTS PASSED!")
        print("=" * 70)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
