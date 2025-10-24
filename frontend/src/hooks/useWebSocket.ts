/**
 * WebSocket Hook for Real-time Data
 */
import { useEffect, useState, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { WS_BASE_URL, API_ENDPOINTS, WEBSOCKET_EVENTS } from '../api/config';
import type { TagUpdate, DeviceUpdate, WebSocketMessage } from '../types';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  reconnection?: boolean;
  reconnectionDelay?: number;
  reconnectionAttempts?: number;
}

interface UseWebSocketReturn {
  socket: Socket | null;
  connected: boolean;
  tagData: Record<string, any>;
  deviceData: Record<string, any>;
  subscribeToTag: (tagId: string) => void;
  unsubscribeFromTag: (tagId: string) => void;
  subscribeToDevice: (deviceId: string) => void;
  joinRoom: (roomId: string) => void;
  leaveRoom: (roomId: string) => void;
  sendMessage: (message: WebSocketMessage) => void;
}

export const useWebSocket = (
  options: UseWebSocketOptions = {}
): UseWebSocketReturn => {
  const {
    autoConnect = true,
    reconnection = true,
    reconnectionDelay = 1000,
    reconnectionAttempts = 5,
  } = options;

  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [tagData, setTagData] = useState<Record<string, any>>({});
  const [deviceData, setDeviceData] = useState<Record<string, any>>({});

  const socketRef = useRef<Socket | null>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    if (!autoConnect) return;

    const token = localStorage.getItem('access_token');
    const wsUrl = `${WS_BASE_URL}${API_ENDPOINTS.WS_REALTIME}?token=${token}`;

    const newSocket = io(wsUrl, {
      transports: ['websocket'],
      reconnection,
      reconnectionDelay,
      reconnectionAttempts,
    });

    socketRef.current = newSocket;
    setSocket(newSocket);

    // Connection events
    newSocket.on(WEBSOCKET_EVENTS.CONNECT, () => {
      console.log('✅ WebSocket connected');
      setConnected(true);
    });

    newSocket.on(WEBSOCKET_EVENTS.DISCONNECT, () => {
      console.log('❌ WebSocket disconnected');
      setConnected(false);
    });

    newSocket.on(WEBSOCKET_EVENTS.CONNECTION, (data: any) => {
      console.log('Connection established:', data);
    });

    // Data events
    newSocket.on(WEBSOCKET_EVENTS.TAG_UPDATE, (update: TagUpdate) => {
      console.log('Tag update:', update);
      setTagData((prev) => ({
        ...prev,
        [update.tag_id]: update.data,
      }));
    });

    newSocket.on(WEBSOCKET_EVENTS.DEVICE_UPDATE, (update: DeviceUpdate) => {
      console.log('Device update:', update);
      setDeviceData((prev) => ({
        ...prev,
        [update.device_id]: update.data,
      }));
    });

    newSocket.on(WEBSOCKET_EVENTS.ERROR, (error: any) => {
      console.error('WebSocket error:', error);
    });

    // Cleanup
    return () => {
      newSocket.close();
    };
  }, [autoConnect, reconnection, reconnectionDelay, reconnectionAttempts]);

  // Subscribe to tag updates
  const subscribeToTag = useCallback(
    (tagId: string) => {
      if (socket && connected) {
        socket.emit('message', {
          type: 'subscribe_tag',
          tag_id: tagId,
        });
        console.log(`📊 Subscribed to tag: ${tagId}`);
      }
    },
    [socket, connected]
  );

  // Unsubscribe from tag updates
  const unsubscribeFromTag = useCallback(
    (tagId: string) => {
      if (socket && connected) {
        socket.emit('message', {
          type: 'unsubscribe_tag',
          tag_id: tagId,
        });
        console.log(`🚫 Unsubscribed from tag: ${tagId}`);
      }
    },
    [socket, connected]
  );

  // Subscribe to device updates
  const subscribeToDevice = useCallback(
    (deviceId: string) => {
      if (socket && connected) {
        socket.emit('message', {
          type: 'subscribe_device',
          device_id: deviceId,
        });
        console.log(`🔌 Subscribed to device: ${deviceId}`);
      }
    },
    [socket, connected]
  );

  // Join a room
  const joinRoom = useCallback(
    (roomId: string) => {
      if (socket && connected) {
        socket.emit('message', {
          type: 'join_room',
          room_id: roomId,
        });
        console.log(`🚪 Joined room: ${roomId}`);
      }
    },
    [socket, connected]
  );

  // Leave a room
  const leaveRoom = useCallback(
    (roomId: string) => {
      if (socket && connected) {
        socket.emit('message', {
          type: 'leave_room',
          room_id: roomId,
        });
        console.log(`🚪 Left room: ${roomId}`);
      }
    },
    [socket, connected]
  );

  // Send custom message
  const sendMessage = useCallback(
    (message: WebSocketMessage) => {
      if (socket && connected) {
        socket.emit('message', message);
      }
    },
    [socket, connected]
  );

  return {
    socket,
    connected,
    tagData,
    deviceData,
    subscribeToTag,
    unsubscribeFromTag,
    subscribeToDevice,
    joinRoom,
    leaveRoom,
    sendMessage,
  };
};

// Dashboard-specific WebSocket hook
export const useDashboardWebSocket = (dashboardId: string) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [tagData, setTagData] = useState<Record<string, any>>({});

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const wsUrl = `${WS_BASE_URL}${API_ENDPOINTS.WS_DASHBOARD}/${dashboardId}?token=${token}`;

    const newSocket = io(wsUrl, {
      transports: ['websocket'],
      reconnection: true,
    });

    setSocket(newSocket);

    newSocket.on('connect', () => {
      console.log(`✅ Dashboard WebSocket connected: ${dashboardId}`);
      setConnected(true);
    });

    newSocket.on('disconnect', () => {
      console.log(`❌ Dashboard WebSocket disconnected: ${dashboardId}`);
      setConnected(false);
    });

    newSocket.on('tag_update', (update: TagUpdate) => {
      setTagData((prev) => ({
        ...prev,
        [update.tag_id]: update.data,
      }));
    });

    return () => {
      newSocket.close();
    };
  }, [dashboardId]);

  const subscribeToTags = useCallback(
    (tagIds: string[]) => {
      if (socket && connected) {
        socket.emit('message', {
          type: 'subscribe_tags',
          tag_ids: tagIds,
        });
      }
    },
    [socket, connected]
  );

  return { socket, connected, tagData, subscribeToTags };
};
