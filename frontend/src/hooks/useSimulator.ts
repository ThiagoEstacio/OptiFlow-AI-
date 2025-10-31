import { useState, useCallback, useEffect } from 'react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const SIMULATOR_API = `${API_BASE}/api/v1/simulator`;

export interface SimulatorStatus {
  system: {
    time_s: number;
    running: boolean;
    warehouse_inventory_t: number;
    warehouse_level_pct: number;
    total_kWh: number;
    total_mass_t: number;
    cost_BRL: number;
    kWh_per_ton: number;
    availability_pct: number;
  };
  gates: Array<{
    id: number;
    open_pct: number;
    open_pct_sp: number;
    flow_tph: number;
    plugged: boolean;
    failure: boolean;
  }>;
  belts: {
    [key: string]: {
      running: boolean;
      rpm: number;
      speed_mps: number;
      flow_tph: number;
      load_pct: number;
      current_A: number;
      power_kW: number;
      temp_bearing_C: number;
      temp_belt_C: number;
      underspeed_warn: boolean;
      underspeed_alarm: boolean;
      chute_level_pct: number;
      chute_plugged: boolean;
    };
  };
  elevator: {
    running: boolean;
    speed_mps: number;
    flow_tph: number;
    current_A: number;
    power_kW: number;
    temp_motor_C: number;
    temp_gearbox_C: number;
    slip: boolean;
  };
  balance: {
    running: boolean;
    weight_kg: number;
    target_kg: number;
    cycle_count: number;
    total_mass_t: number;
    avg_flow_tph: number;
    cycle_state: string;
  };
  shiploader: {
    running: boolean;
    flow_sp_tph: number;
    flow_pv_tph: number;
    power_kW: number;
    dust_level: number;
  };
  alarms: Array<{
    tag: string;
    active: boolean;
    latched: boolean;
    timestamp: number;
    count: number;
  }>;
  trips: Array<{
    tag: string;
    active: boolean;
    latched: boolean;
    timestamp: number;
    count: number;
  }>;
  interlocks?: {
    active_count: number;
    active_interlocks: Array<{
      id: string;
      cause: string;
      type: string;
      effects: string[];
      active: boolean;
      can_reset: boolean;
    }>;
  };
  maintenance?: {
    avg_health_pct: number;
    equipment: {
      [key: string]: {
        health_pct: number;
        vibration_mm_s: number;
        oil_temp_C: number;
        hours_running: number;
        alarm_count: number;
        trip_count: number;
      };
    };
  };
  energy?: {
    total_power_kW: number;
    avg_power_factor: number;
    total_kWh: number;
    cost_peak_BRL: number;
    cost_offpeak_BRL: number;
    cost_total_BRL: number;
    equipment: {
      [key: string]: {
        voltage_V: number;
        current_A: number;
        power_kW: number;
        reactive_kvar: number;
        apparent_kVA: number;
        power_factor: number;
        kwh: number;
      };
    };
  };
}

export function useSimulator() {
  const [status, setStatus] = useState<SimulatorStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${SIMULATOR_API}/status`);
      setStatus(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch simulator status:', err);
      setError(err.response?.data?.detail || err.message || 'Erro ao buscar status');
    }
  }, []);

  const startSystem = useCallback(async () => {
    setLoading(true);
    try {
      await axios.post(`${SIMULATOR_API}/start`);
      await refreshStatus();
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao iniciar sistema');
    } finally {
      setLoading(false);
    }
  }, [refreshStatus]);

  const stopSystem = useCallback(async () => {
    setLoading(true);
    try {
      await axios.post(`${SIMULATOR_API}/stop`);
      await refreshStatus();
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao parar sistema');
    } finally {
      setLoading(false);
    }
  }, [refreshStatus]);

  const resetSystem = useCallback(async () => {
    setLoading(true);
    try {
      await axios.post(`${SIMULATOR_API}/reset`);
      await refreshStatus();
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao resetar sistema');
    } finally {
      setLoading(false);
    }
  }, [refreshStatus]);

  const setGateSetpoint = useCallback(async (gateId: number, value: number) => {
    setLoading(true);
    try {
      await axios.post(`${SIMULATOR_API}/gates/${gateId}/setpoint`, { value });
      await refreshStatus();
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao ajustar comporta');
    } finally {
      setLoading(false);
    }
  }, [refreshStatus]);

  const setAllGatesSetpoint = useCallback(async (value: number) => {
    setLoading(true);
    try {
      await axios.post(`${SIMULATOR_API}/gates/all/setpoint`, { value });
      await refreshStatus();
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao ajustar comportas');
    } finally {
      setLoading(false);
    }
  }, [refreshStatus]);

  const setShiploaderSetpoint = useCallback(async (value: number) => {
    setLoading(true);
    try {
      await axios.post(`${SIMULATOR_API}/shiploader/setpoint`, { value });
      await refreshStatus();
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao ajustar shiploader');
    } finally {
      setLoading(false);
    }
  }, [refreshStatus]);

  const acknowledgeAllAlarms = useCallback(async () => {
    setLoading(true);
    try {
      await axios.post(`${SIMULATOR_API}/alarms/acknowledge-all`);
      await refreshStatus();
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao reconhecer alarmes');
    } finally {
      setLoading(false);
    }
  }, [refreshStatus]);

  // Auto-update loop: step simulation and refresh status
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    if (status?.system?.running) {
      intervalId = setInterval(async () => {
        try {
          // Step the simulation by 1 second
          await axios.post(`${SIMULATOR_API}/step`, null, { params: { dt_s: 1.0 } });
          // Refresh status
          await refreshStatus();
        } catch (err) {
          console.error('Error in simulation loop:', err);
        }
      }, 1000); // Update every 1 second
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [status?.system?.running, refreshStatus]);

  return {
    status,
    loading,
    error,
    startSystem,
    stopSystem,
    resetSystem,
    setGateSetpoint,
    setAllGatesSetpoint,
    setShiploaderSetpoint,
    acknowledgeAllAlarms,
    refreshStatus,
  };
}
