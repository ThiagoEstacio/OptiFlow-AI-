/**
 * Gateway Edge API Service
 *
 * Client for the OptiFlow Gateway Edge microservice
 * Handles real-time tag data, compression stats, formula engine, and automation
 */
import axios from 'axios';

// Gateway Edge runs on port 8080
// In production (Docker), use the nginx proxy at /gateway-api
// In development, connect directly to localhost:8080
const isProduction = import.meta.env.PROD;
const GATEWAY_BASE_URL = import.meta.env.VITE_GATEWAY_URL || (isProduction ? '' : 'http://localhost:8080');
const API_BASE = isProduction ? '/gateway-api' : `${GATEWAY_BASE_URL}/api`;
const HEALTH_URL = isProduction ? '/gateway-api' : GATEWAY_BASE_URL; // Health endpoint

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

// ========================================
// Asset Framework Types (PI Asset Framework style)
// ========================================

export type ElementType = 'plant' | 'area' | 'equipment_group' | 'equipment' | 'component';
export type AttributeType = 'tag' | 'formula' | 'constant' | 'rollup';

export interface AssetAttribute {
  id: string;
  name: string;
  description?: string;
  data_type: string;
  uom?: string;
  attribute_type: AttributeType;
  tag_id?: string;
  tag_address?: string;
  formula?: string;
  constant_value?: any;
  current_value?: any;
  current_quality?: string;
  current_timestamp?: string;
  hi_hi?: number;
  hi?: number;
  lo?: number;
  lo_lo?: number;
  categories?: string[];
  metadata?: Record<string, any>;
}

export interface AssetElement {
  id: string;
  name: string;
  description?: string;
  element_type: ElementType;
  template_id?: string;
  parent_id?: string;
  path: string;
  attributes: AssetAttribute[];
  children: string[];
  icon?: string;
  color?: string;
  position?: { x: number; y: number };
  metadata?: Record<string, any>;
  tags?: string[];
  created_at: string;
  updated_at: string;
}

export interface AssetElementHierarchy {
  id: string;
  name: string;
  type: ElementType;
  path: string;
  template_id?: string;
  icon?: string;
  color?: string;
  attributes_count: number;
  children: AssetElementHierarchy[];
}

export interface AttributeTemplate {
  name: string;
  description?: string;
  data_type: string;
  default_uom?: string;
  attribute_type: AttributeType;
  tag_pattern?: string;
  formula?: string;
  categories?: string[];
  hi_hi?: number;
  hi?: number;
  lo?: number;
  lo_lo?: number;
}

export interface AssetTemplate {
  id: string;
  name: string;
  description?: string;
  element_type: ElementType;
  base_template_id?: string;
  attributes: AttributeTemplate[];
  icon?: string;
  color?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
  elements_count?: number;
}

export interface AssetFrameworkStats {
  total_templates: number;
  total_elements: number;
  root_elements: number;
  elements_by_type: Record<ElementType, number>;
  total_attributes: number;
  linked_attributes: number;
  unlinked_attributes: number;
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
   * Uses /api/tags/realtime/all which returns live values from subscriptions
   */
  getAllRealtimeValues: async (): Promise<Record<string, RealtimeValue>> => {
    try {
      const response = await axios.get<{
        count: number;
        adapters: number;
        tags: Record<string, {
          value: number | boolean | string;
          quality: string;
          timestamp: string;
          address: string;
          adapter_id: string;
          protocol: string;
        }>;
      }>(`${API_BASE}/tags/realtime/all`);

      const result: Record<string, RealtimeValue> = {};

      Object.entries(response.data.tags).forEach(([tagName, tagData]) => {
        result[tagName] = {
          tag_id: tagName,
          value: tagData.value,
          quality: tagData.quality?.toLowerCase() || 'good',
          timestamp: tagData.timestamp,
          source: tagData.protocol
        };
      });

      return result;
    } catch (error) {
      console.error('Failed to get realtime values:', error);
      return {};
    }
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

  // ========================================
  // Asset Framework (PI Asset Framework style)
  // ========================================

  /**
   * Get asset framework hierarchy
   */
  getAssetHierarchy: async (rootId?: string): Promise<AssetElementHierarchy[]> => {
    try {
      const params = rootId ? { root_id: rootId } : {};
      const response = await axios.get<{ success: boolean; hierarchy: AssetElementHierarchy[]; root_count: number }>(
        `${API_BASE}/assets/hierarchy`,
        { params }
      );
      return response.data.hierarchy;
    } catch (error) {
      console.error('Failed to get asset hierarchy:', error);
      return [];
    }
  },

  /**
   * Get asset framework statistics
   */
  getAssetStats: async (): Promise<AssetFrameworkStats> => {
    try {
      const response = await axios.get<AssetFrameworkStats & { success: boolean }>(
        `${API_BASE}/assets/statistics`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get asset stats:', error);
      return {
        total_templates: 0,
        total_elements: 0,
        root_elements: 0,
        elements_by_type: {} as Record<ElementType, number>,
        total_attributes: 0,
        linked_attributes: 0,
        unlinked_attributes: 0
      };
    }
  },

  /**
   * List asset elements with optional filters
   */
  listAssetElements: async (params?: {
    element_type?: ElementType;
    template_id?: string;
    parent_id?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ total: number; elements: AssetElement[] }> => {
    try {
      const response = await axios.get<{
        success: boolean;
        total: number;
        limit: number;
        offset: number;
        elements: AssetElement[];
      }>(`${API_BASE}/assets/elements`, { params });
      return { total: response.data.total, elements: response.data.elements };
    } catch (error) {
      console.error('Failed to list asset elements:', error);
      return { total: 0, elements: [] };
    }
  },

  /**
   * Get asset element by ID
   */
  getAssetElement: async (elementId: string, includeChildren?: boolean): Promise<AssetElement | null> => {
    try {
      const params = includeChildren ? { include_children: true } : {};
      const response = await axios.get<{ success: boolean; element: AssetElement }>(
        `${API_BASE}/assets/elements/${elementId}`,
        { params }
      );
      return response.data.element;
    } catch (error) {
      console.error('Failed to get asset element:', error);
      return null;
    }
  },

  /**
   * Get asset element by path
   */
  getAssetElementByPath: async (path: string): Promise<AssetElement | null> => {
    try {
      const response = await axios.get<{ success: boolean; element: AssetElement }>(
        `${API_BASE}/assets/elements/by-path/${encodeURIComponent(path)}`
      );
      return response.data.element;
    } catch (error) {
      console.error('Failed to get asset element by path:', error);
      return null;
    }
  },

  /**
   * Create a new asset element
   */
  createAssetElement: async (element: {
    name: string;
    description?: string;
    element_type: ElementType;
    template_id?: string;
    parent_id?: string;
    icon?: string;
    color?: string;
    attributes?: Partial<AssetAttribute>[];
    metadata?: Record<string, any>;
  }): Promise<AssetElement | null> => {
    try {
      const response = await axios.post<{ success: boolean; message: string; element: AssetElement }>(
        `${API_BASE}/assets/elements`,
        element
      );
      return response.data.element;
    } catch (error) {
      console.error('Failed to create asset element:', error);
      return null;
    }
  },

  /**
   * Update an asset element
   */
  updateAssetElement: async (
    elementId: string,
    updates: {
      name?: string;
      description?: string;
      template_id?: string;
      icon?: string;
      color?: string;
      metadata?: Record<string, any>;
    }
  ): Promise<AssetElement | null> => {
    try {
      const response = await axios.put<{ success: boolean; message: string; element: AssetElement }>(
        `${API_BASE}/assets/elements/${elementId}`,
        updates
      );
      return response.data.element;
    } catch (error) {
      console.error('Failed to update asset element:', error);
      return null;
    }
  },

  /**
   * Delete an asset element
   */
  deleteAssetElement: async (elementId: string, recursive?: boolean): Promise<boolean> => {
    try {
      const params = recursive ? { recursive: true } : {};
      await axios.delete(`${API_BASE}/assets/elements/${elementId}`, { params });
      return true;
    } catch (error) {
      console.error('Failed to delete asset element:', error);
      return false;
    }
  },

  /**
   * List asset templates
   */
  listAssetTemplates: async (elementType?: ElementType): Promise<AssetTemplate[]> => {
    try {
      const params = elementType ? { element_type: elementType } : {};
      const response = await axios.get<{ success: boolean; total: number; templates: AssetTemplate[] }>(
        `${API_BASE}/assets/templates`,
        { params }
      );
      return response.data.templates;
    } catch (error) {
      console.error('Failed to list asset templates:', error);
      return [];
    }
  },

  /**
   * Get asset template by ID
   */
  getAssetTemplate: async (templateId: string): Promise<AssetTemplate | null> => {
    try {
      const response = await axios.get<{ success: boolean; template: AssetTemplate }>(
        `${API_BASE}/assets/templates/${templateId}`
      );
      return response.data.template;
    } catch (error) {
      console.error('Failed to get asset template:', error);
      return null;
    }
  },

  /**
   * Create a new asset template
   */
  createAssetTemplate: async (template: {
    name: string;
    description?: string;
    element_type: ElementType;
    base_template_id?: string;
    icon?: string;
    color?: string;
    attributes?: AttributeTemplate[];
    metadata?: Record<string, any>;
  }): Promise<AssetTemplate | null> => {
    try {
      const response = await axios.post<{ success: boolean; message: string; template: AssetTemplate }>(
        `${API_BASE}/assets/templates`,
        template
      );
      return response.data.template;
    } catch (error) {
      console.error('Failed to create asset template:', error);
      return null;
    }
  },

  /**
   * Delete an asset template
   */
  deleteAssetTemplate: async (templateId: string): Promise<boolean> => {
    try {
      await axios.delete(`${API_BASE}/assets/templates/${templateId}`);
      return true;
    } catch (error) {
      console.error('Failed to delete asset template:', error);
      return false;
    }
  },

  /**
   * Build asset hierarchy from tags_config.json
   */
  buildAssetHierarchyFromTags: async (): Promise<AssetFrameworkStats> => {
    try {
      const response = await axios.post<{
        success: boolean;
        message: string;
        statistics: AssetFrameworkStats;
      }>(`${API_BASE}/assets/build`);
      return response.data.statistics;
    } catch (error) {
      console.error('Failed to build asset hierarchy:', error);
      throw error;
    }
  },

  /**
   * Save asset framework configuration
   */
  saveAssetConfiguration: async (): Promise<boolean> => {
    try {
      await axios.post(`${API_BASE}/assets/save`);
      return true;
    } catch (error) {
      console.error('Failed to save asset configuration:', error);
      return false;
    }
  },

  /**
   * Reload asset framework configuration
   */
  reloadAssetConfiguration: async (): Promise<AssetFrameworkStats> => {
    try {
      const response = await axios.post<{
        success: boolean;
        message: string;
        statistics: AssetFrameworkStats;
      }>(`${API_BASE}/assets/reload`);
      return response.data.statistics;
    } catch (error) {
      console.error('Failed to reload asset configuration:', error);
      throw error;
    }
  },

  /**
   * Get available tags for linking to attributes
   */
  getAvailableTags: async (adapterId?: string, search?: string): Promise<{
    tags: Array<{
      tag_id: string;
      tag_name: string;
      address: string;
      adapter_id: string;
      data_type: string;
      metadata?: {
        engineering_units?: string;
        description?: string;
      };
    }>;
    total: number;
    adapters: string[];
  }> => {
    try {
      const params: Record<string, string> = {};
      if (adapterId) params.adapter_id = adapterId;
      if (search) params.search = search;

      const response = await axios.get(`${API_BASE}/assets/available-tags`, { params });
      return {
        tags: response.data.tags,
        total: response.data.total,
        adapters: response.data.adapters
      };
    } catch (error) {
      console.error('Failed to get available tags:', error);
      return { tags: [], total: 0, adapters: [] };
    }
  },

  /**
   * Add attribute (tag link) to element
   */
  addAttributeToElement: async (elementId: string, attribute: {
    name: string;
    description?: string;
    data_type?: string;
    uom?: string;
    tag_id?: string;
    tag_address?: string;
    hi_hi?: number;
    hi?: number;
    lo?: number;
    lo_lo?: number;
  }): Promise<AssetElement | null> => {
    try {
      const response = await axios.post<{
        success: boolean;
        message: string;
        element: AssetElement;
      }>(`${API_BASE}/assets/elements/${elementId}/attributes`, attribute);
      return response.data.element;
    } catch (error) {
      console.error('Failed to add attribute:', error);
      throw error;
    }
  },

  /**
   * Update attribute on element
   */
  updateAttribute: async (elementId: string, attributeId: string, attribute: {
    name: string;
    description?: string;
    data_type?: string;
    uom?: string;
    tag_id?: string;
    tag_address?: string;
    hi_hi?: number;
    hi?: number;
    lo?: number;
    lo_lo?: number;
  }): Promise<AssetElement | null> => {
    try {
      const response = await axios.put<{
        success: boolean;
        message: string;
        element: AssetElement;
      }>(`${API_BASE}/assets/elements/${elementId}/attributes/${attributeId}`, attribute);
      return response.data.element;
    } catch (error) {
      console.error('Failed to update attribute:', error);
      throw error;
    }
  },

  /**
   * Delete attribute from element
   */
  deleteAttribute: async (elementId: string, attributeId: string): Promise<boolean> => {
    try {
      await axios.delete(`${API_BASE}/assets/elements/${elementId}/attributes/${attributeId}`);
      return true;
    } catch (error) {
      console.error('Failed to delete attribute:', error);
      return false;
    }
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
