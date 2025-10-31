import { apiClient } from './client';
import type {
  Device,
  DeviceCreate,
  TestConnectionRequest,
  TestConnectionResponse,
  BrowseTagsRequest,
  BrowseTagsResponse,
  ImportTagsRequest,
} from '../types/device';

export const devicesApi = {
  // List devices
  list: async (params?: {
    skip?: number;
    limit?: number;
    site_id?: string;
    protocol?: string;
    is_active?: boolean;
  }) => {
    const response = await apiClient.get<{
      devices: Device[];
      total: number;
      page: number;
      page_size: number;
    }>('/devices/', { params });
    return response.data;
  },

  // Get device by ID
  get: async (deviceId: string) => {
    const response = await apiClient.get<Device>(`/devices/${deviceId}`);
    return response.data;
  },

  // Create device
  create: async (data: DeviceCreate) => {
    const response = await apiClient.post<Device>('/devices/', data);
    return response.data;
  },

  // Update device
  update: async (deviceId: string, data: Partial<DeviceCreate>) => {
    const response = await apiClient.put<Device>(`/devices/${deviceId}`, data);
    return response.data;
  },

  // Delete device
  delete: async (deviceId: string) => {
    await apiClient.delete(`/devices/${deviceId}`);
  },

  // Test connection
  testConnection: async (data: TestConnectionRequest) => {
    const response = await apiClient.post<TestConnectionResponse>(
      '/devices/test-connection',
      data
    );
    return response.data;
  },

  // Browse tags
  browseTags: async (data: BrowseTagsRequest) => {
    const response = await apiClient.post<BrowseTagsResponse>(
      '/devices/browse-tags',
      data
    );
    return response.data;
  },

  // Import tags
  importTags: async (data: ImportTagsRequest) => {
    const response = await apiClient.post<{
      success: boolean;
      imported: number;
      skipped: number;
      total: number;
    }>('/devices/import-tags', data);
    return response.data;
  },
};
