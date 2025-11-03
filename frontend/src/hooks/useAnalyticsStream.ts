/**
 * useAnalyticsStream Hook
 *
 * React hook for real-time analytics data streaming via WebSocket
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { AnalyticsQuery, QueryResult } from '../services/analyticsApi';

export interface StreamConfig {
  query: AnalyticsQuery;
  refresh_interval: number; // seconds
  mode?: 'continuous' | 'windowed';
}

export interface StreamStatus {
  connected: boolean;
  streaming: boolean;
  paused: boolean;
  error: string | null;
  sequence: number;
  lastUpdate: string | null;
}

export interface UseAnalyticsStreamResult {
  // Data
  data: QueryResult | null;
  status: StreamStatus;

  // Controls
  start: (config: StreamConfig) => void;
  pause: () => void;
  resume: () => void;
  stop: () => void;
  updateQuery: (query: AnalyticsQuery) => void;

  // Connection
  connect: () => void;
  disconnect: () => void;
}

/**
 * Custom hook for managing analytics WebSocket streaming
 */
export const useAnalyticsStream = (): UseAnalyticsStreamResult => {
  const [data, setData] = useState<QueryResult | null>(null);
  const [status, setStatus] = useState<StreamStatus>({
    connected: false,
    streaming: false,
    paused: false,
    error: null,
    sequence: 0,
    lastUpdate: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const configRef = useRef<StreamConfig | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Get WebSocket URL
   */
  const getWebSocketUrl = useCallback((): string => {
    const token = localStorage.getItem('token');
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost =
      import.meta.env.VITE_WS_URL ||
      window.location.host.replace('3000', '8000'); // Dev: frontend 3000 -> backend 8000

    return `${wsProtocol}//${wsHost}/api/v1/analytics/ws/stream?token=${token}`;
  }, []);

  /**
   * Send message to WebSocket
   */
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.error('WebSocket not connected');
    }
  }, []);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    try {
      const url = getWebSocketUrl();
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setStatus((prev) => ({ ...prev, connected: true, error: null }));
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'data') {
            // Update data
            setData(message.data);
            setStatus((prev) => ({
              ...prev,
              sequence: message.sequence || prev.sequence + 1,
              lastUpdate: message.timestamp,
              error: null,
            }));
          } else if (message.type === 'error') {
            // Handle error
            setStatus((prev) => ({
              ...prev,
              error: message.message,
              streaming: false,
            }));
          } else if (message.type === 'status') {
            // Handle status update
            console.log('WebSocket status:', message.message);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStatus((prev) => ({
          ...prev,
          error: 'WebSocket connection error',
        }));
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setStatus((prev) => ({
          ...prev,
          connected: false,
          streaming: false,
        }));

        // Attempt reconnection after 3 seconds if we were streaming
        if (configRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, 3000);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      setStatus((prev) => ({
        ...prev,
        error: 'Failed to create WebSocket connection',
      }));
    }
  }, [getWebSocketUrl]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    // Clear reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Reset state
    configRef.current = null;
    setStatus({
      connected: false,
      streaming: false,
      paused: false,
      error: null,
      sequence: 0,
      lastUpdate: null,
    });
    setData(null);
  }, []);

  /**
   * Start streaming
   */
  const start = useCallback(
    (config: StreamConfig) => {
      configRef.current = config;

      // Connect if not connected
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        connect();
        // Wait for connection then start streaming
        setTimeout(() => {
          sendMessage({
            action: 'start',
            query: config.query,
            refresh_interval: config.refresh_interval,
            mode: config.mode || 'continuous',
          });
        }, 1000);
      } else {
        sendMessage({
          action: 'start',
          query: config.query,
          refresh_interval: config.refresh_interval,
          mode: config.mode || 'continuous',
        });
      }

      setStatus((prev) => ({ ...prev, streaming: true, paused: false }));
    },
    [connect, sendMessage]
  );

  /**
   * Pause streaming
   */
  const pause = useCallback(() => {
    sendMessage({ action: 'pause' });
    setStatus((prev) => ({ ...prev, paused: true }));
  }, [sendMessage]);

  /**
   * Resume streaming
   */
  const resume = useCallback(() => {
    sendMessage({ action: 'resume' });
    setStatus((prev) => ({ ...prev, paused: false }));
  }, [sendMessage]);

  /**
   * Stop streaming
   */
  const stop = useCallback(() => {
    sendMessage({ action: 'stop' });
    setStatus((prev) => ({ ...prev, streaming: false, paused: false }));
    configRef.current = null;
  }, [sendMessage]);

  /**
   * Update query while streaming
   */
  const updateQuery = useCallback(
    (query: AnalyticsQuery) => {
      if (configRef.current) {
        const newConfig = { ...configRef.current, query };
        configRef.current = newConfig;
        sendMessage({
          action: 'update_query',
          query: query,
          refresh_interval: newConfig.refresh_interval,
          mode: newConfig.mode || 'continuous',
        });
      }
    },
    [sendMessage]
  );

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    data,
    status,
    start,
    pause,
    resume,
    stop,
    updateQuery,
    connect,
    disconnect,
  };
};

export default useAnalyticsStream;
