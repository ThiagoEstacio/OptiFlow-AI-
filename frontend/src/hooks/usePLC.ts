/**
 * usePLC Hook
 *
 * Custom hook for PLC tag monitoring with WebSocket real-time updates
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { WS_BASE_URL } from '../api/config';
import { plcApi, PLCTag, PLCTagValue, HistoricalDataPoint, PLCStatistics } from '../api/plc';

interface UsePLCOptions {
  autoConnect?: boolean;
  enableWebSocket?: boolean;
  updateInterval?: number;
}

interface UsePLCReturn {
  // Data
  tags: PLCTag[];
  tagValues: Record<string, PLCTagValue>;

  // WebSocket
  connected: boolean;

  // Loading states
  loading: boolean;
  tagsLoading: boolean;

  // Methods
  refreshTags: () => Promise<void>;
  readTag: (tagName: string) => Promise<PLCTagValue | null>;
  subscribeToTag: (tagName: string) => void;
  unsubscribeFromTag: (tagName: string) => void;
  subscribeToAll: () => void;
  unsubscribeFromAll: () => void;
  getHistory: (tagName: string, hours?: number) => Promise<HistoricalDataPoint[]>;
  getStatistics: (tagName: string, hours?: number) => Promise<PLCStatistics | null>;
}

export const usePLC = (options: UsePLCOptions = {}): UsePLCReturn => {
  const { autoConnect = true, enableWebSocket = true } = options;

  // Data state
  const [tags, setTags] = useState<PLCTag[]>([]);
  const [tagValues, setTagValues] = useState<Record<string, PLCTagValue>>({});

  // Loading states
  const [loading, setLoading] = useState(true);
  const [tagsLoading, setTagsLoading] = useState(false);

  // WebSocket state
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const subscribedTagsRef = useRef<Set<string>>(new Set());

  // Refresh tags list
  const refreshTags = useCallback(async () => {
    setTagsLoading(true);
    try {
      const data = await plcApi.listTags();
      setTags(data);
    } catch (error) {
      console.error('Error fetching tags:', error);
    } finally {
      setTagsLoading(false);
    }
  }, []);

  // Read single tag value
  const readTag = useCallback(async (tagName: string): Promise<PLCTagValue | null> => {
    try {
      const value = await plcApi.readTag(tagName);
      setTagValues((prev) => ({
        ...prev,
        [tagName]: value,
      }));
      return value;
    } catch (error) {
      console.error(`Error reading tag ${tagName}:`, error);
      return null;
    }
  }, []);

  // Get historical data
  const getHistory = useCallback(
    async (tagName: string, hours: number = 24): Promise<HistoricalDataPoint[]> => {
      try {
        const response = await plcApi.getHistory(tagName, { hours });
        return response.data;
      } catch (error) {
        console.error(`Error fetching history for ${tagName}:`, error);
        return [];
      }
    },
    []
  );

  // Get statistics
  const getStatistics = useCallback(
    async (tagName: string, hours: number = 24): Promise<PLCStatistics | null> => {
      try {
        const response = await plcApi.getStatistics(tagName, hours);
        return response.statistics;
      } catch (error) {
        console.error(`Error fetching statistics for ${tagName}:`, error);
        return null;
      }
    },
    []
  );

  // WebSocket connection
  const connectWebSocket = useCallback(() => {
    if (!enableWebSocket) return;

    const token = localStorage.getItem('access_token');
    const wsUrl = `${WS_BASE_URL}/ws/plc${token ? `?token=${token}` : ''}`;

    console.log('Connecting to PLC WebSocket:', wsUrl);

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ PLC WebSocket connected');
        setConnected(true);

        // Resubscribe to previously subscribed tags
        subscribedTagsRef.current.forEach((tagName) => {
          ws.send(JSON.stringify({ type: 'subscribe_tag', tag_name: tagName }));
        });
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'plc_update') {
            // Update tag values from WebSocket
            const updates = message.data;
            setTagValues((prev) => {
              const newValues = { ...prev };
              Object.entries(updates).forEach(([tagName, data]: [string, any]) => {
                newValues[tagName] = data;
              });
              return newValues;
            });
          } else if (message.type === 'tag_value') {
            // Single tag update
            const { tag_name, value, timestamp, quality, unit, description } = message;
            setTagValues((prev) => ({
              ...prev,
              [tag_name]: {
                name: tag_name,
                value,
                timestamp,
                quality,
                unit,
                description,
              },
            }));
          } else if (message.type === 'error') {
            console.error('PLC WebSocket error:', message.message);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ PLC WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('❌ PLC WebSocket disconnected');
        setConnected(false);
        wsRef.current = null;

        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('🔄 Attempting to reconnect PLC WebSocket...');
          connectWebSocket();
        }, 3000);
      };
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
    }
  }, [enableWebSocket]);

  // Subscribe to specific tag
  const subscribeToTag = useCallback((tagName: string) => {
    subscribedTagsRef.current.add(tagName);

    if (wsRef.current && connected) {
      wsRef.current.send(JSON.stringify({ type: 'subscribe_tag', tag_name: tagName }));
      console.log(`📊 Subscribed to PLC tag: ${tagName}`);
    }
  }, [connected]);

  // Unsubscribe from tag
  const unsubscribeFromTag = useCallback((tagName: string) => {
    subscribedTagsRef.current.delete(tagName);

    if (wsRef.current && connected) {
      wsRef.current.send(JSON.stringify({ type: 'unsubscribe_tag', tag_name: tagName }));
      console.log(`🚫 Unsubscribed from PLC tag: ${tagName}`);
    }
  }, [connected]);

  // Subscribe to all tags
  const subscribeToAll = useCallback(() => {
    if (wsRef.current && connected) {
      wsRef.current.send(JSON.stringify({ type: 'subscribe_all' }));
      console.log('📊 Subscribed to all PLC tags');
    }
  }, [connected]);

  // Unsubscribe from all tags
  const unsubscribeFromAll = useCallback(() => {
    subscribedTagsRef.current.clear();

    if (wsRef.current && connected) {
      wsRef.current.send(JSON.stringify({ type: 'unsubscribe_all' }));
      console.log('🚫 Unsubscribed from all PLC tags');
    }
  }, [connected]);

  // Initial data load
  useEffect(() => {
    const loadInitialData = async () => {
      setLoading(true);
      await refreshTags();
      setLoading(false);
    };

    if (autoConnect) {
      loadInitialData();
    }
  }, [autoConnect, refreshTags]);

  // WebSocket connection
  useEffect(() => {
    if (autoConnect && enableWebSocket) {
      connectWebSocket();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [autoConnect, enableWebSocket, connectWebSocket]);

  return {
    tags,
    tagValues,
    connected,
    loading,
    tagsLoading,
    refreshTags,
    readTag,
    subscribeToTag,
    unsubscribeFromTag,
    subscribeToAll,
    unsubscribeFromAll,
    getHistory,
    getStatistics,
  };
};
