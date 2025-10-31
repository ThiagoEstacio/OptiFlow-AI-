import { apiClient } from './client';
import type { Tag, TagWithDevice, TagValue } from '../types/tag';

export const tagsApi = {
  // List tags
  list: async (params?: {
    skip?: number;
    limit?: number;
    device_id?: string;
    site_id?: string;
    category?: string;
    is_active?: boolean;
    search?: string;
  }) => {
    const response = await apiClient.get<{
      tags: Tag[];
      total: number;
      page: number;
      page_size: number;
    }>('/tags/', { params });
    return response.data;
  },

  // List tags with device info
  listWithDevices: async (params?: {
    skip?: number;
    limit?: number;
    device_id?: string;
    site_id?: string;
  }) => {
    const response = await apiClient.get<{
      tags: TagWithDevice[];
      total: number;
    }>('/tags/with-devices', { params });
    return response.data;
  },

  // Get tag by ID
  get: async (tagId: string) => {
    const response = await apiClient.get<Tag>(`/tags/${tagId}`);
    return response.data;
  },

  // Get latest tag value
  getLatest: async (tagId: string) => {
    const response = await apiClient.get<TagValue>(`/tags/${tagId}/latest`);
    return response.data;
  },

  // Get tag history
  getHistory: async (
    tagId: string,
    params?: {
      start_time?: string;
      end_time?: string;
      limit?: number;
    }
  ) => {
    const response = await apiClient.get<{
      tag_id: string;
      tag_name: string;
      start_time: string;
      end_time: string;
      data_points: Array<{ timestamp: string; value: any; quality: string }>;
      count: number;
    }>(`/tags/${tagId}/history`, { params });
    return response.data;
  },
};
