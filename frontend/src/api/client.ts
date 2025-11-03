/**
 * API Client for OptiFlow Backend
 */
import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  User,
  LoginRequest,
  LoginResponse,
  Organization,
  Site,
  Device,
  Tag,
  TimeseriesDataPoint,
  TimeseriesQueryParams,
  AlarmDefinition,
  AlarmEvent,
  DashboardStats,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Load token from localStorage
    const storedToken = localStorage.getItem('auth_token');
    if (storedToken) {
      this.setToken(storedToken);
    }

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Unauthorized - clear token and redirect to login
          this.clearToken();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  getToken(): string | null {
    return this.token;
  }

  // Auth endpoints
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await this.client.post<LoginResponse>('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    this.setToken(response.data.access_token);
    return response.data;
  }

  async logout() {
    this.clearToken();
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/api/v1/auth/me');
    return response.data;
  }

  // Organization endpoints
  async getOrganizations(): Promise<Organization[]> {
    const response = await this.client.get<Organization[]>('/api/v1/organizations/');
    return response.data;
  }

  async getOrganization(id: string): Promise<Organization> {
    const response = await this.client.get<Organization>(`/api/v1/organizations/${id}`);
    return response.data;
  }

  async createOrganization(data: Partial<Organization>): Promise<Organization> {
    const response = await this.client.post<Organization>('/api/v1/organizations/', data);
    return response.data;
  }

  async updateOrganization(id: string, data: Partial<Organization>): Promise<Organization> {
    const response = await this.client.put<Organization>(`/api/v1/organizations/${id}`, data);
    return response.data;
  }

  async deleteOrganization(id: string): Promise<void> {
    await this.client.delete(`/api/v1/organizations/${id}`);
  }

  // Site endpoints
  async getSites(params?: { organization_id?: string; site_type?: string }): Promise<Site[]> {
    const response = await this.client.get<Site[]>('/api/v1/sites/', { params });
    return response.data;
  }

  async getSite(id: string): Promise<Site> {
    const response = await this.client.get<Site>(`/api/v1/sites/${id}`);
    return response.data;
  }

  async createSite(data: Partial<Site>): Promise<Site> {
    const response = await this.client.post<Site>('/api/v1/sites/', data);
    return response.data;
  }

  async updateSite(id: string, data: Partial<Site>): Promise<Site> {
    const response = await this.client.put<Site>(`/api/v1/sites/${id}`, data);
    return response.data;
  }

  async deleteSite(id: string): Promise<void> {
    await this.client.delete(`/api/v1/sites/${id}`);
  }

  // Device endpoints
  async getDevices(params?: { site_id?: string }): Promise<Device[]> {
    const response = await this.client.get<Device[]>('/api/v1/devices/', { params });
    return response.data;
  }

  async getDevice(id: string): Promise<Device> {
    const response = await this.client.get<Device>(`/api/v1/devices/${id}`);
    return response.data;
  }

  async createDevice(data: Partial<Device>): Promise<Device> {
    const response = await this.client.post<Device>('/api/v1/devices/', data);
    return response.data;
  }

  async updateDevice(id: string, data: Partial<Device>): Promise<Device> {
    const response = await this.client.put<Device>(`/api/v1/devices/${id}`, data);
    return response.data;
  }

  async deleteDevice(id: string): Promise<void> {
    await this.client.delete(`/api/v1/devices/${id}`);
  }

  // Tag endpoints
  async getTags(params?: { device_id?: string }): Promise<Tag[]> {
    const response = await this.client.get<Tag[]>('/api/v1/tags/', { params });
    return response.data;
  }

  async getTag(id: string): Promise<Tag> {
    const response = await this.client.get<Tag>(`/api/v1/tags/${id}`);
    return response.data;
  }

  async createTag(data: Partial<Tag>): Promise<Tag> {
    const response = await this.client.post<Tag>('/api/v1/tags/', data);
    return response.data;
  }

  async updateTag(id: string, data: Partial<Tag>): Promise<Tag> {
    const response = await this.client.put<Tag>(`/api/v1/tags/${id}`, data);
    return response.data;
  }

  async deleteTag(id: string): Promise<void> {
    await this.client.delete(`/api/v1/tags/${id}`);
  }

  // Timeseries endpoints
  async getTagData(params: TimeseriesQueryParams): Promise<TimeseriesDataPoint[]> {
    const response = await this.client.get<TimeseriesDataPoint[]>(
      `/api/v1/timeseries/tags/${params.tag_id}/data`,
      {
        params: {
          start: params.start,
          end: params.end,
          range: params.range,
          aggregation: params.aggregation,
          window: params.window,
        },
      }
    );
    return response.data;
  }

  async getLatestValue(tagId: string): Promise<TimeseriesDataPoint> {
    const response = await this.client.get<TimeseriesDataPoint>(
      `/api/v1/timeseries/tags/${tagId}/latest`
    );
    return response.data;
  }

  async writeDataPoint(tagId: string, value: any, timestamp?: string): Promise<void> {
    await this.client.post('/api/v1/timeseries/write', {
      tag_id: tagId,
      value,
      timestamp: timestamp || new Date().toISOString(),
    });
  }

  // Alarm endpoints
  async getAlarmDefinitions(params?: { tag_id?: string }): Promise<AlarmDefinition[]> {
    const response = await this.client.get<AlarmDefinition[]>('/api/v1/alarms/definitions/', {
      params,
    });
    return response.data;
  }

  async getAlarmDefinition(id: string): Promise<AlarmDefinition> {
    const response = await this.client.get<AlarmDefinition>(`/api/v1/alarms/definitions/${id}`);
    return response.data;
  }

  async createAlarmDefinition(data: Partial<AlarmDefinition>): Promise<AlarmDefinition> {
    const response = await this.client.post<AlarmDefinition>('/api/v1/alarms/definitions/', data);
    return response.data;
  }

  async updateAlarmDefinition(id: string, data: Partial<AlarmDefinition>): Promise<AlarmDefinition> {
    const response = await this.client.put<AlarmDefinition>(`/api/v1/alarms/definitions/${id}`, data);
    return response.data;
  }

  async deleteAlarmDefinition(id: string): Promise<void> {
    await this.client.delete(`/api/v1/alarms/definitions/${id}`);
  }

  async getAlarmEvents(params?: { active?: boolean }): Promise<AlarmEvent[]> {
    const response = await this.client.get<AlarmEvent[]>('/api/v1/alarms/events/', { params });
    return response.data;
  }

  async acknowledgeAlarm(alarmEventId: string): Promise<void> {
    await this.client.post(`/api/v1/alarms/events/${alarmEventId}/acknowledge`);
  }

  // Dashboard endpoints
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await this.client.get<DashboardStats>('/api/v1/dashboard/stats');
    return response.data;
  }

  // User endpoints
  async getUsers(): Promise<User[]> {
    const response = await this.client.get<User[]>('/api/v1/users/');
    return response.data;
  }

  async getUser(id: string): Promise<User> {
    const response = await this.client.get<User>(`/api/v1/users/${id}`);
    return response.data;
  }

  async createUser(data: Partial<User> & { password: string }): Promise<User> {
    const response = await this.client.post<User>('/api/v1/users/', data);
    return response.data;
  }

  async updateUser(id: string, data: Partial<User>): Promise<User> {
    const response = await this.client.put<User>(`/api/v1/users/${id}`, data);
    return response.data;
  }

  async deleteUser(id: string): Promise<void> {
    await this.client.delete(`/api/v1/users/${id}`);
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await this.client.get('/api/v1/health');
      return true;
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;
