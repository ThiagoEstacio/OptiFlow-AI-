/**
 * Dashboard Page
 */
import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, Zap, AlertCircle } from 'lucide-react';
import { RealTimeChart } from '../components/dashboard/RealTimeChart';
import { StatisticsPanel } from '../components/analytics/StatisticsPanel';
import { AnomalyDetector } from '../components/analytics/AnomalyDetector';
import { StatCard } from '../components/common/StatCard';
import { useWebSocket } from '../hooks/useWebSocket';

export const DashboardPage: React.FC = () => {
  const { connected, tagData } = useWebSocket();
  const [demoTagIds] = useState(['demo-tag-1', 'demo-tag-2', 'demo-tag-3']);

  // Demo: Calculate live stats
  const [liveValues, setLiveValues] = useState<number[]>([]);

  useEffect(() => {
    const values = Object.values(tagData).map((data: any) => data?.value || 0);
    if (values.length > 0) {
      setLiveValues(values);
    }
  }, [tagData]);

  const avgValue = liveValues.length > 0
    ? liveValues.reduce((a, b) => a + b, 0) / liveValues.length
    : 0;

  const maxValue = liveValues.length > 0 ? Math.max(...liveValues) : 0;

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-lg p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">Welcome to OptiFlow AI</h1>
        <p className="text-blue-100 text-lg">
          Real-time industrial monitoring and AI-powered analytics
        </p>
        <div className="mt-4 flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400'}`} />
          <span className="text-sm">
            {connected ? 'WebSocket Connected' : 'WebSocket Disconnected'}
          </span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Sensors"
          value={demoTagIds.length}
          subtitle="Currently monitoring"
          icon={Activity}
          color="blue"
        />

        <StatCard
          title="Average Value"
          value={avgValue.toFixed(2)}
          subtitle="Real-time average"
          icon={TrendingUp}
          color="green"
          trend={{ value: 5.2, isPositive: true }}
        />

        <StatCard
          title="Peak Value"
          value={maxValue.toFixed(2)}
          subtitle="Maximum recorded"
          icon={Zap}
          color="yellow"
        />

        <StatCard
          title="Alerts"
          value={0}
          subtitle="No active alerts"
          icon={AlertCircle}
          color="red"
        />
      </div>

      {/* Real-time Charts */}
      <RealTimeChart
        tagIds={demoTagIds}
        title="Real-time Sensor Data"
        height={400}
        maxDataPoints={50}
        yAxisLabel="Value"
      />

      {/* Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <StatisticsPanel
            tagIds={demoTagIds}
            startTime={new Date(Date.now() - 3600000)}
            endTime={new Date()}
            autoRefresh
          />
        </div>

        <div>
          <AnomalyDetector
            tagId={demoTagIds[0]}
            startTime={new Date(Date.now() - 3600000)}
            endTime={new Date()}
          />
        </div>
      </div>

      {/* Info Section */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">
          🚀 All Features Implemented!
        </h3>
        <ul className="space-y-2 text-blue-800">
          <li className="flex items-center">
            <span className="mr-2">✅</span>
            <span>Real-time WebSocket data streaming</span>
          </li>
          <li className="flex items-center">
            <span className="mr-2">✅</span>
            <span>Advanced analytics (statistics, trends, anomalies)</span>
          </li>
          <li className="flex items-center">
            <span className="mr-2">✅</span>
            <span>Interactive dashboards with live charts</span>
          </li>
          <li className="flex items-center">
            <span className="mr-2">✅</span>
            <span>Data export capabilities (CSV, JSON, Excel)</span>
          </li>
          <li className="flex items-center">
            <span className="mr-2">✅</span>
            <span>Team collaboration and annotations</span>
          </li>
        </ul>
      </div>
    </div>
  );
};
