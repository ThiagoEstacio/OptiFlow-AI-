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

export const useLiveTagData = (tagId?: string): LiveTagData => {
  const [data, setData] = useState<LiveTagData>({
    value: null,
    timestamp: null,
    quality: 'unknown',
    loading: false,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

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
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);

            if (message.type === 'data' && message.data) {
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
          // Fallback to polling
          startPolling();
        };

        ws.onclose = () => {
          console.log('WebSocket closed, falling back to polling');
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
          // If no endpoint, generate random value for demo
          // This simulates data from the simulator
          setData(prev => ({
            ...prev,
            value: Math.random() * 100,
            timestamp: new Date().toISOString(),
            quality: 'simulated',
            loading: false,
          }));
        }
      } catch (error) {
        console.error('Error fetching latest value:', error);
        // Generate demo data
        setData(prev => ({
          ...prev,
          value: Math.random() * 100,
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
    };
  }, [tagId]);

  return data;
};
