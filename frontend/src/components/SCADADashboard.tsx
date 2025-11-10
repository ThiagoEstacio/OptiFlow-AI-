import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Activity, Loader2, AlertCircle, Gauge, Package, Zap, Clock } from 'lucide-react';
import { apiClient } from '../api/client';

interface TagData {
  tag_name: string;
  timestamp: string;
  value: number;
  quality: string;
  source: string;
}

interface TagDataMap {
  [tagName: string]: TagData | null;
}

interface SCADADashboardProps {
  pollInterval?: number;
}

export const SCADADashboard: React.FC<SCADADashboardProps> = ({
  pollInterval = 1000
}) => {
  const [tagData, setTagData] = useState<TagDataMap>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Tags to monitor
  const monitoredTags = [
    'SYSTEM_RUNNING_PV',
    'WAREHOUSE_LEVEL_PCT_PV',
    'TOTAL_MASS_T_PV',
    'TOTAL_KWH_PV',
    'TEST_COUNTER_PV',
    'ARZ_GATES_GATE01_POSICAO_PV',
    'ARZ_GATES_GATE01_VAZAO_TPH_PV',
    'ARZ_GATES_GATE02_POSICAO_PV',
    'ARZ_GATES_GATE02_VAZAO_TPH_PV',
    'ARZ_GATES_GATE03_POSICAO_PV',
    'ARZ_GATES_GATE03_VAZAO_TPH_PV',
    'ARZ_GATES_GATE04_POSICAO_PV',
    'ARZ_GATES_GATE04_VAZAO_TPH_PV',
  ];

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    const fetchTagValues = async () => {
      try {
        const response = await apiClient.post('/api/v1/tags/realtime/batch', monitoredTags);
        setTagData(response.data);
        setLastUpdate(new Date());
        setError(null);
        setIsLoading(false);
      } catch (err: any) {
        console.error('Error fetching tag values:', err);
        setError(err.response?.data?.detail || 'Failed to fetch tag values');
        setIsLoading(false);
      }
    };

    // Initial fetch
    fetchTagValues();

    // Poll every interval
    intervalId = setInterval(fetchTagValues, pollInterval);

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [pollInterval]);

  const getTagValue = (tagName: string): number => {
    return tagData[tagName]?.value ?? 0;
  };

  const getTagQuality = (tagName: string): string => {
    return tagData[tagName]?.quality ?? 'unknown';
  };

  const isSystemRunning = getTagValue('SYSTEM_RUNNING_PV') === 1.0;
  const warehouseLevel = getTagValue('WAREHOUSE_LEVEL_PCT_PV');
  const totalMass = getTagValue('TOTAL_MASS_T_PV');
  const totalEnergy = getTagValue('TOTAL_KWH_PV');

  // Calculate total flow from all gates
  const totalFlow =
    getTagValue('ARZ_GATES_GATE01_VAZAO_TPH_PV') +
    getTagValue('ARZ_GATES_GATE02_VAZAO_TPH_PV') +
    getTagValue('ARZ_GATES_GATE03_VAZAO_TPH_PV') +
    getTagValue('ARZ_GATES_GATE04_VAZAO_TPH_PV');

  const getGateData = (gateNum: number) => {
    const gateStr = gateNum.toString().padStart(2, '0');
    return {
      position: getTagValue(`ARZ_GATES_GATE${gateStr}_POSICAO_PV`),
      flow: getTagValue(`ARZ_GATES_GATE${gateStr}_VAZAO_TPH_PV`),
      quality: getTagQuality(`ARZ_GATES_GATE${gateStr}_POSICAO_PV`)
    };
  };

  const getStatusColor = (quality: string) => {
    switch (quality) {
      case 'good': return 'text-green-600 bg-green-100';
      case 'bad': return 'text-red-600 bg-red-100';
      default: return 'text-yellow-600 bg-yellow-100';
    }
  };

  const getLevelColor = (level: number) => {
    if (level > 60) return 'bg-green-500';
    if (level > 30) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  if (isLoading && Object.keys(tagData).length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-3 text-gray-600">Loading SCADA data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header Status */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-4 h-4 rounded-full ${isSystemRunning ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
              <span className="font-semibold">
                System Status: {isSystemRunning ? 'RUNNING' : 'STOPPED'}
              </span>
            </div>
            {lastUpdate && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Clock className="h-4 w-4" />
                <span>Last Update: {lastUpdate.toLocaleTimeString()}</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Main KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Warehouse Level */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Package className="h-4 w-4" />
              Warehouse Level
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-3xl font-bold">{warehouseLevel.toFixed(1)}%</div>
              <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${getLevelColor(warehouseLevel)}`}
                  style={{ width: `${warehouseLevel}%` }}
                />
              </div>
              <p className="text-xs text-gray-500">Current inventory level</p>
            </div>
          </CardContent>
        </Card>

        {/* Total Flow */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Gauge className="h-4 w-4" />
              Total Flow
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-3xl font-bold">{totalFlow.toFixed(0)}</div>
              <p className="text-sm text-gray-600">t/h</p>
              <p className="text-xs text-gray-500">Combined gate flow rate</p>
            </div>
          </CardContent>
        </Card>

        {/* Total Mass Loaded */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Package className="h-4 w-4" />
              Mass Loaded
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-3xl font-bold">{totalMass.toFixed(1)}</div>
              <p className="text-sm text-gray-600">tonnes</p>
              <p className="text-xs text-gray-500">Total mass processed</p>
            </div>
          </CardContent>
        </Card>

        {/* Total Energy */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Energy Used
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-3xl font-bold">{totalEnergy.toFixed(1)}</div>
              <p className="text-sm text-gray-600">kWh</p>
              <p className="text-xs text-gray-500">Total energy consumed</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Gates Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-500" />
            Gate Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((gateNum) => {
              const gate = getGateData(gateNum);
              return (
                <div key={gateNum} className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">Gate {gateNum}</h4>
                    <span className={`text-xs px-2 py-1 rounded ${getStatusColor(gate.quality)}`}>
                      {gate.quality.toUpperCase()}
                    </span>
                  </div>

                  {/* Position */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">Position</span>
                      <span className="font-semibold">{gate.position.toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 transition-all duration-300"
                        style={{ width: `${gate.position}%` }}
                      />
                    </div>
                  </div>

                  {/* Flow */}
                  <div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Flow</span>
                      <span className="font-semibold">{gate.flow.toFixed(0)} t/h</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Polling Indicator */}
      <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
        <span>Real-time monitoring active (polling every {pollInterval}ms)</span>
      </div>
    </div>
  );
};
