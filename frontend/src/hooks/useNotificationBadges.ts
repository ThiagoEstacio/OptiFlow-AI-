/**
 * Custom hook for notification badges
 * Fetches real-time counts for alarms, work orders, etc.
 */

import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

export interface NotificationBadges {
  activeAlarms: number;
  criticalAlarms: number;
  openWorkOrders: number;
  pendingApprovals: number;
}

export const useNotificationBadges = (refreshInterval: number = 30000) => {
  const [badges, setBadges] = useState<NotificationBadges>({
    activeAlarms: 0,
    criticalAlarms: 0,
    openWorkOrders: 0,
    pendingApprovals: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBadges = async () => {
    try {
      // TODO: Replace with actual API endpoints when available
      // For now, using mock data

      // In production, these would be real API calls:
      // const alarmsRes = await apiClient.get('/api/v1/operations/alarms/count');
      // const workOrdersRes = await apiClient.get('/api/v1/maintenance/work-orders/count');

      // Mock data for now
      setBadges({
        activeAlarms: Math.floor(Math.random() * 20), // 0-19 active alarms
        criticalAlarms: Math.floor(Math.random() * 5), // 0-4 critical
        openWorkOrders: Math.floor(Math.random() * 15), // 0-14 open WOs
        pendingApprovals: Math.floor(Math.random() * 8), // 0-7 pending
      });

      setError(null);
    } catch (err) {
      console.error('Error fetching notification badges:', err);
      setError('Failed to fetch notifications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBadges();

    const interval = setInterval(() => {
      fetchBadges();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  return { badges, loading, error, refetch: fetchBadges };
};
