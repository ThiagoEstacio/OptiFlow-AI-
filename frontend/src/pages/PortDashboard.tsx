/**
 * PortDashboard - Main dashboard page for SmartPort
 * Shows KPIs, real-time charts, berths, and equipment status
 */
import { useEffect, useState } from 'react';
import { KPICard } from '@/components/port/KPICard';
import { BerthCard } from '@/components/port/BerthCard';
import { EquipmentCard } from '@/components/port/EquipmentCard';
import { Card } from '@/components/ui/Card';
import { SkeletonKPICard } from '@/components/ui/Skeleton';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  Package,
  TrendingUp,
  Ship,
  AlertTriangle,
  Activity,
} from 'lucide-react';
import type { PortKPI, Berth, PortEquipment, TrendData } from '@/types/port';
import { portAPI } from '@/services/portService';
import { formatNumber } from '@/lib/utils';

export function PortDashboard() {
  // State
  const [kpis, setKpis] = useState<PortKPI | null>(null);
  const [berths, setBerths] = useState<Berth[]>([]);
  const [criticalEquipment, setCriticalEquipment] = useState<PortEquipment[]>([]);
  const [trendData, setTrendData] = useState<TrendData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch dashboard data
  useEffect(() => {
    fetchDashboardData();
    // Set up auto-refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setError(null);

      // Calculate date range (last 30 days)
      const toDate = new Date();
      const fromDate = new Date();
      fromDate.setDate(fromDate.getDate() - 30);

      // Fetch all data in parallel
      const [kpisData, berthsData, equipmentData, trendsData] = await Promise.all([
        portAPI.analytics.getKPIs(fromDate.toISOString(), toDate.toISOString()),
        portAPI.berths.list(),
        portAPI.equipment.list({ max_failure_probability: 30 }), // Get at-risk equipment
        portAPI.analytics.getTrends(
          'loading_rate,energy_consumption',
          'hour',
          new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(), // Last 48 hours
          toDate.toISOString()
        ),
      ]);

      setKpis(kpisData);
      setBerths(berthsData);
      setCriticalEquipment(equipmentData.items?.slice(0, 3) || []); // Top 3 critical
      setTrendData(trendsData);
    } catch (err: any) {
      console.error('Error fetching dashboard data:', err);
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  // Mock chart data (for demo when API is not available)
  const mockChartData = [
    { time: '00:00', loading_rate: 1850, energy: 420 },
    { time: '04:00', loading_rate: 1920, energy: 438 },
    { time: '08:00', loading_rate: 1780, energy: 405 },
    { time: '12:00', loading_rate: 1950, energy: 445 },
    { time: '16:00', loading_rate: 1820, energy: 415 },
    { time: '20:00', loading_rate: 1890, energy: 430 },
    { time: '24:00', loading_rate: 1860, energy: 425 },
    { time: '28:00', loading_rate: 1910, energy: 435 },
    { time: '32:00', loading_rate: 1830, energy: 418 },
    { time: '36:00', loading_rate: 1880, energy: 428 },
    { time: '40:00', loading_rate: 1850, energy: 422 },
    { time: '44:00', loading_rate: 1900, energy: 433 },
    { time: '48:00', loading_rate: 1870, energy: 427 },
  ];

  const chartData = trendData.length > 0 ? trendData : mockChartData;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-dark-100">Port Dashboard</h1>
        <p className="mt-1 text-sm text-dark-400">
          Real-time monitoring and analytics for port operations
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-lg border border-danger-500/30 bg-danger-500/10 p-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-danger-500" />
            <p className="text-sm text-danger-500">{error}</p>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {loading ? (
          <>
            <SkeletonKPICard />
            <SkeletonKPICard />
            <SkeletonKPICard />
            <SkeletonKPICard />
          </>
        ) : (
          <>
            <KPICard
              title="Total Throughput"
              value={kpis?.total_throughput_tons || 0}
              unit="tons"
              format="number"
              icon={<Package className="h-6 w-6" />}
              variant="primary"
              trend={{
                value: 8.5,
                period: 'vs last month',
              }}
            />
            <KPICard
              title="Average Efficiency"
              value={kpis?.average_efficiency || 0}
              format="percent"
              decimals={1}
              icon={<TrendingUp className="h-6 w-6" />}
              variant="success"
              trend={{
                value: 3.2,
                period: 'vs last month',
              }}
            />
            <KPICard
              title="Vessels Processed"
              value={kpis?.total_vessels_processed || 0}
              icon={<Ship className="h-6 w-6" />}
              variant="info"
              trend={{
                value: 5.0,
                period: 'vs last month',
              }}
            />
            <KPICard
              title="Critical Alerts"
              value={criticalEquipment.length}
              icon={<AlertTriangle className="h-6 w-6" />}
              variant="danger"
            />
          </>
        )}
      </div>

      {/* Real-Time Chart */}
      <Card
        title="Real-Time Performance (Last 48h)"
        subtitle="Loading rate and energy consumption trends"
      >
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="time"
              stroke="#94a3b8"
              style={{ fontSize: '12px' }}
            />
            <YAxis
              yAxisId="left"
              stroke="#3b82f6"
              style={{ fontSize: '12px' }}
              label={{
                value: 'Loading Rate (t/h)',
                angle: -90,
                position: 'insideLeft',
                style: { fill: '#94a3b8', fontSize: '12px' },
              }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="#22c55e"
              style={{ fontSize: '12px' }}
              label={{
                value: 'Energy (kW)',
                angle: 90,
                position: 'insideRight',
                style: { fill: '#94a3b8', fontSize: '12px' },
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#f1f5f9',
              }}
              formatter={(value: number) => formatNumber(value, 0)}
            />
            <Legend
              wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }}
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="loading_rate"
              name="Loading Rate (t/h)"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="energy"
              name="Energy (kW)"
              stroke="#22c55e"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* Berths and Equipment Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Berths Status */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-dark-100">
              Berth Status
            </h2>
            <span className="text-sm text-dark-400">
              {berths.filter((b) => b.status === 'available').length} of{' '}
              {berths.length} available
            </span>
          </div>

          <div className="grid gap-4">
            {loading ? (
              <>
                <SkeletonKPICard />
                <SkeletonKPICard />
              </>
            ) : berths.length > 0 ? (
              berths.map((berth) => (
                <BerthCard
                  key={berth.id}
                  berth={berth}
                  vesselName={
                    berth.status === 'occupied'
                      ? 'MV GRAIN CARRIER'
                      : undefined
                  }
                  operationProgress={
                    berth.status === 'occupied' ? 65 : undefined
                  }
                />
              ))
            ) : (
              <Card>
                <p className="text-center text-sm text-dark-400">
                  No berths configured
                </p>
              </Card>
            )}
          </div>
        </div>

        {/* Critical Equipment */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-dark-100">
              Critical Equipment
            </h2>
            <span className="text-sm text-dark-400">
              {criticalEquipment.length} items need attention
            </span>
          </div>

          <div className="grid gap-4">
            {loading ? (
              <>
                <SkeletonKPICard />
                <SkeletonKPICard />
                <SkeletonKPICard />
              </>
            ) : criticalEquipment.length > 0 ? (
              criticalEquipment.map((equipment) => (
                <EquipmentCard key={equipment.id} equipment={equipment} />
              ))
            ) : (
              <Card>
                <div className="flex flex-col items-center justify-center py-8">
                  <Activity className="h-12 w-12 text-success-500" />
                  <p className="mt-3 text-sm font-medium text-dark-200">
                    All Equipment Healthy
                  </p>
                  <p className="mt-1 text-xs text-dark-400">
                    No critical alerts at this time
                  </p>
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Current Operations Summary */}
      {kpis && (
        <Card title="Operations Summary" subtitle="Current period statistics">
          <div className="grid gap-6 md:grid-cols-3 lg:grid-cols-5">
            <div>
              <p className="text-sm text-dark-400">Operations In Progress</p>
              <p className="mt-1 text-2xl font-bold text-success-500">
                {kpis.operations_in_progress}
              </p>
            </div>
            <div>
              <p className="text-sm text-dark-400">Completed Operations</p>
              <p className="mt-1 text-2xl font-bold text-dark-100">
                {kpis.operations_completed}
              </p>
            </div>
            <div>
              <p className="text-sm text-dark-400">Average Loading Rate</p>
              <p className="mt-1 text-2xl font-bold text-primary-500">
                {formatNumber(kpis.average_loading_rate, 0)} <span className="text-sm text-dark-400">t/h</span>
              </p>
            </div>
            <div>
              <p className="text-sm text-dark-400">Vessels at Berth</p>
              <p className="mt-1 text-2xl font-bold text-info-500">
                {kpis.vessels_at_berth}
              </p>
            </div>
            <div>
              <p className="text-sm text-dark-400">Avg Turnaround Time</p>
              <p className="mt-1 text-2xl font-bold text-dark-100">
                {kpis.average_turnaround_time_hours
                  ? formatNumber(kpis.average_turnaround_time_hours, 1)
                  : 'N/A'}{' '}
                <span className="text-sm text-dark-400">hrs</span>
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
