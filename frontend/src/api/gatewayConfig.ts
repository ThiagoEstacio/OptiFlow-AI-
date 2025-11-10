/**
 * Gateway Configuration API Service
 */
import axios from 'axios';
import type {
  GatewayConfig,
  GatewayConfigList,
  GatewayConfigCreate,
  OPCUADiscoveryRequest,
  OPCUADiscoveryResponse,
  OPCUADiscoveryImportRequest,
} from '../types/gateway';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_BASE = `${BASE_URL}/api/v1/gateway-config`;

// Helper to get auth token
const getAuthHeader = () => {
  const token = localStorage.getItem('auth_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const gatewayConfigApi = {
  /**
   * List all gateway configurations
   */
  list: async (params?: {
    skip?: number;
    limit?: number;
    enabled_only?: boolean;
    gateway_type?: string;
  }): Promise<GatewayConfigList[]> => {
    const response = await axios.get<GatewayConfigList[]>(API_BASE + '/', {
      params,
      headers: getAuthHeader(),
    });
    return response.data;
  },

  /**
   * Get gateway configuration by ID
   */
  get: async (id: number): Promise<GatewayConfig> => {
    const response = await axios.get<GatewayConfig>(`${API_BASE}/${id}`, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  /**
   * Create new gateway configuration
   */
  create: async (data: GatewayConfigCreate): Promise<GatewayConfig> => {
    const response = await axios.post<GatewayConfig>(API_BASE + '/', data, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  /**
   * Update gateway configuration
   */
  update: async (id: number, data: Partial<GatewayConfigCreate>): Promise<GatewayConfig> => {
    const response = await axios.put<GatewayConfig>(`${API_BASE}/${id}`, data, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  /**
   * Delete gateway configuration
   */
  delete: async (id: number): Promise<void> => {
    await axios.delete(`${API_BASE}/${id}`, {
      headers: getAuthHeader(),
    });
  },

  /**
   * Enable gateway
   */
  enable: async (id: number): Promise<GatewayConfig> => {
    const response = await axios.post<GatewayConfig>(`${API_BASE}/${id}/enable`, null, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  /**
   * Disable gateway
   */
  disable: async (id: number): Promise<GatewayConfig> => {
    const response = await axios.post<GatewayConfig>(`${API_BASE}/${id}/disable`, null, {
      headers: getAuthHeader(),
    });
    return response.data;
  },

  /**
   * Discover OPC-UA tags
   */
  discoverOPCUA: async (request: OPCUADiscoveryRequest): Promise<OPCUADiscoveryResponse> => {
    const response = await axios.post<OPCUADiscoveryResponse>(
      `${API_BASE}/discover/opcua`,
      request,
      {
        headers: getAuthHeader(),
        timeout: 60000, // 60 seconds for discovery
      }
    );
    return response.data;
  },

  /**
   * Discover and import OPC-UA gateway
   */
  importOPCUA: async (request: OPCUADiscoveryImportRequest): Promise<GatewayConfig> => {
    const response = await axios.post<GatewayConfig>(
      `${API_BASE}/discover/opcua/import`,
      request,
      {
        headers: getAuthHeader(),
        timeout: 60000, // 60 seconds for discovery + import
      }
    );
    return response.data;
  },

  /**
   * Tag Management APIs
   */
  tags: {
    /**
     * List all tags for a gateway
     */
    list: async (gatewayId: number, enabledOnly?: boolean) => {
      const response = await axios.get(`${API_BASE}/${gatewayId}/tags`, {
        params: { enabled_only: enabledOnly },
        headers: getAuthHeader(),
      });
      return response.data;
    },

    /**
     * Create a new tag
     */
    create: async (gatewayId: number, tag: any) => {
      const response = await axios.post(`${API_BASE}/${gatewayId}/tags`, tag, {
        headers: getAuthHeader(),
      });
      return response.data;
    },

    /**
     * Update a tag
     */
    update: async (gatewayId: number, tagId: number, tag: any) => {
      const response = await axios.put(`${API_BASE}/${gatewayId}/tags/${tagId}`, tag, {
        headers: getAuthHeader(),
      });
      return response.data;
    },

    /**
     * Delete a tag
     */
    delete: async (gatewayId: number, tagId: number) => {
      await axios.delete(`${API_BASE}/${gatewayId}/tags/${tagId}`, {
        headers: getAuthHeader(),
      });
    },
  },
};
