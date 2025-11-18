/**
 * useBackendHealth Hook
 * Monitors backend health and provides connection status
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { apiClient } from '../api/client';

interface BackendHealthState {
  isHealthy: boolean;
  lastCheck: Date | null;
  consecutiveFailures: number;
  latency: number | null;
  status: 'online' | 'offline' | 'degraded' | 'checking';
}

interface UseBackendHealthOptions {
  checkInterval?: number; // ms between health checks
  failureThreshold?: number; // failures before marking offline
  enabled?: boolean;
}

export const useBackendHealth = (options: UseBackendHealthOptions = {}) => {
  const {
    checkInterval = 30000, // 30 seconds
    failureThreshold = 3,
    enabled = true,
  } = options;

  const [health, setHealth] = useState<BackendHealthState>({
    isHealthy: true, // Optimistic start
    lastCheck: null,
    consecutiveFailures: 0,
    latency: null,
    status: 'checking',
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);

  const checkHealth = useCallback(async () => {
    if (!enabled || !isMountedRef.current) return;

    const startTime = Date.now();

    try {
      await apiClient.get('/api/health');
      const latency = Date.now() - startTime;

      if (isMountedRef.current) {
        setHealth(prev => ({
          isHealthy: true,
          lastCheck: new Date(),
          consecutiveFailures: 0,
          latency,
          status: latency > 5000 ? 'degraded' : 'online',
        }));
      }
    } catch (error) {
      if (isMountedRef.current) {
        setHealth(prev => {
          const newFailures = prev.consecutiveFailures + 1;
          const isOffline = newFailures >= failureThreshold;

          return {
            isHealthy: !isOffline,
            lastCheck: new Date(),
            consecutiveFailures: newFailures,
            latency: null,
            status: isOffline ? 'offline' : 'degraded',
          };
        });
      }
    }
  }, [enabled, failureThreshold]);

  // Initial check and periodic monitoring
  useEffect(() => {
    isMountedRef.current = true;

    if (enabled) {
      // Initial check
      checkHealth();

      // Set up periodic checks
      intervalRef.current = setInterval(checkHealth, checkInterval);
    }

    return () => {
      isMountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [enabled, checkInterval, checkHealth]);

  // Manual health check
  const forceCheck = useCallback(() => {
    setHealth(prev => ({ ...prev, status: 'checking' }));
    checkHealth();
  }, [checkHealth]);

  return {
    ...health,
    forceCheck,
  };
};

export default useBackendHealth;
