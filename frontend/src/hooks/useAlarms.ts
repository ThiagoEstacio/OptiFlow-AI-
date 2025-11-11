/**
 * 🎣 useAlarms Hook - React Hook for Alarms API
 * ==============================================
 * 
 * Custom hook to manage alarms state and operations
 */

import { useState, useEffect, useCallback } from 'react';
import {
  alarmsApi,
  AlarmEvent,
  AlarmStatistics,
  TopAlarm,
} from '../services/alarms.api';
import { showToast } from '../utils/toast';

export interface UseAlarmsOptions {
  autoRefresh?: boolean;
  refreshInterval?: number; // in milliseconds
}

export const useAlarms = (options: UseAlarmsOptions = {}) => {
  const { autoRefresh = false, refreshInterval = 10000 } = options;

  const [activeAlarms, setActiveAlarms] = useState<AlarmEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchActiveAlarms = useCallback(async (severity?: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await alarmsApi.getActiveAlarms({ severity });
      setActiveAlarms(data);
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to fetch active alarms';
      setError(errorMsg);
      console.error('Error fetching active alarms:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const acknowledgeAlarm = useCallback(async (alarmId: string, comment?: string) => {
    try {
      await alarmsApi.acknowledgeAlarm(alarmId, {
        comment,
        user_id: 'current_user', // TODO: Get from auth context
      });
      showToast.success('Alarm acknowledged successfully');
      await fetchActiveAlarms();
      return true;
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to acknowledge alarm';
      showToast.error(errorMsg);
      console.error('Error acknowledging alarm:', err);
      return false;
    }
  }, [fetchActiveAlarms]);

  const clearAlarm = useCallback(async (alarmId: string) => {
    try {
      await alarmsApi.clearAlarm(alarmId);
      showToast.success('Alarm cleared successfully');
      await fetchActiveAlarms();
      return true;
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to clear alarm';
      showToast.error(errorMsg);
      console.error('Error clearing alarm:', err);
      return false;
    }
  }, [fetchActiveAlarms]);

  // Auto-refresh effect
  useEffect(() => {
    if (autoRefresh) {
      fetchActiveAlarms();
      const interval = setInterval(fetchActiveAlarms, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, fetchActiveAlarms]);

  return {
    activeAlarms,
    loading,
    error,
    fetchActiveAlarms,
    acknowledgeAlarm,
    clearAlarm,
  };
};

export const useAlarmHistory = () => {
  const [history, setHistory] = useState<AlarmEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = useCallback(async (params?: {
    start_date?: string;
    end_date?: string;
    severity?: string;
    state?: string;
    limit?: number;
  }) => {
    try {
      setLoading(true);
      setError(null);
      const data = await alarmsApi.getHistory(params);
      setHistory(data);
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to fetch alarm history';
      setError(errorMsg);
      console.error('Error fetching alarm history:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    history,
    loading,
    error,
    fetchHistory,
  };
};

export const useAlarmStatistics = () => {
  const [statistics, setStatistics] = useState<AlarmStatistics | null>(null);
  const [topAlarms, setTopAlarms] = useState<TopAlarm[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatistics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [stats, top] = await Promise.all([
        alarmsApi.getStatistics(),
        alarmsApi.getTopAlarms(10),
      ]);
      setStatistics(stats);
      setTopAlarms(top);
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to fetch statistics';
      setError(errorMsg);
      console.error('Error fetching statistics:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatistics();
  }, [fetchStatistics]);

  return {
    statistics,
    topAlarms,
    loading,
    error,
    fetchStatistics,
  };
};
