/**
 * SmartPort Dashboard - Enhanced with Real-Time Data
 */
import React, { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import { fetchSites } from '../store/slices/sitesSlice';
import { fetchDevices } from '../store/slices/devicesSlice';
import { fetchActiveAlarms } from '../store/slices/alarmsSlice';
import { StatCard } from '../components/Dashboard/StatCard';
import apiClient from '../api/client';
import { Tag } from '../types';

export const Dashboard: React.FC = () => {
  const dispatch = useAppDispatch();
  const sites = useAppSelector((state) => state.sites.items);
  const devices = useAppSelector((state) => state.devices.items);
  const activeAlarms = useAppSelector((state) => state.alarms.activeAlarms);
  
  const [activeTags, setActiveTags] = useState<Tag[]>([]);
  const [dataPointsToday, setDataPointsToday] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dispatch(fetchSites({ site_type: 'smartport' }));
    dispatch(fetchDevices({}));
    dispatch(fetchActiveAlarms());
    loadActiveTags();
    
    // Refresh active tags every 30 seconds
    const interval = setInterval(loadActiveTags, 30000);
    return () => clearInterval(interval);
  }, [dispatch]);

  const loadActiveTags = async () => {
    try {
      const tags = await apiClient.getTags();
      setActiveTags(tags);
      
      // Estimate data points (tags * updates per minute * minutes in day)
      const estimatedPoints = tags.length * 60 * 1440; // Assuming 1 update/sec
      setDataPointsToday(estimatedPoints);
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading active tags:', error);
      setLoading(false);
    }
  };

  const activeDevices = devices.filter((d) => d.status === 'CONNECTED' || d.status === 'ONLINE');
  const smartportSites = sites.filter((s) => s.site_type === 'smartport');
  
  // Format large numbers
  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

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
          title="Active Tags"
          value={activeTags.length}
          icon="📡"
          color="blue"
          subtitle="Real-time data streams"
        />
        <StatCard
          title="Connected Devices"
          value={activeDevices.length}
          icon="🔌"
          color="green"
          subtitle={`${devices.length} total devices`}
        />
        <StatCard
          title="Data Points Today"
          value={formatNumber(dataPointsToday)}
          icon="📊"
          color="blue"
          subtitle="Estimated data collection"
        />
        <StatCard
          title="Active Alarms"
          value={activeAlarms.length}
          icon="🚨"
          color={activeAlarms.length > 0 ? 'red' : 'green'}
          subtitle={activeAlarms.length > 0 ? 'Needs attention' : 'All systems normal'}
        />
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Tags - Real-Time Values */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              📡 Live Tag Values
            </h2>
            <span className="flex items-center text-sm text-green-600 dark:text-green-400">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
              Live
            </span>
          </div>
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-gray-500 dark:text-gray-400 mt-2">Loading data...</p>
            </div>
          ) : activeTags.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400 text-center py-8">No active tags found</p>
          ) : (
            <div className="space-y-3">
              {activeTags.slice(0, 6).map((tag) => (
                <div key={tag.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 dark:text-white text-sm">
                      {tag.name || tag.id}
                    </p>
                    {tag.description && (
                      <p className="text-xs text-gray-500 dark:text-gray-400">{tag.description}</p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-blue-600 dark:text-blue-400">
                      {tag.last_value !== null && tag.last_value !== undefined
                        ? typeof tag.last_value === 'number'
                          ? tag.last_value.toFixed(2)
                          : tag.last_value
                        : 'N/A'}
                    </p>
                    {tag.last_timestamp && (
                      <p className="text-xs text-gray-400">
                        {new Date(tag.last_timestamp).toLocaleTimeString()}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Sites */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Sites</h2>
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
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Active Alarms</h2>
          {activeAlarms.length === 0 ? (
            <div className="text-center py-8">
              <span className="text-6xl">✅</span>
              <p className="text-gray-500 dark:text-gray-400 mt-2">No active alarms</p>
            </div>
          ) : (
            <div className="space-y-3">
              {activeAlarms.slice(0, 5).map((alarm) => (
                <div key={alarm.id} className="flex items-start space-x-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <span className="text-2xl">🚨</span>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 dark:text-white">{alarm.message}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {new Date(alarm.triggered_at).toLocaleString()}
                    </p>
                  </div>
                  <button className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors">
                    Ack
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Device Status */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Connected Devices</h2>
        {devices.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">No devices configured</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {devices.slice(0, 6).map((device) => {
              const isOnline = device.status === 'CONNECTED' || device.status === 'ONLINE';
              return (
                <div
                  key={device.id}
                  className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md dark:hover:shadow-gray-900/50 transition-shadow bg-white dark:bg-gray-750"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-medium text-gray-900 dark:text-white">{device.name}</h3>
                    <span
                      className={`w-3 h-3 rounded-full ${
                        isOnline ? 'bg-green-500 animate-pulse' : 'bg-gray-400 dark:bg-gray-600'
                      }`}
                      title={isOnline ? 'Online' : 'Offline'}
                    ></span>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {device.protocol?.toUpperCase() || 'N/A'}
                    </p>
                    {device.connection_config && typeof device.connection_config === 'object' && 'endpoint' in device.connection_config && (
                      <p className="text-xs text-gray-500 dark:text-gray-500 font-mono truncate">
                        {String(device.connection_config.endpoint)}
                      </p>
                    )}
                    {device.last_seen && (
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                        Last: {new Date(device.last_seen).toLocaleTimeString()}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
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
