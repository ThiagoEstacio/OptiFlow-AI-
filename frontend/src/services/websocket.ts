/**
 * WebSocket Service for Real-Time Updates
 * Enhanced with connection handlers and improved reconnection logic
 */

type MessageHandler = (data: any) => void;
type ConnectionHandler = () => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectInterval: number = 5000;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private messageHandlers: Map<string, MessageHandler[]> = new Map();
  private connectHandlers: ConnectionHandler[] = [];
  private disconnectHandlers: ConnectionHandler[] = [];
  private url: string = '';
  private isIntentionalClose: boolean = false;

  connect(url: string) {
    this.url = url;
    this.isIntentionalClose = false;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected');
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
        // Notify connection handlers
        this.connectHandlers.forEach(handler => handler());
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          const { type, ...data } = message; // Extract type and rest of message as data

          const handlers = this.messageHandlers.get(type);
          if (handlers) {
            // If message has explicit 'data' property, use it; otherwise use the rest of message
            const payload = message.data !== undefined ? message.data : data;
            handlers.forEach((handler) => handler(payload));
          }

          // Also call wildcard handlers
          const wildcardHandlers = this.messageHandlers.get('*');
          if (wildcardHandlers) {
            wildcardHandlers.forEach((handler) => handler(message));
          }
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        // Notify disconnection handlers
        this.disconnectHandlers.forEach(handler => handler());
        
        // Auto-reconnect if not intentional
        if (!this.isIntentionalClose) {
          this.reconnect();
        }
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.reconnect();
    }
  }

  disconnect() {
    this.isIntentionalClose = true;
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private reconnect() {
    if (this.reconnectTimer || this.isIntentionalClose) {
      return;
    }

    this.reconnectTimer = setTimeout(() => {
      console.log('🔄 Attempting to reconnect WebSocket...');
      this.connect(this.url);
    }, this.reconnectInterval);
  }

  on(type: string, handler: MessageHandler): () => void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type)!.push(handler);

    // Return unsubscribe function
    return () => this.off(type, handler);
  }

  off(type: string, handler: MessageHandler) {
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index !== -1) {
        handlers.splice(index, 1);
      }
    }
  }

  onConnect(handler: ConnectionHandler): () => void {
    this.connectHandlers.push(handler);
    return () => {
      const index = this.connectHandlers.indexOf(handler);
      if (index !== -1) {
        this.connectHandlers.splice(index, 1);
      }
    };
  }

  onDisconnect(handler: ConnectionHandler): () => void {
    this.disconnectHandlers.push(handler);
    return () => {
      const index = this.disconnectHandlers.indexOf(handler);
      if (index !== -1) {
        this.disconnectHandlers.splice(index, 1);
      }
    };
  }

  send(type: string, data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }));
    } else {
      console.warn('WebSocket not connected, message not sent');
    }
  }

  get isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

export const websocketService = new WebSocketService();
