/**
 * Main Dashboard Component
 */
import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import wsService from '../services/websocket';

interface Stats {
  totalDevices: number;
  activeDevices: number;
  totalTags: number;
  activeAlarms: number;
}

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats>({
    totalDevices: 0,
    activeDevices: 0,
    totalTags: 0,
    activeAlarms: 0,
  });
  const [devices, setDevices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    connectWebSocket();

    return () => {
      wsService.disconnect();
    };
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Load devices
      const devicesData = await apiClient.getDevices();
      setDevices(devicesData);

      // Calculate stats
      const activeDevices = devicesData.filter((d: any) => d.status === 'connected').length;

      setStats({
        totalDevices: devicesData.length,
        activeDevices: activeDevices,
        totalTags: 0, // Would load from API
        activeAlarms: 0, // Would load from API
      });
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    const token = localStorage.getItem('access_token');
    wsService.connect(token || undefined);

    // Subscribe to device status updates
    wsService.subscribe('device_status', (data) => {
      console.log('Device status update:', data);
      // Update device list in real-time
      setDevices((prev) =>
        prev.map((d) =>
          d.id === data.device_id ? { ...d, status: data.status } : d
        )
      );
    });

    // Subscribe to alarms
    wsService.subscribe('alarm', (data) => {
      console.log('New alarm:', data);
      // Show notification or update alarm list
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          OptiFlow Dashboard
        </h1>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="Total Devices"
            value={stats.totalDevices}
            icon="🔌"
            color="blue"
          />
          <StatsCard
            title="Active Devices"
            value={stats.activeDevices}
            icon="✅"
            color="green"
          />
          <StatsCard
            title="Total Tags"
            value={stats.totalTags}
            icon="🏷️"
            color="purple"
          />
          <StatsCard
            title="Active Alarms"
            value={stats.activeAlarms}
            icon="🚨"
            color="red"
          />
        </div>

        {/* Devices List */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Devices</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Protocol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {devices.map((device) => (
                  <tr key={device.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {device.name}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">
                        {device.protocol.toUpperCase()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          device.status === 'connected'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {device.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <button className="text-blue-600 hover:text-blue-900">
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

interface StatsCardProps {
  title: string;
  value: number;
  icon: string;
  color: 'blue' | 'green' | 'purple' | 'red';
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon, color }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    red: 'bg-red-50 text-red-600',
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
        </div>
        <div className={`text-4xl ${colorClasses[color]} p-3 rounded-lg`}>
          {icon}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
