/**
 * React Hook for WebSocket Connection
 */
import { useEffect } from 'react';
import { websocketService } from '../services/websocket';

interface UseWebSocketOptions {
  url?: string;
  onMessage?: (type: string, data: any) => void;
  autoConnect?: boolean;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const { url, onMessage, autoConnect = true } = options;

  useEffect(() => {
    if (autoConnect && url) {
      websocketService.connect(url);
    }

    if (onMessage) {
      const handler = (message: any) => {
        onMessage(message.type, message.data);
      };

      websocketService.on('*', handler);

      return () => {
        websocketService.off('*', handler);
      };
    }

    return () => {
      if (autoConnect) {
        websocketService.disconnect();
      }
    };
  }, [url, autoConnect, onMessage]);

  return {
    send: (type: string, data: any) => websocketService.send(type, data),
    on: (type: string, handler: (data: any) => void) => websocketService.on(type, handler),
    off: (type: string, handler: (data: any) => void) => websocketService.off(type, handler),
  };
};
