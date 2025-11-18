/**
 * Equipment Statistics Dashboard
 * 
 * Real-time statistics dashboard showing:
 * - Conveyor system performance
 * - Silo inventory levels
 * - Elevator operations
 * - Energy consumption
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import {
  Activity,
  Loader2,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Zap,
  Package,
  BarChart3,
  Gauge
} from 'lucide-react';
import { apiClient } from '../api/client';

interface TagValue {
  value: number;
  timestamp: string;
  quality: string;
}

interface EquipmentStats {
  conveyors: {
    avgSpeed: number;
    avgLoad: number;
    totalPower: number;
    avgTemp: number;
    maxVibration: number;
  };
  silos: {
    totalCapacity: number;
    currentInventory: number;
    avgLevel: number;
    avgTemp: number;
    lowestLevel: { name: string; value: number };
    highestLevel: { name: string; value: number };
  };
  elevators: {
    avgSpeed: number;
    totalPower: number;
    avgTemp: number;
    runningCount: number;
  };
  energy: {
    gridPower: number;
    totalEnergy: number;
    powerFactor: number;
    gridVoltage: number;
  };
}

export const EquipmentStatistics: React.FC = () => {
  const [stats, setStats] = useState<EquipmentStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Fetch all tag values
        const response = await apiClient.get('/api/v1/tags/');
        const tags = response.data;

        // Filter simulator tags
        const simTags = tags.filter((tag: any) => 
          !tag.name.startsWith('SYSTEM') && 
          !tag.name.startsWith('ARZ_') &&
          !tag.name.startsWith('GATE_') &&
          !tag.name.startsWith('SHIPLOADER_')
        );

        // Fetch values for all tags
        const values: Record<string, TagValue> = {};
        for (const tag of simTags) {
          try {
            const resp = await apiClient.get(`/api/v1/tags/realtime/${tag.name}`);
            values[tag.name] = resp.data;
          } catch (err) {
            console.error(`Error fetching ${tag.name}:`, err);
          }
        }

        // Calculate statistics
        const newStats = calculateStatistics(values);
        setStats(newStats);
        setLastUpdate(new Date());
        setError(null);
      } catch (err: any) {
        console.error('Error fetching statistics:', err);
        setError(err.response?.data?.detail || 'Failed to fetch statistics');
      } finally {
        setIsLoading(false);
      }
    };

    // Initial fetch
    fetchStats();

    // Poll every 5 seconds
    const intervalId = setInterval(fetchStats, 5000);

    return () => clearInterval(intervalId);
  }, []);

  const calculateStatistics = (values: Record<string, TagValue>): EquipmentStats => {
    // Conveyor stats
    const convSpeeds = ['CORR01_SPEED_MPS_PV', 'CORR02_SPEED_MPS_PV', 'CORR03_SPEED_MPS_PV']
      .map(name => values[name]?.value || 0);
    const convLoads = ['CORR01_LOAD_PCT_PV', 'CORR02_LOAD_PCT_PV', 'CORR03_LOAD_PCT_PV']
      .map(name => values[name]?.value || 0);
    const convPowers = ['CORR01_POWER_KW_PV', 'CORR02_POWER_KW_PV', 'CORR03_POWER_KW_PV']
      .map(name => values[name]?.value || 0);
    const convTemps = ['CORR01_TEMP_C_PV', 'CORR02_TEMP_C_PV', 'CORR03_TEMP_C_PV']
      .map(name => values[name]?.value || 0);
    const convVibs = ['CORR01_VIBRATION_MMS_PV', 'CORR02_VIBRATION_MMS_PV', 'CORR03_VIBRATION_MMS_PV']
      .map(name => values[name]?.value || 0);

    // Silo stats
    const siloLevels = [
      { name: 'SILO01', value: values['SILO01_LEVEL_PCT_PV']?.value || 0 },
      { name: 'SILO02', value: values['SILO02_LEVEL_PCT_PV']?.value || 0 },
      { name: 'SILO03', value: values['SILO03_LEVEL_PCT_PV']?.value || 0 }
    ];
    const siloTemps = ['SILO01_TEMP_GRAIN_C_PV', 'SILO02_TEMP_GRAIN_C_PV', 'SILO03_TEMP_GRAIN_C_PV']
      .map(name => values[name]?.value || 0);
    
    const lowestSilo = siloLevels.reduce((min, silo) => silo.value < min.value ? silo : min);
    const highestSilo = siloLevels.reduce((max, silo) => silo.value > max.value ? silo : max);

    // Elevator stats
    const elevSpeeds = ['ELEV01_BUCKET_SPEED_MPS_PV', 'ELEV02_BUCKET_SPEED_MPS_PV']
      .map(name => values[name]?.value || 0);
    const elevPowers = ['ELEV01_POWER_KW_PV', 'ELEV02_POWER_KW_PV']
      .map(name => values[name]?.value || 0);
    const elevTemps = ['ELEV01_TEMP_C_PV', 'ELEV02_TEMP_C_PV']
      .map(name => values[name]?.value || 0);
    const elevRunning = ['ELEV01_RUNNING_PV', 'ELEV02_RUNNING_PV']
      .filter(name => values[name]?.value).length;

    return {
      conveyors: {
        avgSpeed: avg(convSpeeds),
        avgLoad: avg(convLoads),
        totalPower: sum(convPowers),
        avgTemp: avg(convTemps),
        maxVibration: Math.max(...convVibs)
      },
      silos: {
        totalCapacity: 3 * 1000, // 3 silos x 1000 tons each
        currentInventory: sum(siloLevels.map(s => s.value)) / 100 * 1000, // Tons
        avgLevel: avg(siloLevels.map(s => s.value)),
        avgTemp: avg(siloTemps),
        lowestLevel: lowestSilo,
        highestLevel: highestSilo
      },
      elevators: {
        avgSpeed: avg(elevSpeeds),
        totalPower: sum(elevPowers),
        avgTemp: avg(elevTemps),
        runningCount: elevRunning
      },
      energy: {
        gridPower: values['Energy_GRID_POWER_KW_PV']?.value || 0,
        totalEnergy: values['Energy_TOTAL_ENERGY_KWH_PV']?.value || 0,
        powerFactor: values['Energy_POWER_FACTOR_PV']?.value || 0,
        gridVoltage: values['Energy_GRID_VOLTAGE_V_PV']?.value || 0
      }
    };
  };

  const avg = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length;
  const sum = (arr: number[]) => arr.reduce((a, b) => a + b, 0);

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="flex items-center justify-center p-8">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            <span className="ml-3 text-gray-600">Loading statistics...</span>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <BarChart3 className="h-8 w-8 text-blue-500" />
          Equipment Statistics
        </h1>
        <p className="text-gray-600 mt-2">
          Real-time performance metrics and KPIs
          {lastUpdate && (
            <span className="ml-2 text-sm">
              • Updated {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Conveyor Systems */}
      <Card className="mb-6">
        <CardHeader className="bg-gradient-to-r from-blue-50 to-blue-100">
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-600" />
            Conveyor Systems (3 units)
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
            <StatBox
              label="Avg Speed"
              value={stats.conveyors.avgSpeed.toFixed(2)}
              unit="m/s"
              icon={<TrendingUp className="h-5 w-5 text-blue-500" />}
            />
            <StatBox
              label="Avg Load"
              value={stats.conveyors.avgLoad.toFixed(1)}
              unit="%"
              icon={<Package className="h-5 w-5 text-green-500" />}
            />
            <StatBox
              label="Total Power"
              value={stats.conveyors.totalPower.toFixed(1)}
              unit="kW"
              icon={<Zap className="h-5 w-5 text-yellow-500" />}
            />
            <StatBox
              label="Avg Temperature"
              value={stats.conveyors.avgTemp.toFixed(1)}
              unit="°C"
              icon={<Gauge className="h-5 w-5 text-orange-500" />}
              alert={stats.conveyors.avgTemp > 70}
            />
            <StatBox
              label="Max Vibration"
              value={stats.conveyors.maxVibration.toFixed(2)}
              unit="mm/s"
              icon={<Activity className="h-5 w-5 text-purple-500" />}
              alert={stats.conveyors.maxVibration > 8}
            />
          </div>
        </CardContent>
      </Card>

      {/* Silos */}
      <Card className="mb-6">
        <CardHeader className="bg-gradient-to-r from-green-50 to-green-100">
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5 text-green-600" />
            Silo Inventory (3 units × 1000 tons)
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
            <StatBox
              label="Current Inventory"
              value={stats.silos.currentInventory.toFixed(0)}
              unit="tons"
              icon={<Package className="h-5 w-5 text-green-500" />}
            />
            <StatBox
              label="Avg Fill Level"
              value={stats.silos.avgLevel.toFixed(1)}
              unit="%"
              icon={<BarChart3 className="h-5 w-5 text-blue-500" />}
            />
            <StatBox
              label="Avg Temperature"
              value={stats.silos.avgTemp.toFixed(1)}
              unit="°C"
              icon={<Gauge className="h-5 w-5 text-orange-500" />}
              alert={stats.silos.avgTemp > 35}
            />
            <StatBox
              label="Total Capacity"
              value={stats.silos.totalCapacity.toString()}
              unit="tons"
              icon={<Package className="h-5 w-5 text-gray-400" />}
            />
          </div>

          <div className="flex gap-4">
            <div className="flex-1 p-4 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-red-700 font-medium">Lowest Level</span>
                <TrendingDown className="h-4 w-4 text-red-500" />
              </div>
              <div className="text-2xl font-bold text-red-900">
                {stats.silos.lowestLevel.name}
              </div>
              <div className="text-sm text-red-600">
                {stats.silos.lowestLevel.value.toFixed(1)}%
              </div>
            </div>

            <div className="flex-1 p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-green-700 font-medium">Highest Level</span>
                <TrendingUp className="h-4 w-4 text-green-500" />
              </div>
              <div className="text-2xl font-bold text-green-900">
                {stats.silos.highestLevel.name}
              </div>
              <div className="text-sm text-green-600">
                {stats.silos.highestLevel.value.toFixed(1)}%
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Elevators & Energy */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Elevators */}
        <Card>
          <CardHeader className="bg-gradient-to-r from-purple-50 to-purple-100">
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-purple-600" />
              Bucket Elevators (2 units)
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-2 gap-4">
              <StatBox
                label="Running"
                value={stats.elevators.runningCount.toString()}
                unit="of 2"
                icon={<Activity className="h-5 w-5 text-green-500" />}
              />
              <StatBox
                label="Avg Speed"
                value={stats.elevators.avgSpeed.toFixed(2)}
                unit="m/s"
                icon={<TrendingUp className="h-5 w-5 text-blue-500" />}
              />
              <StatBox
                label="Total Power"
                value={stats.elevators.totalPower.toFixed(1)}
                unit="kW"
                icon={<Zap className="h-5 w-5 text-yellow-500" />}
              />
              <StatBox
                label="Avg Temp"
                value={stats.elevators.avgTemp.toFixed(1)}
                unit="°C"
                icon={<Gauge className="h-5 w-5 text-orange-500" />}
                alert={stats.elevators.avgTemp > 75}
              />
            </div>
          </CardContent>
        </Card>

        {/* Energy */}
        <Card>
          <CardHeader className="bg-gradient-to-r from-yellow-50 to-yellow-100">
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-600" />
              Energy Consumption
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-2 gap-4">
              <StatBox
                label="Grid Power"
                value={stats.energy.gridPower.toFixed(1)}
                unit="kW"
                icon={<Zap className="h-5 w-5 text-yellow-500" />}
                alert={stats.energy.gridPower > 250}
              />
              <StatBox
                label="Total Energy"
                value={stats.energy.totalEnergy.toFixed(1)}
                unit="kWh"
                icon={<BarChart3 className="h-5 w-5 text-blue-500" />}
              />
              <StatBox
                label="Power Factor"
                value={stats.energy.powerFactor.toFixed(2)}
                unit=""
                icon={<Gauge className="h-5 w-5 text-green-500" />}
                alert={stats.energy.powerFactor < 0.85}
              />
              <StatBox
                label="Grid Voltage"
                value={stats.energy.gridVoltage.toFixed(0)}
                unit="V"
                icon={<Zap className="h-5 w-5 text-purple-500" />}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

interface StatBoxProps {
  label: string;
  value: string;
  unit: string;
  icon: React.ReactNode;
  alert?: boolean;
}

const StatBox: React.FC<StatBoxProps> = ({ label, value, unit, icon, alert }) => (
  <div className={`p-4 rounded-lg border ${alert ? 'bg-red-50 border-red-300' : 'bg-gray-50 border-gray-200'}`}>
    <div className="flex items-center justify-between mb-2">
      <span className={`text-xs ${alert ? 'text-red-700' : 'text-gray-600'} font-medium uppercase`}>
        {label}
      </span>
      {icon}
    </div>
    <div className={`text-2xl font-bold ${alert ? 'text-red-900' : 'text-gray-900'}`}>
      {value}
      <span className={`text-sm ml-1 ${alert ? 'text-red-600' : 'text-gray-500'} font-normal`}>
        {unit}
      </span>
    </div>
    {alert && (
      <div className="mt-1 flex items-center text-xs text-red-600">
        <AlertCircle className="h-3 w-3 mr-1" />
        Threshold exceeded
      </div>
    )}
  </div>
);

export default EquipmentStatistics;
