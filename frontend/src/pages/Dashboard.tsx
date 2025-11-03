/**
 * SmartPort Dashboard
 */
import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import { fetchSites } from '../store/slices/sitesSlice';
import { fetchDevices } from '../store/slices/devicesSlice';
import { fetchActiveAlarms } from '../store/slices/alarmsSlice';
import { StatCard } from '../components/Dashboard/StatCard';

export const Dashboard: React.FC = () => {
  const dispatch = useAppDispatch();
  const sites = useAppSelector((state) => state.sites.items);
  const devices = useAppSelector((state) => state.devices.items);
  const activeAlarms = useAppSelector((state) => state.alarms.activeAlarms);

  useEffect(() => {
    dispatch(fetchSites({ site_type: 'smartport' }));
    dispatch(fetchDevices());
    dispatch(fetchActiveAlarms());
  }, [dispatch]);

  const activeDevices = devices.filter((d) => d.enabled && d.status === 'connected');
  const smartportSites = sites.filter((s) => s.site_type === 'smartport');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">SmartPort Dashboard</h1>
        <p className="text-gray-600 mt-1">Real-time monitoring and analytics</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="SmartPort Sites"
          value={smartportSites.length}
          icon="🏭"
          color="blue"
          subtitle="Active sites"
        />
        <StatCard
          title="Active Devices"
          value={activeDevices.length}
          icon="🔌"
          color="green"
          subtitle={`${devices.length} total`}
        />
        <StatCard
          title="Data Points Today"
          value="24.5K"
          icon="📊"
          color="blue"
          subtitle="+12% vs yesterday"
        />
        <StatCard
          title="Active Alarms"
          value={activeAlarms.length}
          icon="🚨"
          color={activeAlarms.length > 0 ? 'red' : 'green'}
          subtitle={activeAlarms.length > 0 ? 'Needs attention' : 'All clear'}
        />
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Sites */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Sites</h2>
          {smartportSites.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No SmartPort sites found</p>
          ) : (
            <div className="space-y-3">
              {smartportSites.slice(0, 5).map((site) => (
                <div key={site.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{site.name}</p>
                    <p className="text-sm text-gray-500">{site.city}, {site.country}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    site.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {site.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Active Alarms */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Active Alarms</h2>
          {activeAlarms.length === 0 ? (
            <div className="text-center py-8">
              <span className="text-6xl">✅</span>
              <p className="text-gray-500 mt-2">No active alarms</p>
            </div>
          ) : (
            <div className="space-y-3">
              {activeAlarms.slice(0, 5).map((alarm) => (
                <div key={alarm.id} className="flex items-start space-x-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <span className="text-2xl">🚨</span>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{alarm.message}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(alarm.triggered_at).toLocaleString()}
                    </p>
                  </div>
                  <button className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700">
                    Ack
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Device Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Device Status</h2>
        {devices.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No devices configured</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {devices.slice(0, 6).map((device) => (
              <div key={device.id} className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-medium text-gray-900">{device.name}</h3>
                  <span className={`w-3 h-3 rounded-full ${
                    device.status === 'connected' ? 'bg-green-500' : 'bg-gray-300'
                  }`}></span>
                </div>
                <p className="text-sm text-gray-600">{device.protocol.toUpperCase()}</p>
                <p className="text-xs text-gray-500 mt-1">{device.ip_address}</p>
                {device.last_seen && (
                  <p className="text-xs text-gray-400 mt-2">
                    Last seen: {new Date(device.last_seen).toLocaleString()}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            Add New Site
          </button>
          <button className="px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-lg hover:bg-blue-50 transition-colors">
            Configure Device
          </button>
          <button className="px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-lg hover:bg-blue-50 transition-colors">
            View Reports
          </button>
          <button className="px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-lg hover:bg-blue-50 transition-colors">
            Export Data
          </button>
        </div>
      </div>
    </div>
  );
};
