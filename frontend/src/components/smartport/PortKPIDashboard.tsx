/**
 * PortKPIDashboard Component
 *
 * Dashboard showing key performance indicators for the port
 */
import React from 'react';
import { PortKPIs } from '../../api/smartport';
import {
  Anchor,
  Ship,
  Package,
  Activity,
  Clock,
  TrendingUp,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';

interface PortKPIDashboardProps {
  kpis: PortKPIs | null;
  loading?: boolean;
}

export const PortKPIDashboard: React.FC<PortKPIDashboardProps> = ({ kpis, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-4" />
            <div className="h-8 bg-gray-200 rounded w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  if (!kpis) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center">
        <AlertCircle className="mx-auto h-12 w-12 text-gray-400" />
        <p className="mt-2 text-sm text-gray-500">No KPI data available</p>
      </div>
    );
  }

  const kpiCards = [
    {
      title: 'Total Berths',
      value: kpis.total_berths,
      icon: <Anchor className="h-6 w-6" />,
      color: 'bg-blue-500',
      subtitle: `${kpis.available_berths} available`,
    },
    {
      title: 'Berth Occupancy',
      value: `${kpis.berth_occupancy_rate.toFixed(1)}%`,
      icon: <Activity className="h-6 w-6" />,
      color: kpis.berth_occupancy_rate > 80 ? 'bg-red-500' : kpis.berth_occupancy_rate > 60 ? 'bg-yellow-500' : 'bg-green-500',
      subtitle: `${kpis.occupied_berths} occupied`,
    },
    {
      title: 'Total Vessels',
      value: kpis.total_vessels,
      icon: <Ship className="h-6 w-6" />,
      color: 'bg-indigo-500',
      subtitle: `${kpis.berthed_vessels} in port`,
    },
    {
      title: 'Approaching Vessels',
      value: kpis.approaching_vessels,
      icon: <TrendingUp className="h-6 w-6" />,
      color: 'bg-purple-500',
      subtitle: 'Expected arrivals',
    },
    {
      title: 'Active Operations',
      value: kpis.active_operations,
      icon: <Package className="h-6 w-6" />,
      color: 'bg-green-500',
      subtitle: 'In progress',
    },
    {
      title: 'Completed Today',
      value: kpis.completed_operations_today,
      icon: <CheckCircle className="h-6 w-6" />,
      color: 'bg-teal-500',
      subtitle: 'Operations finished',
    },
    {
      title: 'Containers Today',
      value: kpis.containers_handled_today.toLocaleString(),
      icon: <Package className="h-6 w-6" />,
      color: 'bg-orange-500',
      subtitle: 'TEU handled',
    },
    {
      title: 'Avg Berthing Time',
      value: `${kpis.average_berthing_time_hours.toFixed(1)}h`,
      icon: <Clock className="h-6 w-6" />,
      color: 'bg-cyan-500',
      subtitle: `Efficiency: ${kpis.operational_efficiency.toFixed(1)}%`,
    },
  ];

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map((kpi, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow"
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`${kpi.color} text-white p-3 rounded-lg`}>{kpi.icon}</div>
                <div className="text-right">
                  <p className="text-sm text-gray-600 font-medium">{kpi.title}</p>
                </div>
              </div>

              <div className="space-y-1">
                <p className="text-3xl font-bold text-gray-900">{kpi.value}</p>
                <p className="text-xs text-gray-500">{kpi.subtitle}</p>
              </div>
            </div>

            {/* Progress indicator at bottom for occupancy/efficiency metrics */}
            {(kpi.title === 'Berth Occupancy' || kpi.title === 'Avg Berthing Time') && (
              <div className="h-1 bg-gray-100">
                <div
                  className={`h-full ${kpi.color}`}
                  style={{
                    width: `${
                      kpi.title === 'Berth Occupancy'
                        ? kpis.berth_occupancy_rate
                        : kpis.operational_efficiency
                    }%`,
                  }}
                />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="mt-4 bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Port Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Berth utilization */}
          <div>
            <p className="text-sm text-gray-600 mb-2">Berth Utilization</p>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-green-600">Available</span>
                <span className="font-medium">{kpis.available_berths}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-red-600">Occupied</span>
                <span className="font-medium">{kpis.occupied_berths}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5 mt-2">
                <div
                  className="bg-blue-600 h-2.5 rounded-full"
                  style={{ width: `${kpis.berth_occupancy_rate}%` }}
                />
              </div>
            </div>
          </div>

          {/* Vessel traffic */}
          <div>
            <p className="text-sm text-gray-600 mb-2">Vessel Traffic</p>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-indigo-600">In Port</span>
                <span className="font-medium">{kpis.berthed_vessels}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-purple-600">Approaching</span>
                <span className="font-medium">{kpis.approaching_vessels}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Total</span>
                <span className="font-medium">{kpis.total_vessels}</span>
              </div>
            </div>
          </div>

          {/* Operations performance */}
          <div>
            <p className="text-sm text-gray-600 mb-2">Operations Performance</p>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-green-600">Active</span>
                <span className="font-medium">{kpis.active_operations}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-teal-600">Completed Today</span>
                <span className="font-medium">{kpis.completed_operations_today}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Efficiency</span>
                <span className="font-medium">{kpis.operational_efficiency.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
