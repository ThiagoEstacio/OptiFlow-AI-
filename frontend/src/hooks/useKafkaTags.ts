import { useEffect, useState, useRef, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE = API_BASE.replace('http://', 'ws://').replace('https://', 'wss://');

export interface TagUpdate {
  tag_id: string;
  name: string;
  value: number;
  quality: string;
  timestamp: string;
  source: string;
}

export interface SimulatorStateUpdate {
  timestamp: string;
  data: any;
}

export function useKafkaTags() {
  const [tags, setTags] = useState<Map<string, TagUpdate>>(new Map());
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [messageCount, setMessageCount] = useState(0);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    try {
      const wsUrl = `${WS_BASE}/api/v1/ws/tags`;
      console.log('🔌 Connecting to Kafka stream:', wsUrl);

      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log('✅ Connected to Kafka tag stream');
        setConnected(true);
        reconnectAttempts.current = 0;
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'connected') {
            console.log('✅ Kafka stream connection confirmed:', message.client_id);
            return;
          }

          if (message.type === 'tag_update') {
            const tagData: TagUpdate = message.data;

            // Update tags map (O(1) lookup by tag_id)
            setTags(prev => {
              const newMap = new Map(prev);
              newMap.set(tagData.tag_id, tagData);
              return newMap;
            });

            setLastUpdate(new Date());
            setMessageCount(prev => prev + 1);
          }

          if (message.type === 'simulator_state') {
            // Full simulator state update
            console.log('📊 Simulator state update received');
            setLastUpdate(new Date());
          }
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error);
        }
      };

      ws.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setConnected(false);
      };

      ws.current.onclose = (event) => {
        console.log('🔌 Disconnected from Kafka stream:', event.code, event.reason);
        setConnected(false);

        // Exponential backoff reconnection
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current += 1;

        console.log(`🔄 Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})...`);

        reconnectTimeout.current = setTimeout(() => {
          connect();
        }, delay);
      };
    } catch (error) {
      console.error('❌ Failed to create WebSocket connection:', error);
      setConnected(false);
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  const getTag = useCallback((tagId: string): TagUpdate | undefined => {
    return tags.get(tagId);
  }, [tags]);

  const getAllTags = useCallback((): TagUpdate[] => {
    return Array.from(tags.values());
  }, [tags]);

  const getTagsBySource = useCallback((source: string): TagUpdate[] => {
    return Array.from(tags.values()).filter(tag => tag.source === source);
  }, [tags]);

  return {
    tags,
    connected,
    lastUpdate,
    messageCount,
    getTag,
    getAllTags,
    getTagsBySource,
  };
}
