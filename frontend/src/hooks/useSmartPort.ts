/**
 * useSmartPort Hook
 *
 * Custom hook for managing SmartPort data with WebSocket real-time updates
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { WS_BASE_URL } from '../api/config';
import {
  Berth,
  Vessel,
  PortOperation,
  PortKPIs,
  berthsApi,
  vesselsApi,
  operationsApi,
  dashboardApi,
} from '../api/smartport';

interface UseSmartPortOptions {
  autoConnect?: boolean;
  enableWebSocket?: boolean;
}

interface UseSmartPortReturn {
  // Data
  berths: Berth[];
  vessels: Vessel[];
  operations: PortOperation[];
  kpis: PortKPIs | null;

  // Loading states
  loading: boolean;
  berthsLoading: boolean;
  vesselsLoading: boolean;
  operationsLoading: boolean;
  kpisLoading: boolean;

  // WebSocket
  connected: boolean;

  // Methods
  refreshBerths: () => Promise<void>;
  refreshVessels: () => Promise<void>;
  refreshOperations: () => Promise<void>;
  refreshKPIs: () => Promise<void>;
  refreshAll: () => Promise<void>;

  // WebSocket subscriptions
  subscribeToBerth: (berthId: string) => void;
  subscribeToVessel: (vesselId: string) => void;
  subscribeToOperation: (operationId: string) => void;
  subscribeToPort: () => void;
}

export const useSmartPort = (options: UseSmartPortOptions = {}): UseSmartPortReturn => {
  const { autoConnect = true, enableWebSocket = true } = options;

  // Data state
  const [berths, setBerths] = useState<Berth[]>([]);
  const [vessels, setVessels] = useState<Vessel[]>([]);
  const [operations, setOperations] = useState<PortOperation[]>([]);
  const [kpis, setKPIs] = useState<PortKPIs | null>(null);

  // Loading states
  const [loading, setLoading] = useState(true);
  const [berthsLoading, setBerthsLoading] = useState(false);
  const [vesselsLoading, setVesselsLoading] = useState(false);
  const [operationsLoading, setOperationsLoading] = useState(false);
  const [kpisLoading, setKPIsLoading] = useState(false);

  // WebSocket state
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<Socket | null>(null);

  // Refresh functions
  const refreshBerths = useCallback(async () => {
    setBerthsLoading(true);
    try {
      const data = await berthsApi.list();
      setBerths(data);
    } catch (error) {
      console.error('Error fetching berths:', error);
    } finally {
      setBerthsLoading(false);
    }
  }, []);

  const refreshVessels = useCallback(async () => {
    setVesselsLoading(true);
    try {
      const data = await vesselsApi.list();
      setVessels(data);
    } catch (error) {
      console.error('Error fetching vessels:', error);
    } finally {
      setVesselsLoading(false);
    }
  }, []);

  const refreshOperations = useCallback(async () => {
    setOperationsLoading(true);
    try {
      const data = await operationsApi.listActive();
      setOperations(data);
    } catch (error) {
      console.error('Error fetching operations:', error);
    } finally {
      setOperationsLoading(false);
    }
  }, []);

  const refreshKPIs = useCallback(async () => {
    setKPIsLoading(true);
    try {
      const data = await dashboardApi.getKPIs();
      setKPIs(data);
    } catch (error) {
      console.error('Error fetching KPIs:', error);
    } finally {
      setKPIsLoading(false);
    }
  }, []);

  const refreshAll = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
        refreshBerths(),
        refreshVessels(),
        refreshOperations(),
        refreshKPIs(),
      ]);
    } finally {
      setLoading(false);
    }
  }, [refreshBerths, refreshVessels, refreshOperations, refreshKPIs]);

  // WebSocket setup
  useEffect(() => {
    if (!enableWebSocket || !autoConnect) return;

    const token = localStorage.getItem('access_token');
    if (!token) return;

    const wsUrl = `${WS_BASE_URL}/api/v1/ws/smartport?token=${token}`;

    const newSocket = io(wsUrl, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });

    socketRef.current = newSocket;

    newSocket.on('connect', () => {
      console.log('SmartPort WebSocket connected');
      setConnected(true);
    });

    newSocket.on('disconnect', () => {
      console.log('SmartPort WebSocket disconnected');
      setConnected(false);
    });

    newSocket.on('error', (error: any) => {
      console.error('SmartPort WebSocket error:', error);
    });

    // Handle berth updates
    newSocket.on('berth_update', (data: any) => {
      console.log('Berth update:', data);
      setBerths((prev) =>
        prev.map((berth) => (berth.id === data.berth_id ? { ...berth, ...data.data } : berth))
      );
    });

    // Handle vessel updates
    newSocket.on('vessel_update', (data: any) => {
      console.log('Vessel update:', data);
      setVessels((prev) =>
        prev.map((vessel) => (vessel.id === data.vessel_id ? { ...vessel, ...data.data } : vessel))
      );
    });

    // Handle operation updates
    newSocket.on('operation_update', (data: any) => {
      console.log('Operation update:', data);
      setOperations((prev) =>
        prev.map((op) => (op.id === data.operation_id ? { ...op, ...data.data } : op))
      );
    });

    // Handle vessel arrival
    newSocket.on('vessel_arrived', (data: any) => {
      console.log('Vessel arrived:', data);
      refreshVessels();
      refreshKPIs();
    });

    // Handle vessel departure
    newSocket.on('vessel_departed', (data: any) => {
      console.log('Vessel departed:', data);
      refreshVessels();
      refreshKPIs();
    });

    // Handle operation status change
    newSocket.on('operation_status_changed', (data: any) => {
      console.log('Operation status changed:', data);
      refreshOperations();
      refreshKPIs();
    });

    // Subscribe to port-wide events
    newSocket.emit('subscribe_port');

    return () => {
      newSocket.close();
      socketRef.current = null;
    };
  }, [enableWebSocket, autoConnect, refreshVessels, refreshOperations, refreshKPIs]);

  // Load initial data
  useEffect(() => {
    if (autoConnect) {
      refreshAll();
    }
  }, [autoConnect, refreshAll]);

  // WebSocket subscription methods
  const subscribeToBerth = useCallback((berthId: string) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('subscribe_berth', { berth_id: berthId });
    }
  }, []);

  const subscribeToVessel = useCallback((vesselId: string) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('subscribe_vessel', { vessel_id: vesselId });
    }
  }, []);

  const subscribeToOperation = useCallback((operationId: string) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('subscribe_operation', { operation_id: operationId });
    }
  }, []);

  const subscribeToPort = useCallback(() => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('subscribe_port');
    }
  }, []);

  return {
    // Data
    berths,
    vessels,
    operations,
    kpis,

    // Loading states
    loading,
    berthsLoading,
    vesselsLoading,
    operationsLoading,
    kpisLoading,

    // WebSocket
    connected,

    // Methods
    refreshBerths,
    refreshVessels,
    refreshOperations,
    refreshKPIs,
    refreshAll,

    // WebSocket subscriptions
    subscribeToBerth,
    subscribeToVessel,
    subscribeToOperation,
    subscribeToPort,
  };
};
