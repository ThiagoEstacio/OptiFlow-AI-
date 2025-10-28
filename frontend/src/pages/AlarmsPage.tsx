/**
 * Alarms Management Page with Acknowledge
 */
import React, { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import { fetchAlarms, acknowledgeAlarm } from '../store/slices/alarmsSlice';
import { fetchTags } from '../store/slices/tagsSlice';
import { Alarm, AlarmSeverity } from '../types';
import { showToast } from '../utils/toast';
import { format } from 'date-fns';

export const AlarmsPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { items: alarms, loading } = useAppSelector((state) => state.alarms);
  const { items: tags } = useAppSelector((state) => state.tags);

  const [searchQuery, setSearchQuery] = useState('');
  const [filterSeverity, setFilterSeverity] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('active');

  useEffect(() => {
    dispatch(fetchAlarms());
    dispatch(fetchTags());
  }, [dispatch]);

  const handleAcknowledge = async (alarm: Alarm) => {
    try {
      await dispatch(acknowledgeAlarm(alarm.id)).unwrap();
      showToast.success('Alarm acknowledged successfully!');
      dispatch(fetchAlarms());
    } catch (error: any) {
      showToast.error(error.message || 'Failed to acknowledge alarm');
    }
  };

  const getTagName = (tagId: string) => {
    return tags.find((t) => t.id === tagId)?.name || tagId;
  };

  const getSeverityColor = (severity: AlarmSeverity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeverityIcon = (severity: AlarmSeverity) => {
    switch (severity) {
      case 'critical':
        return '🔴';
      case 'high':
        return '🟠';
      case 'medium':
        return '🟡';
      case 'low':
        return '🔵';
      default:
        return '⚪';
    }
  };

  const filteredAlarms = alarms.filter((alarm) => {
    const matchesSearch =
      alarm.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (alarm.tag_id && getTagName(alarm.tag_id).toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesSeverity = !filterSeverity || alarm.severity === filterSeverity;

    const matchesStatus =
      !filterStatus ||
      (filterStatus === 'active' && alarm.status === 'active') ||
      (filterStatus === 'acknowledged' && alarm.status === 'acknowledged') ||
      (filterStatus === 'resolved' && alarm.status === 'resolved');

    return matchesSearch && matchesSeverity && matchesStatus;
  });

  const activeAlarms = alarms.filter((a) => a.status === 'active');
  const acknowledgedAlarms = alarms.filter((a) => a.status === 'acknowledged');
  const resolvedAlarms = alarms.filter((a) => a.status === 'resolved');

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Alarms</h1>
          <p className="text-gray-600 mt-1">Monitor and manage system alarms</p>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Alarms</p>
              <p className="text-3xl font-bold text-red-600 mt-2">{activeAlarms.length}</p>
            </div>
            <div className="text-4xl">🔔</div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Acknowledged</p>
              <p className="text-3xl font-bold text-yellow-600 mt-2">{acknowledgedAlarms.length}</p>
            </div>
            <div className="text-4xl">✓</div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Resolved</p>
              <p className="text-3xl font-bold text-green-600 mt-2">{resolvedAlarms.length}</p>
            </div>
            <div className="text-4xl">✅</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 space-y-4">
        <input
          type="text"
          placeholder="Search alarms by message or tag..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Severity
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Message
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tag
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredAlarms.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                  {searchQuery || filterSeverity || filterStatus
                    ? 'No alarms found matching your filters.'
                    : 'No alarms found.'}
                </td>
              </tr>
            ) : (
              filteredAlarms.map((alarm) => (
                <tr key={alarm.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <span className="text-xl">{getSeverityIcon(alarm.severity)}</span>
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getSeverityColor(
                          alarm.severity
                        )}`}
                      >
                        {alarm.severity.toUpperCase()}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">{alarm.message}</div>
                    {alarm.tag_id && (
                      <div className="text-sm text-gray-500">Value: {alarm.value}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {alarm.tag_id ? getTagName(alarm.tag_id) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {format(new Date(alarm.triggered_at), 'MMM d, yyyy')}
                    </div>
                    <div className="text-sm text-gray-500">
                      {format(new Date(alarm.triggered_at), 'HH:mm:ss')}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        alarm.status === 'active'
                          ? 'bg-red-100 text-red-800'
                          : alarm.status === 'acknowledged'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-green-100 text-green-800'
                      }`}
                    >
                      {alarm.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {alarm.status === 'active' && (
                      <button
                        onClick={() => handleAcknowledge(alarm)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Acknowledge
                      </button>
                    )}
                    {alarm.status === 'acknowledged' && (
                      <span className="text-gray-400">Acknowledged</span>
                    )}
                    {alarm.status === 'resolved' && (
                      <span className="text-green-600">Resolved</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
