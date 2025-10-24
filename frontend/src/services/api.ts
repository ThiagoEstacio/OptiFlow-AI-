/**
 * API Client for OptiFlow Backend
 */
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for auth token
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized - redirect to login
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async login(username: string, password: string) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await this.client.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }

    return response.data;
  }

  async logout() {
    await this.client.post('/auth/logout');
    localStorage.removeItem('access_token');
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  // Organizations
  async getOrganizations(skip = 0, limit = 100) {
    const response = await this.client.get('/organizations/', {
      params: { skip, limit },
    });
    return response.data;
  }

  // Sites
  async getSites(organizationId?: string, skip = 0, limit = 100) {
    const response = await this.client.get('/sites/', {
      params: { organization_id: organizationId, skip, limit },
    });
    return response.data;
  }

  // Devices
  async getDevices(siteId?: string, skip = 0, limit = 100) {
    const response = await this.client.get('/devices/', {
      params: { site_id: siteId, skip, limit },
    });
    return response.data;
  }

  async getDevice(deviceId: string) {
    const response = await this.client.get(`/devices/${deviceId}`);
    return response.data;
  }

  // Tags
  async getTags(deviceId?: string, skip = 0, limit = 100) {
    const response = await this.client.get('/tags/', {
      params: { device_id: deviceId, skip, limit },
    });
    return response.data;
  }

  // Time Series Data
  async getTagData(
    tagId: string,
    startTime: string,
    endTime?: string,
    aggregation?: string,
    interval?: string
  ) {
    const response = await this.client.get(`/timeseries/tags/${tagId}`, {
      params: { start_time: startTime, end_time: endTime, aggregation, interval },
    });
    return response.data;
  }

  async writeTagData(points: any[]) {
    const response = await this.client.post('/timeseries/batch', points);
    return response.data;
  }

  // Alarms
  async getAlarms(skip = 0, limit = 100) {
    const response = await this.client.get('/alarms/', {
      params: { skip, limit },
    });
    return response.data;
  }
}

export const apiClient = new APIClient();
export default apiClient;
