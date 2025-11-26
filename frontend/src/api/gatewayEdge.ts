/**
 * Gateway Edge API Service
 *
 * Client for the OptiFlow Gateway Edge microservice
 * Handles real-time tag data, compression stats, formula engine, and automation
 */
import axios from 'axios';

// Gateway Edge runs on port 8080
const GATEWAY_BASE_URL = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8080';
const API_BASE = `${GATEWAY_BASE_URL}/api`;
const HEALTH_URL = GATEWAY_BASE_URL; // Health endpoint is at root, not under /api

// Types
export interface GatewayHealthResponse {
  status: string;
  gateway_id: string;
  gateway_name: string;
  mode: string;
  version: string;
  uptime_seconds: number;
  adapters_status: Record<string, {
    connected: boolean;
    last_read: string | null;
    error: string | null;
  }>;
  kafka_status: {
    connected: boolean;
    messages_sent: number;
  };
  timestamp: string;
}

export interface DiscoveredTag {
  tag_name: string;
  display_name: string;
  address: string;
  data_type: string;
  readable: boolean;
  writable: boolean;
  description?: string;
  unit?: string;
  adapter_id: string;
  protocol: string;
  last_value?: number | string | boolean;
  last_quality?: string;
  last_timestamp?: string;
}

export interface ManagedTag {
  tag_id: string;
  tag_name: string;
  address: string;
  data_type: string;
  enabled: boolean;
  scaling?: {
    enabled: boolean;
    raw_min?: number;
    raw_max?: number;
    eng_min?: number;
    eng_max?: number;
    mode: string;
  };
  deadband?: {
    enabled: boolean;
    type: string;
    value?: number;
    percentage?: number;
    time_ms?: number;
  };
  formula?: {
    enabled: boolean;
    expression?: string;
    input_tags: string[];
  };
}

export interface CompressionStats {
  total_received: number;
  total_archived: number;
  total_compressed: number;
  compression_ratio_percent: number;
  configured_tags: number;
}

export interface FormulaEngineStats {
  evaluations: number;
  errors: number;
  last_evaluation: string | null;
  avg_eval_time_ms: number;
  registered_formulas: number;
  cached_tags: number;
}

export interface RealtimeValue {
  tag_id: string;
  value: number | string | boolean;
  quality: string;
  timestamp: string;
  source: string;
}

export interface AdapterStatus {
  adapter_id: string;
  protocol: string;
  enabled: boolean;
  connected: boolean;
  host: string;
  port: number;
  tags_discovered: number;
  tags_monitored: number;
  last_scan: string | null;
  scan_rate_ms: number;
  error?: string;
}

// API Client
export const gatewayEdgeApi = {
  // ========================================
  // Health & Status
  // ========================================

  /**
   * Get gateway health status
   */
  getHealth: async (): Promise<GatewayHealthResponse> => {
    const response = await axios.get<GatewayHealthResponse>(`${HEALTH_URL}/health`);
    return response.data;
  },

  /**
   * Get gateway metrics (Prometheus format)
   */
  getMetrics: async (): Promise<string> => {
    const response = await axios.get(`${API_BASE}/metrics`);
    return response.data;
  },

  // ========================================
  // Tag Discovery
  // ========================================

  /**
   * Get all discovered tags from all adapters (live from OPC-UA/Modbus)
   */
  discoverAllTags: async (): Promise<DiscoveredTag[]> => {
    const response = await axios.get<{ count: number; tags: any[] }>(`${API_BASE}/tags/list`);
    // Map response to DiscoveredTag format
    return response.data.tags.map(tag => ({
      tag_name: tag.name,
      display_name: tag.name,
      address: tag.address,
      data_type: tag.data_type || 'double',
      readable: true,
      writable: false,
      adapter_id: tag.adapter_id,
      protocol: tag.protocol,
      last_value: tag.current_value,
      last_quality: tag.connected ? 'good' : 'bad',
      unit: tag.unit
    }));
  },

  /**
   * Discover tags from a specific adapter (triggers re-scan)
   */
  discoverAdapterTags: async (adapterId: string): Promise<DiscoveredTag[]> => {
    const response = await axios.post<{ discovered_tags: any[] }>(`${API_BASE}/adapters/${adapterId}/discover`);
    return response.data.discovered_tags.map(tag => ({
      tag_name: tag.name,
      display_name: tag.name,
      address: tag.address,
      data_type: tag.type || 'double',
      readable: true,
      writable: false,
      adapter_id: adapterId,
      protocol: 'opcua'
    }));
  },

  /**
   * Get discovery status
   */
  getDiscoveryStatus: async () => {
    const response = await axios.get(`${API_BASE}/adapters/`);
    return response.data;
  },

  // ========================================
  // Managed Tags (PI Point Builder style)
  // ========================================

  /**
   * List all managed tags
   */
  listManagedTags: async (): Promise<ManagedTag[]> => {
    const response = await axios.get<ManagedTag[]>(`${API_BASE}/tags/`);
    return response.data;
  },

  /**
   * Get managed tag by ID
   */
  getManagedTag: async (tagId: string): Promise<ManagedTag> => {
    const response = await axios.get<ManagedTag>(`${API_BASE}/tags/${tagId}`);
    return response.data;
  },

  /**
   * Create a managed tag
   */
  createManagedTag: async (tag: Partial<ManagedTag>): Promise<ManagedTag> => {
    const response = await axios.post<ManagedTag>(`${API_BASE}/tags/`, tag);
    return response.data;
  },

  /**
   * Update a managed tag
   */
  updateManagedTag: async (tagId: string, tag: Partial<ManagedTag>): Promise<ManagedTag> => {
    const response = await axios.put<ManagedTag>(`${API_BASE}/tags/${tagId}`, tag);
    return response.data;
  },

  /**
   * Delete a managed tag
   */
  deleteManagedTag: async (tagId: string): Promise<void> => {
    await axios.delete(`${API_BASE}/tags/${tagId}`);
  },

  /**
   * Bulk import tags
   */
  bulkImportTags: async (tags: Partial<ManagedTag>[]): Promise<{ imported: number; errors: string[] }> => {
    const response = await axios.post(`${API_BASE}/tags/bulk`, tags);
    return response.data;
  },

  // ========================================
  // Realtime Values
  // ========================================

  /**
   * Get realtime value for a tag
   */
  getRealtimeValue: async (tagId: string): Promise<RealtimeValue> => {
    const response = await axios.get<RealtimeValue>(`${API_BASE}/realtime/${tagId}`);
    return response.data;
  },

  /**
   * Get realtime values for multiple tags
   */
  getRealtimeValues: async (tagIds?: string[]): Promise<Record<string, RealtimeValue>> => {
    const params = tagIds ? { tag_ids: tagIds.join(',') } : {};
    const response = await axios.get(`${API_BASE}/realtime/values`, { params });
    return response.data;
  },

  /**
   * Get all current realtime values
   */
  getAllRealtimeValues: async (): Promise<Record<string, RealtimeValue>> => {
    const response = await axios.get(`${API_BASE}/realtime/all`);
    return response.data;
  },

  // ========================================
  // Compression (Swinging Door)
  // ========================================

  /**
   * Get compression statistics
   * NOTE: Compression is handled by Gateway but stats endpoint may not be available
   */
  getCompressionStats: async (): Promise<CompressionStats> => {
    try {
      // Try to get compression stats from gateway (if endpoint exists)
      const response = await axios.get<CompressionStats>(`${API_BASE}/compression/stats`);
      return response.data;
    } catch (error) {
      // Return default stats if endpoint not available
      return {
        total_received: 0,
        total_archived: 0,
        total_compressed: 0,
        compression_ratio_percent: 0,
        configured_tags: 0
      };
    }
  },

  /**
   * Get compression stats for a specific tag
   */
  getTagCompressionStats: async (tagId: string) => {
    try {
      const response = await axios.get(`${API_BASE}/compression/${tagId}`);
      return response.data;
    } catch (error) {
      return null;
    }
  },

  // ========================================
  // Formula Engine
  // ========================================

  /**
   * Get formula engine status
   */
  getFormulaEngineStatus: async (): Promise<FormulaEngineStats> => {
    try {
      // Correct endpoint path (router mounted at /api, formulas has prefix /formulas)
      const response = await axios.get<FormulaEngineStats>(`${API_BASE}/formulas/engine/status`);
      return response.data;
    } catch (error) {
      // Return default stats if endpoint not available
      return {
        evaluations: 0,
        errors: 0,
        last_evaluation: null,
        avg_eval_time_ms: 0,
        registered_formulas: 0,
        cached_tags: 0
      };
    }
  },

  /**
   * Get formula info for a tag
   */
  getFormulaInfo: async (tagId: string) => {
    try {
      const response = await axios.get(`${API_BASE}/formulas/${tagId}/info`);
      return response.data;
    } catch (error) {
      return null;
    }
  },

  /**
   * List all formulas
   */
  listFormulas: async () => {
    try {
      const response = await axios.get(`${API_BASE}/formulas/examples`);
      return response.data;
    } catch (error) {
      return { examples: [], available_functions: {} };
    }
  },

  /**
   * Evaluate all formulas manually
   */
  evaluateAllFormulas: async () => {
    try {
      const response = await axios.post(`${API_BASE}/formulas/engine/evaluate-all`);
      return response.data;
    } catch (error) {
      return { success: false, message: 'Formula evaluation not available' };
    }
  },

  // ========================================
  // Adapters
  // ========================================

  /**
   * List all adapters
   */
  listAdapters: async (): Promise<AdapterStatus[]> => {
    const response = await axios.get<AdapterStatus[]>(`${API_BASE}/adapters/`);
    return response.data;
  },

  /**
   * Get adapter status
   */
  getAdapterStatus: async (adapterId: string): Promise<AdapterStatus> => {
    const response = await axios.get<AdapterStatus>(`${API_BASE}/adapters/${adapterId}`);
    return response.data;
  },

  /**
   * Start an adapter
   */
  startAdapter: async (adapterId: string) => {
    const response = await axios.post(`${API_BASE}/adapters/${adapterId}/start`);
    return response.data;
  },

  /**
   * Stop an adapter
   */
  stopAdapter: async (adapterId: string) => {
    const response = await axios.post(`${API_BASE}/adapters/${adapterId}/stop`);
    return response.data;
  },

  /**
   * Trigger adapter rescan
   */
  rescanAdapter: async (adapterId: string) => {
    const response = await axios.post(`${API_BASE}/adapters/${adapterId}/rescan`);
    return response.data;
  },

  // ========================================
  // WebSocket URL helpers
  // ========================================

  /**
   * Get WebSocket URL for realtime updates
   */
  getRealtimeWebSocketUrl: (): string => {
    const wsBase = GATEWAY_BASE_URL.replace('http', 'ws');
    return `${wsBase}/ws/realtime`;
  },

  /**
   * Get WebSocket URL for alarms
   */
  getAlarmsWebSocketUrl: (): string => {
    const wsBase = GATEWAY_BASE_URL.replace('http', 'ws');
    return `${wsBase}/ws/alarms`;
  },
};

// WebSocket connection helper
export class GatewayWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(
    private url: string,
    private onMessage: (data: any) => void,
    private onStatusChange?: (connected: boolean) => void
  ) {}

  connect() {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('Gateway WebSocket connected:', this.url);
        this.reconnectAttempts = 0;
        this.onStatusChange?.(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.onMessage(data);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      this.ws.onclose = () => {
        console.log('Gateway WebSocket disconnected');
        this.onStatusChange?.(false);
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('Gateway WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.attemptReconnect();
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      setTimeout(() => this.connect(), delay);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}

export default gatewayEdgeApi;
