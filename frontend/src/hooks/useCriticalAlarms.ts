/**
 * PDCA #5: Critical Alarm Hook
 *
 * Monitors critical/high alarms and triggers notifications
 * Integrates with WebSocket for real-time updates
 * Target MTTR <30 seconds
 */
import { useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';

interface CriticalAlarm {
  id: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  message: string;
  tag_name?: string;
  value: number;
  limit: number;
  occurred_at: string;
  state: 'ACTIVE' | 'ACKNOWLEDGED' | 'CLEARED';
}

interface UseCriticalAlarmsReturn {
  currentAlarm: CriticalAlarm | null;
  alarmQueue: CriticalAlarm[];
  acknowledgeAlarm: (alarmId: string) => Promise<void>;
  dismissAlarm: () => void;
  acknowledgedAlarms: Set<string>;
}

export const useCriticalAlarms = (): UseCriticalAlarmsReturn => {
  const [alarmQueue, setAlarmQueue] = useState<CriticalAlarm[]>([]);
  const [currentAlarm, setCurrentAlarm] = useState<CriticalAlarm | null>(null);
  const [acknowledgedAlarms, setAcknowledgedAlarms] = useState<Set<string>>(new Set());

  // Fetch active critical alarms from backend
  const fetchCriticalAlarms = useCallback(async () => {
    try {
      const response = await apiClient.get('/api/v1/alarms/events?state=ACTIVE');
      const alarms = response.data || [];

      // Filter for CRITICAL and HIGH severity only
      const criticalAlarms = alarms.filter(
        (alarm: CriticalAlarm) =>
          (alarm.severity === 'CRITICAL' || alarm.severity === 'HIGH') &&
          alarm.state === 'ACTIVE' &&
          !acknowledgedAlarms.has(alarm.id)
      );

      // Sort by severity (CRITICAL first) and time
      criticalAlarms.sort((a: CriticalAlarm, b: CriticalAlarm) => {
        if (a.severity === 'CRITICAL' && b.severity !== 'CRITICAL') return -1;
        if (a.severity !== 'CRITICAL' && b.severity === 'CRITICAL') return 1;
        return new Date(a.occurred_at).getTime() - new Date(b.occurred_at).getTime();
      });

      setAlarmQueue(criticalAlarms);

      // Show first alarm if available and no current alarm
      if (criticalAlarms.length > 0 && !currentAlarm) {
        setCurrentAlarm(criticalAlarms[0]);
      }
    } catch (error) {
      console.error('Failed to fetch critical alarms:', error);
    }
  }, [acknowledgedAlarms, currentAlarm]);

  // Acknowledge alarm via backend
  const acknowledgeAlarm = useCallback(async (alarmId: string) => {
    try {
      await apiClient.post(`/api/v1/alarms/events/${alarmId}/acknowledge`, {
        comment: 'Acknowledged via critical alarm notification'
      });

      // Mark as acknowledged locally
      setAcknowledgedAlarms(prev => new Set([...prev, alarmId]));

      // Remove from queue
      setAlarmQueue(prev => prev.filter(alarm => alarm.id !== alarmId));

      // Clear current alarm if it matches
      if (currentAlarm?.id === alarmId) {
        setCurrentAlarm(null);
        // Show next alarm in queue after a short delay
        setTimeout(() => {
          setAlarmQueue(prev => {
            if (prev.length > 0) {
              setCurrentAlarm(prev[0]);
            }
            return prev;
          });
        }, 500);
      }
    } catch (error) {
      console.error('Failed to acknowledge alarm:', error);
    }
  }, [currentAlarm]);

  // Dismiss alarm without acknowledging (temporarily hide)
  const dismissAlarm = useCallback(() => {
    if (currentAlarm) {
      setAcknowledgedAlarms(prev => new Set([...prev, currentAlarm.id]));
      setAlarmQueue(prev => prev.filter(alarm => alarm.id !== currentAlarm.id));
      setCurrentAlarm(null);

      // Show next alarm in queue
      setTimeout(() => {
        setAlarmQueue(prev => {
          if (prev.length > 0) {
            setCurrentAlarm(prev[0]);
          }
          return prev;
        });
      }, 300);
    }
  }, [currentAlarm]);

  // Poll for new alarms every 5 seconds
  useEffect(() => {
    fetchCriticalAlarms();
    const interval = setInterval(fetchCriticalAlarms, 5000);
    return () => clearInterval(interval);
  }, [fetchCriticalAlarms]);

  // WebSocket integration (if available)
  useEffect(() => {
    const handleWebSocketMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);

        // Handle alarm events
        if (data.type === 'alarm_event' && data.alarm) {
          const alarm = data.alarm as CriticalAlarm;

          // Only process CRITICAL/HIGH active alarms
          if (
            (alarm.severity === 'CRITICAL' || alarm.severity === 'HIGH') &&
            alarm.state === 'ACTIVE' &&
            !acknowledgedAlarms.has(alarm.id)
          ) {
            setAlarmQueue(prev => {
              // Check if alarm already exists
              if (prev.some(a => a.id === alarm.id)) {
                return prev;
              }

              // Add to queue and sort
              const newQueue = [...prev, alarm];
              newQueue.sort((a, b) => {
                if (a.severity === 'CRITICAL' && b.severity !== 'CRITICAL') return -1;
                if (a.severity !== 'CRITICAL' && b.severity === 'CRITICAL') return 1;
                return new Date(a.occurred_at).getTime() - new Date(b.occurred_at).getTime();
              });

              // Show immediately if no current alarm
              if (!currentAlarm) {
                setCurrentAlarm(newQueue[0]);
              }

              return newQueue;
            });
          }
        }
      } catch (error) {
        console.error('Failed to process WebSocket message:', error);
      }
    };

    // Add WebSocket listener if available
    if (typeof window !== 'undefined' && 'WebSocket' in window) {
      window.addEventListener('message', handleWebSocketMessage);
      return () => window.removeEventListener('message', handleWebSocketMessage);
    }
  }, [acknowledgedAlarms, currentAlarm]);

  return {
    currentAlarm,
    alarmQueue,
    acknowledgeAlarm,
    dismissAlarm,
    acknowledgedAlarms
  };
};
