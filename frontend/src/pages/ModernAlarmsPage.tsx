/**
 * 🚨 Modern Alarms Page - Complete & Enhanced
 * ==========================================
 * 
 * Features:
 * - Real-time active alarms monitoring
 * - Comprehensive statistics dashboard
 * - History with advanced filters
 * - Top alarms analytics
 * - Acknowledge/Clear functionality
 * - Visual charts and graphs
 */

import React, { useEffect, useState } from 'react';
import {
  alarmsApi,
  AlarmEvent,
  AlarmStatistics,
  TopAlarm,
  getSeverityColor,
  getSeverityIcon,
  getStateColor,
  formatDuration,
} from '../services/alarms.api';
import { format, subDays } from 'date-fns';
import { showToast } from '../utils/toast';

type TabType = 'active' | 'history' | 'statistics';

export const ModernAlarmsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('active');
  const [loading, setLoading] = useState(false);
  
  // Active alarms
  const [activeAlarms, setActiveAlarms] = useState<AlarmEvent[]>([]);
  
  // History
  const [historyAlarms, setHistoryAlarms] = useState<AlarmEvent[]>([]);
  const [historyFilters, setHistoryFilters] = useState({
    start_date: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
    end_date: format(new Date(), 'yyyy-MM-dd'),
    severity: '',
    state: '',
  });
  
  // Statistics
  const [statistics, setStatistics] = useState<AlarmStatistics | null>(null);
  const [topAlarms, setTopAlarms] = useState<TopAlarm[]>([]);

  // Filters for active alarms
  const [activeSeverityFilter, setActiveSeverityFilter] = useState('');

  // ========================================
  // 📡 DATA FETCHING
  // ========================================

  const fetchActiveAlarms = async () => {
    try {
      setLoading(true);
      const data = await alarmsApi.getActiveAlarms({
        severity: activeSeverityFilter || undefined,
      });
      setActiveAlarms(data);
    } catch (error) {
      console.error('Error fetching active alarms:', error);
      showToast.error('Failed to fetch active alarms');
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const data = await alarmsApi.getHistory({
        start_date: historyFilters.start_date,
        end_date: historyFilters.end_date,
        severity: historyFilters.severity || undefined,
        state: historyFilters.state || undefined,
        limit: 100,
      });
      setHistoryAlarms(data);
    } catch (error) {
      console.error('Error fetching alarm history:', error);
      showToast.error('Failed to fetch alarm history');
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      setLoading(true);
      const [stats, top] = await Promise.all([
        alarmsApi.getStatistics(),
        alarmsApi.getTopAlarms(10),
      ]);
      setStatistics(stats);
      setTopAlarms(top);
    } catch (error) {
      console.error('Error fetching statistics:', error);
      showToast.error('Failed to fetch statistics');
    } finally {
      setLoading(false);
    }
  };

  // ========================================
  // 🔄 ACTIONS
  // ========================================

  const handleAcknowledge = async (alarmId: string) => {
    try {
      await alarmsApi.acknowledgeAlarm(alarmId, {
        user_id: 'current_user', // TODO: Get from auth context
        comment: 'Acknowledged from UI',
      });
      showToast.success('Alarm acknowledged successfully');
      fetchActiveAlarms();
    } catch (error) {
      console.error('Error acknowledging alarm:', error);
      showToast.error('Failed to acknowledge alarm');
    }
  };

  const handleClear = async (alarmId: string) => {
    try {
      await alarmsApi.clearAlarm(alarmId);
      showToast.success('Alarm cleared successfully');
      fetchActiveAlarms();
    } catch (error) {
      console.error('Error clearing alarm:', error);
      showToast.error('Failed to clear alarm');
    }
  };

  // ========================================
  // 🎣 EFFECTS
  // ========================================

  useEffect(() => {
    if (activeTab === 'active') {
      fetchActiveAlarms();
      // Auto-refresh every 10 seconds
      const interval = setInterval(fetchActiveAlarms, 10000);
      return () => clearInterval(interval);
    } else if (activeTab === 'history') {
      fetchHistory();
    } else if (activeTab === 'statistics') {
      fetchStatistics();
    }
  }, [activeTab, activeSeverityFilter, historyFilters]);

  // ========================================
  // 🎨 RENDER FUNCTIONS
  // ========================================

  const renderActiveTab = () => (
    <div className="space-y-4">
      {/* Filter */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium text-gray-700">Filter by Severity:</label>
          <select
            value={activeSeverityFilter}
            onChange={(e) => setActiveSeverityFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <div className="flex-1"></div>
          <div className="text-sm text-gray-600">
            Auto-refresh: <span className="text-green-600 font-medium">ON</span> (10s)
          </div>
        </div>
      </div>

      {/* Active Alarms Count */}
      <div className="bg-gradient-to-r from-red-50 to-orange-50 border-l-4 border-red-500 rounded-lg shadow p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">🚨</span>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Active Alarms</h3>
              <p className="text-sm text-gray-600">Requiring attention</p>
            </div>
          </div>
          <div className="text-4xl font-bold text-red-600">{activeAlarms.length}</div>
        </div>
      </div>

      {/* Alarms Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : activeAlarms.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <span className="text-5xl">✅</span>
            <p className="mt-4 text-lg font-medium">No active alarms</p>
            <p className="text-sm">All systems operating normally</p>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Severity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Message
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Tag ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Trigger Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  State
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {activeAlarms.map((alarm) => (
                <tr key={alarm.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl">{getSeverityIcon(alarm.severity)}</span>
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full border ${getSeverityColor(
                          alarm.severity
                        )}`}
                      >
                        {alarm.severity.toUpperCase()}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">{alarm.message}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-mono">
                    {alarm.tag_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {format(new Date(alarm.trigger_timestamp), 'MMM d, yyyy')}
                    </div>
                    <div className="text-xs text-gray-500">
                      {format(new Date(alarm.trigger_timestamp), 'HH:mm:ss')}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {alarm.trigger_value?.toFixed(2) || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${getStateColor(
                        alarm.state
                      )}`}
                    >
                      {alarm.state.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm space-x-2">
                    {alarm.state === 'active' && (
                      <>
                        <button
                          onClick={() => handleAcknowledge(alarm.id)}
                          className="text-blue-600 hover:text-blue-900 font-medium"
                        >
                          Acknowledge
                        </button>
                        <button
                          onClick={() => handleClear(alarm.id)}
                          className="text-green-600 hover:text-green-900 font-medium"
                        >
                          Clear
                        </button>
                      </>
                    )}
                    {alarm.state === 'acknowledged' && (
                      <button
                        onClick={() => handleClear(alarm.id)}
                        className="text-green-600 hover:text-green-900 font-medium"
                      >
                        Clear
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );

  const renderHistoryTab = () => (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
            <input
              type="date"
              value={historyFilters.start_date}
              onChange={(e) =>
                setHistoryFilters({ ...historyFilters, start_date: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
            <input
              type="date"
              value={historyFilters.end_date}
              onChange={(e) => setHistoryFilters({ ...historyFilters, end_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
            <select
              value={historyFilters.severity}
              onChange={(e) => setHistoryFilters({ ...historyFilters, severity: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
            <select
              value={historyFilters.state}
              onChange={(e) => setHistoryFilters({ ...historyFilters, state: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All</option>
              <option value="active">Active</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="cleared">Cleared</option>
            </select>
          </div>
        </div>
      </div>

      {/* History Count */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="text-sm text-gray-600">
          Showing <span className="font-bold text-gray-900">{historyAlarms.length}</span> alarm
          events
        </div>
      </div>

      {/* History Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : historyAlarms.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">No alarm events found for the selected filters</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Severity
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Message
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Trigger Time
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Cleared Time
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Duration
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    State
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {historyAlarms.map((alarm) => (
                  <tr key={alarm.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <span className="text-xl">{getSeverityIcon(alarm.severity)}</span>
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(
                            alarm.severity
                          )}`}
                        >
                          {alarm.severity.toUpperCase()}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">{alarm.message}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                      {format(new Date(alarm.trigger_timestamp), 'MMM d, HH:mm:ss')}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                      {alarm.cleared_at
                        ? format(new Date(alarm.cleared_at), 'MMM d, HH:mm:ss')
                        : '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 font-medium">
                      {formatDuration(alarm.duration_seconds)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${getStateColor(
                          alarm.state
                        )}`}
                      >
                        {alarm.state.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );

  const renderStatisticsTab = () => (
    <div className="space-y-6">
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <>
          {/* Overview Cards */}
          {statistics && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Alarms</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{statistics.total}</p>
                  </div>
                  <div className="text-4xl">📊</div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Active</p>
                    <p className="text-3xl font-bold text-red-600 mt-2">{statistics.active}</p>
                  </div>
                  <div className="text-4xl">🔴</div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Acknowledged</p>
                    <p className="text-3xl font-bold text-yellow-600 mt-2">
                      {statistics.acknowledged}
                    </p>
                  </div>
                  <div className="text-4xl">🟡</div>
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Cleared</p>
                    <p className="text-3xl font-bold text-green-600 mt-2">{statistics.cleared}</p>
                  </div>
                  <div className="text-4xl">✅</div>
                </div>
              </div>
            </div>
          )}

          {/* By Severity & Average Duration */}
          {statistics && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Severity Distribution */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">By Severity</h3>
                <div className="space-y-3">
                  {Object.entries(statistics.by_severity).map(([severity, count]) => (
                    <div key={severity} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-xl">{getSeverityIcon(severity)}</span>
                        <span className="text-sm font-medium text-gray-700 capitalize">
                          {severity}
                        </span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              severity === 'critical'
                                ? 'bg-red-500'
                                : severity === 'high'
                                ? 'bg-orange-500'
                                : severity === 'medium'
                                ? 'bg-yellow-500'
                                : 'bg-blue-500'
                            }`}
                            style={{ width: `${(count / statistics.total) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-bold text-gray-900 w-8 text-right">
                          {count}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Average Duration & Type Distribution */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h3>
                <div className="space-y-4">
                  <div className="border-l-4 border-blue-500 pl-4">
                    <p className="text-sm text-gray-600">Average Duration</p>
                    <p className="text-3xl font-bold text-blue-600 mt-1">
                      {statistics.average_duration_minutes.toFixed(1)} min
                    </p>
                  </div>
                  <div className="mt-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">By Type</p>
                    <div className="space-y-2">
                      {Object.entries(statistics.by_type).map(([type, count]) => (
                        <div key={type} className="flex justify-between text-sm">
                          <span className="text-gray-600 capitalize">{type.replace('_', ' ')}</span>
                          <span className="font-medium text-gray-900">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Top Alarms */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Top 10 Most Frequent Alarms
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Rank
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Alarm Name
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Severity
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Occurrences
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {topAlarms.map((alarm, index) => (
                    <tr key={alarm.alarm_definition_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="text-lg font-bold text-gray-400">#{index + 1}</span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm font-medium text-gray-900">{alarm.name}</div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(
                            alarm.severity
                          )}`}
                        >
                          {alarm.severity.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        <span className="text-lg font-bold text-gray-900">{alarm.count}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );

  // ========================================
  // 🎨 MAIN RENDER
  // ========================================

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">🚨 Alarms Management</h1>
          <p className="text-gray-600 mt-1">Monitor, analyze, and manage system alarms</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            <button
              onClick={() => setActiveTab('active')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'active'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="flex items-center space-x-2">
                <span>🔴</span>
                <span>Active Alarms</span>
                {activeAlarms.length > 0 && (
                  <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs font-bold">
                    {activeAlarms.length}
                  </span>
                )}
              </span>
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'history'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="flex items-center space-x-2">
                <span>📜</span>
                <span>History</span>
              </span>
            </button>
            <button
              onClick={() => setActiveTab('statistics')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'statistics'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="flex items-center space-x-2">
                <span>📊</span>
                <span>Statistics</span>
              </span>
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'active' && renderActiveTab()}
          {activeTab === 'history' && renderHistoryTab()}
          {activeTab === 'statistics' && renderStatisticsTab()}
        </div>
      </div>
    </div>
  );
};
