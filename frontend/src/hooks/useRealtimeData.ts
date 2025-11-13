/**
 * React Hook for Real-time Data via WebSocket
 * Manages WebSocket connection and provides real-time updates
 */
import { useEffect, useState, useCallback, useRef } from 'react';
import { websocketService } from '../services/websocket';

interface UseRealtimeDataOptions {
  autoConnect?: boolean;
  url?: string;
}

interface RealtimeData<T = any> {
  data: T | null;
  isConnected: boolean;
  error: Error | null;
  lastUpdate: Date | null;
}

// Type for simulator update messages
export interface SimulatorUpdate {
  type: 'simulator_update';
  timestamp: string;
  tags: Record<string, number>;
  status: {
    system: {
      running: boolean;
      time_s: number;
      total_mass_t: number;
      total_kWh: number;
      warehouse_level_pct: number;
      kWh_per_ton: number;
      cost_BRL: number;
    };
    gates: Array<{
      name: string;
      setpoint_pct: number;
      opening_pct: number;
      flow_tph: number;
      failure: boolean;
    }>;
    belts: Array<{
      name: string;
      running: boolean;
      speed_mps: number;
      flow_tph: number;
      load_pct: number;
      power_kw: number;
      current_a: number;
      temp_c: number;
      misalignment: number;
    }>;
    shiploader: {
      name: string;
      setpoint_tph: number;
      flow_tph: number;
      power_kw: number;
      current_a: number;
    };
  };
}

/**
 * Hook for subscribing to real-time data updates
 */
export function useRealtimeData<T = any>(
  messageType: string,
  options: UseRealtimeDataOptions = {}
): RealtimeData<T> & {
  send: (data: any) => void;
  connect: () => void;
  disconnect: () => void;
} {
  const { autoConnect = true, url = 'ws://localhost:8000/ws' } = options;

  const [data, setData] = useState<T | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const isConnectedRef = useRef(false);

  // Handle incoming messages
  const handleMessage = useCallback((messageData: T) => {
    setData(messageData);
    setLastUpdate(new Date());
    setError(null);
  }, []);

  // Handle connection status
  const handleConnect = useCallback(() => {
    setIsConnected(true);
    isConnectedRef.current = true;
    setError(null);
  }, []);

  const handleDisconnect = useCallback(() => {
    setIsConnected(false);
    isConnectedRef.current = false;
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!isConnectedRef.current) {
      websocketService.connect(url);
    }
  }, [url]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    websocketService.disconnect();
  }, []);

  // Send message
  const send = useCallback((data: any) => {
    websocketService.send(messageType, data);
  }, [messageType]);

  // Setup subscriptions
  useEffect(() => {
    // Subscribe to messages
    const unsubscribeMessage = websocketService.on(messageType, handleMessage);
    const unsubscribeConnect = websocketService.onConnect(handleConnect);
    const unsubscribeDisconnect = websocketService.onDisconnect(handleDisconnect);

    // Auto-connect if enabled
    if (autoConnect && !isConnectedRef.current) {
      websocketService.connect(url);
    }

    // Cleanup
    return () => {
      unsubscribeMessage();
      unsubscribeConnect();
      unsubscribeDisconnect();
    };
  }, [messageType, autoConnect, url, handleMessage, handleConnect, handleDisconnect]);

  return {
    data,
    isConnected,
    error,
    lastUpdate,
    send,
    connect,
    disconnect
  };
}

/**
 * Hook for managing WebSocket connection status
 */
export function useWebSocketStatus() {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const unsubscribeConnect = websocketService.onConnect(() => setIsConnected(true));
    const unsubscribeDisconnect = websocketService.onDisconnect(() => setIsConnected(false));

    // Check initial status
    setIsConnected(websocketService.isConnected);

    return () => {
      unsubscribeConnect();
      unsubscribeDisconnect();
    };
  }, []);

  return isConnected;
}
