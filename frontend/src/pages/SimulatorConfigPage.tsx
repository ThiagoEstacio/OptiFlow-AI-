import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Play, Pause, RotateCcw, Cpu, Activity, AlertCircle } from 'lucide-react';
import { apiClient } from '../api/client';

const SimulatorConfigPage: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await apiClient.get('/api/v1/simulator/status');
      setStatus(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching simulator status:', err);
    }
  };

  const handleStart = async () => {
    setLoading(true);
    try {
      await apiClient.post('/api/v1/simulator/start');
      await fetchStatus();
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start simulator');
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      await apiClient.post('/api/v1/simulator/stop');
      await fetchStatus();
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to stop simulator');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setLoading(true);
    try {
      await apiClient.post('/api/v1/simulator/reset');
      await fetchStatus();
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reset simulator');
    } finally {
      setLoading(false);
    }
  };

  const isRunning = status?.status === 'running';

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Cpu className="h-8 w-8 text-cyan-500" />
          Simulator Control
        </h1>
        <p className="text-gray-600 mt-2">
          Virtual PLC - Grain Terminal Simulator (Lightweight, No DEM)
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Current Status
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <div className={`w-4 h-4 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
              <span className="font-semibold text-lg">
                {isRunning ? 'RUNNING' : 'STOPPED'}
              </span>
            </div>

            {status && (
              <>
                <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                  <div>
                    <p className="text-sm text-gray-500">Simulation Time</p>
                    <p className="text-xl font-bold">{status.time_s?.toFixed(1) || '0.0'} s</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Total Mass</p>
                    <p className="text-xl font-bold">{status.total_mass_t?.toFixed(1) || '0.0'} t</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Warehouse Level</p>
                    <p className="text-xl font-bold">{status.warehouse_level_pct?.toFixed(1) || '0.0'}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Total Energy</p>
                    <p className="text-xl font-bold">{status.total_kwh?.toFixed(1) || '0.0'} kWh</p>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <p className="text-sm text-gray-500 mb-2">Data Publishing</p>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    <span className="text-sm">Publishing to Kafka (raw_tags)</span>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Controls Card */}
        <Card>
          <CardHeader>
            <CardTitle>Controls</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <button
              onClick={handleStart}
              disabled={loading || isRunning}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Play className="h-5 w-5" />
              Start Simulator
            </button>

            <button
              onClick={handleStop}
              disabled={loading || !isRunning}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Pause className="h-5 w-5" />
              Stop Simulator
            </button>

            <button
              onClick={handleReset}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <RotateCcw className="h-5 w-5" />
              Reset Simulator
            </button>

            <div className="pt-4 border-t">
              <h4 className="font-semibold mb-2">Auto-Step Mode</h4>
              <p className="text-sm text-gray-600 mb-3">
                The simulator automatically advances when started. Each step represents 1 second of process time.
              </p>
              <div className="bg-blue-50 border border-blue-200 rounded p-3">
                <p className="text-xs text-blue-800">
                  <strong>Note:</strong> Data is automatically published to Kafka and consumed by InfluxDB.
                  View real-time data in Operations → SCADA Monitor.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Info Card */}
      <Card className="mt-6 bg-cyan-50 border-cyan-200">
        <CardHeader>
          <CardTitle>About This Simulator</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm text-cyan-900">
            <p>
              <strong>Purpose:</strong> This is a lightweight grain terminal simulator that acts as a virtual PLC,
              generating realistic process data for testing and demonstration.
            </p>
            <p>
              <strong>Equipment Simulated:</strong>
            </p>
            <ul className="list-disc list-inside ml-4 space-y-1">
              <li>7 Gates (dosing gates) with position and flow control</li>
              <li>3 Conveyor Belts (CORR01, CORR02, CORR03) with speed and load monitoring</li>
              <li>1 Shiploader with position control</li>
              <li>Warehouse inventory tracking</li>
              <li>Energy consumption monitoring</li>
            </ul>
            <p>
              <strong>Data Flow:</strong> Simulator → Kafka (raw_tags topic) → InfluxDB Consumer → InfluxDB → Real-time Dashboards
            </p>
            <p className="text-xs text-cyan-700 mt-4">
              💡 <strong>Tip:</strong> Start the simulator, then navigate to <strong>Operations → SCADA Monitor</strong> to see
              real-time data visualization of all equipment and process variables.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SimulatorConfigPage;
