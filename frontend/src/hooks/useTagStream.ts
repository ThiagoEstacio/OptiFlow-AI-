/**
 * React Hook for real-time tag values via WebSocket
 * Connects directly to OPC UA via WebSocket (bypasses database)
 */
import { useEffect, useState, useCallback, useRef } from 'react';

interface TagValue {
  value: string;
  quality: string;
  timestamp: string;
}

interface StreamMessage {
  timestamp: string;
  values: {
    [nodeId: string]: TagValue;
  };
}

interface UseTagStreamOptions {
  autoConnect?: boolean;
  reconnectInterval?: number;
}

export function useTagStream(options: UseTagStreamOptions = {}) {
  const {
    autoConnect = true,
    reconnectInterval = 5000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<StreamMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tagValues, setTagValues] = useState<Map<string, TagValue>>(new Map());

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      // Connect to WebSocket endpoint
      const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/ws/tags/stream';
      console.log('🔌 Connecting to WebSocket:', wsUrl);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        setError(null);

        // Send ping to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000); // 30 seconds

        ws.addEventListener('close', () => {
          clearInterval(pingInterval);
        });
      };

      ws.onmessage = (event) => {
        try {
          const message: StreamMessage = JSON.parse(event.data);
          setLastMessage(message);

          // Update tag values map
          setTagValues((prev) => {
            const newMap = new Map(prev);
            Object.entries(message.values).forEach(([nodeId, value]) => {
              newMap.set(nodeId, value);
            });
            return newMap;
          });
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('❌ WebSocket error:', event);
        setError('WebSocket connection error');
      };

      ws.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;

        // Attempt reconnection if enabled
        if (shouldReconnectRef.current && autoConnect) {
          console.log(`🔄 Reconnecting in ${reconnectInterval}ms...`);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };
    } catch (err) {
      console.error('Error creating WebSocket:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  }, [autoConnect, reconnectInterval]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  const getTagValue = useCallback((nodeId: string): TagValue | null => {
    return tagValues.get(nodeId) || null;
  }, [tagValues]);

  const subscribeToTags = useCallback((nodeIds: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        nodeIds,
      }));
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      shouldReconnectRef.current = true;
      connect();
    }

    // Cleanup on unmount
    return () => {
      shouldReconnectRef.current = false;
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    error,
    tagValues,
    getTagValue,
    connect,
    disconnect,
    subscribeToTags,
  };
}

/**
 * Example usage:
 * 
 * const { isConnected, getTagValue, tagValues } = useTagStream();
 * 
 * const gate01Position = getTagValue('ns=2;i=8');
 * console.log(gate01Position?.value); // "90.0"
 * 
 * // Or iterate all values
 * tagValues.forEach((value, nodeId) => {
 *   console.log(`${nodeId}: ${value.value} (${value.quality})`);
 * });
 */
