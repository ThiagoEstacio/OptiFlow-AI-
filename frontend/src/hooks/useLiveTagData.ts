/**
 * useLiveTagData Hook
 * Connects to WebSocket for real-time tag data
 * Falls back to polling if WebSocket unavailable
 */

import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../api/client';

interface LiveTagData {
  value: number | string | boolean | null;
  timestamp: string | null;
  quality: string;
  loading: boolean;
  error: string | null;
}

interface UseLiveTagDataOptions {
  tagId?: string;
  min?: number;
  max?: number;
}

export const useLiveTagData = (
  tagIdOrOptions?: string | UseLiveTagDataOptions,
  legacyMin?: number,
  legacyMax?: number
): LiveTagData => {
  // Support both old API (string) and new API (options object)
  let tagId: string | undefined;
  let min: number = 0;
  let max: number = 100;

  if (typeof tagIdOrOptions === 'string') {
    tagId = tagIdOrOptions;
    min = legacyMin ?? 0;
    max = legacyMax ?? 100;
  } else if (tagIdOrOptions) {
    tagId = tagIdOrOptions.tagId;
    min = tagIdOrOptions.min ?? 0;
    max = tagIdOrOptions.max ?? 100;
  }

  const [data, setData] = useState<LiveTagData>({
    value: null,
    timestamp: null,
    quality: 'unknown',
    loading: false,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const wsTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const receivedDataRef = useRef<boolean>(false);

  useEffect(() => {
    if (!tagId) {
      setData({
        value: null,
        timestamp: null,
        quality: 'unknown',
        loading: false,
        error: null,
      });
      return;
    }

    setData(prev => ({ ...prev, loading: true, error: null }));
    receivedDataRef.current = false;

    // Try WebSocket first
    const connectWebSocket = () => {
      try {
        const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
        const ws = new WebSocket(`${wsUrl}/api/v1/analytics/ws/stream?token=dummy`);

        ws.onopen = () => {
          console.log(`WebSocket connected for tag ${tagId}`);

          // Subscribe to tag
          ws.send(JSON.stringify({
            query: {
              tag_ids: [tagId],
              range: '1m',
            },
            refresh_interval: 1, // 1 second
            mode: 'continuous',
          }));

          setData(prev => ({ ...prev, loading: false }));

          // Set timeout: if no data received in 3 seconds, fall back to simulation
          wsTimeoutRef.current = setTimeout(() => {
            if (!receivedDataRef.current) {
              console.log(`No data received from WebSocket for tag ${tagId}, falling back to simulation`);
              ws.close();
              startPolling();
            }
          }, 3000);
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);

            if (message.type === 'data' && message.data) {
              receivedDataRef.current = true;

              // Clear timeout since we received data
              if (wsTimeoutRef.current) {
                clearTimeout(wsTimeoutRef.current);
                wsTimeoutRef.current = null;
              }

              // Extract value from response
              const result = message.data;
              if (result.data && result.data.length > 0) {
                const latest = result.data[result.data.length - 1];
                setData({
                  value: latest.value,
                  timestamp: latest.timestamp,
                  quality: latest.quality || 'good',
                  loading: false,
                  error: null,
                });
              }
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setData(prev => ({ ...prev, error: 'WebSocket connection error' }));

          // Clear timeout
          if (wsTimeoutRef.current) {
            clearTimeout(wsTimeoutRef.current);
            wsTimeoutRef.current = null;
          }

          // Fallback to polling
          startPolling();
        };

        ws.onclose = () => {
          console.log('WebSocket closed, falling back to polling');

          // Clear timeout
          if (wsTimeoutRef.current) {
            clearTimeout(wsTimeoutRef.current);
            wsTimeoutRef.current = null;
          }

          startPolling();
        };

        wsRef.current = ws;

      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        startPolling();
      }
    };

    // Polling fallback
    const startPolling = () => {
      if (pollingIntervalRef.current) return;

      // Initial fetch
      fetchLatestValue();

      // Poll every 2 seconds
      pollingIntervalRef.current = setInterval(() => {
        fetchLatestValue();
      }, 2000);
    };

    const generateSimulatedValue = () => {
      // Generate realistic simulated value with some variation
      const range = max - min;
      const baseValue = min + (range * 0.5); // Middle of range
      const variation = range * 0.3; // 30% variation
      const randomValue = baseValue + (Math.random() - 0.5) * variation;

      // Add some wave pattern for more realistic data
      const time = Date.now() / 1000;
      const wave = Math.sin(time / 10) * (range * 0.2);

      return Math.max(min, Math.min(max, randomValue + wave));
    };

    const fetchLatestValue = async () => {
      try {
        // Try to get latest value from Redis cache or last value endpoint
        const response = await fetch(`/api/v1/tags/${tagId}/latest`);
        if (response.ok) {
          const result = await response.json();
          setData({
            value: result.value,
            timestamp: result.timestamp,
            quality: result.quality || 'good',
            loading: false,
            error: null,
          });
        } else {
          // If no endpoint, generate realistic simulated value
          setData(prev => ({
            ...prev,
            value: generateSimulatedValue(),
            timestamp: new Date().toISOString(),
            quality: 'simulated',
            loading: false,
          }));
        }
      } catch (error) {
        console.error('Error fetching latest value:', error);
        // Generate demo data with realistic values
        setData(prev => ({
          ...prev,
          value: generateSimulatedValue(),
          timestamp: new Date().toISOString(),
          quality: 'simulated',
          loading: false,
        }));
      }
    };

    // Start connection
    connectWebSocket();

    // Cleanup
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      if (wsTimeoutRef.current) {
        clearTimeout(wsTimeoutRef.current);
        wsTimeoutRef.current = null;
      }
    };
  }, [tagId]);

  return data;
};
