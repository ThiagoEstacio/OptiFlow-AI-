/**
 * PLC API Client
 *
 * API functions for PLC tag operations and time series data
 */
import api from './client';

// ============================================================================
// Types
// ============================================================================

export interface PLCTag {
  name: string;
  address: string;
  data_type: string;
  description: string;
  unit: string;
  min_value?: number;
  max_value?: number;
  value?: any;
  timestamp?: string;
  quality: string;
}

export interface PLCTagValue {
  name: string;
  value: any;
  timestamp: string;
  quality: string;
  unit: string;
  description: string;
}

export interface HistoricalDataPoint {
  time: string;
  value: number;
}

export interface PLCStatistics {
  mean: number;
  min: number;
  max: number;
  stddev: number;
}

// ============================================================================
// PLC API
// ============================================================================

export const plcApi = {
  /**
   * List all available PLC tags
   */
  listTags: async () => {
    const response = await api.get<{ tags: PLCTag[] }>('/api/v1/plc/tags');
    return response.data.tags;
  },

  /**
   * Read current value of a specific tag
   */
  readTag: async (tagName: string) => {
    const response = await api.get<PLCTagValue>(`/api/v1/plc/tags/${tagName}`);
    return response.data;
  },

  /**
   * Get historical data for a tag
   */
  getHistory: async (
    tagName: string,
    params?: {
      hours?: number;
      aggregate?: 'mean' | 'min' | 'max' | 'sum';
      window?: string;
    }
  ) => {
    const response = await api.get<{
      tag_name: string;
      data: HistoricalDataPoint[];
      aggregate?: string;
      window?: string;
    }>(`/api/v1/plc/tags/${tagName}/history`, { params });
    return response.data;
  },

  /**
   * Get statistics for a tag over a period
   */
  getStatistics: async (tagName: string, hours: number = 24) => {
    const response = await api.get<{
      tag_name: string;
      statistics: PLCStatistics;
      period_hours: number;
    }>(`/api/v1/plc/tags/${tagName}/stats`, {
      params: { hours },
    });
    return response.data;
  },
};

export default plcApi;
