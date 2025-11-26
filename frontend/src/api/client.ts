/**
 * API Client for OptiFlow Backend
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
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

// Configuration constants for fault tolerance
const API_TIMEOUT = 30000; // 30 seconds
const MAX_RETRIES = 3;
const RETRY_DELAYS = [1000, 2000, 4000]; // Exponential backoff in milliseconds
const RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504]; // HTTP status codes that should trigger retry

// Extended config to track retry count
interface RetryableAxiosRequestConfig extends InternalAxiosRequestConfig {
  _retryCount?: number;
  _isRetry?: boolean;
}

/**
 * Sleep utility for exponential backoff
 */
const sleep = (ms: number): Promise<void> => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Determine if an error is retryable
 */
const isRetryableError = (error: AxiosError): boolean => {
  // Network errors (no response)
  if (!error.response) {
    return true;
  }

  // Check if status code is retryable
  const status = error.response.status;
  return RETRYABLE_STATUS_CODES.includes(status);
};

/**
 * Get user-friendly error message
 */
export const getErrorMessage = (error: any): string => {
  if (axios.isAxiosError(error)) {
    // Network errors
    if (!error.response) {
      if (error.code === 'ECONNABORTED') {
        return 'Request timed out. Please check your connection and try again.';
      }
      if (error.code === 'ERR_NETWORK') {
        return 'Unable to connect to server. Please check your internet connection.';
      }
      return 'Network error. Please check your connection and try again.';
    }

    // HTTP errors
    const status = error.response.status;
    if (status === 401) {
      return 'Your session has expired. Please log in again.';
    }
    if (status === 403) {
      return 'You do not have permission to perform this action.';
    }
    if (status === 404) {
      return 'The requested resource was not found.';
    }
    if (status === 408) {
      return 'Request timed out. Please try again.';
    }
    if (status === 429) {
      return 'Too many requests. Please wait a moment and try again.';
    }
    if (status >= 500) {
      return 'Server is temporarily unavailable. Please try again in a moment.';
    }

    // Use server message if available
    return error.response.data?.message || error.response.data?.detail || 'An unexpected error occurred.';
  }

  return error.message || 'An unexpected error occurred.';
};

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      timeout: API_TIMEOUT,
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
      (config: RetryableAxiosRequestConfig) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor with retry logic
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error: AxiosError) => {
        const config = error.config as RetryableAxiosRequestConfig;

        // Handle 401 Unauthorized
        if (error.response?.status === 401) {
          // Don't retry login requests
          if (!config.url?.includes('/auth/login')) {
            this.clearToken();
            window.location.href = '/login';
          }
          return Promise.reject(error);
        }

        // Initialize retry count
        if (!config._retryCount) {
          config._retryCount = 0;
        }

        // Check if we should retry
        if (config._retryCount < MAX_RETRIES && isRetryableError(error)) {
          config._retryCount++;
          config._isRetry = true;

          // Calculate delay with exponential backoff
          const delay = RETRY_DELAYS[config._retryCount - 1] || RETRY_DELAYS[RETRY_DELAYS.length - 1];

          // Log retry attempt (in production, you might want to send this to monitoring)
          console.warn(
            `Request failed. Retrying attempt ${config._retryCount}/${MAX_RETRIES} after ${delay}ms`,
            {
              url: config.url,
              status: error.response?.status,
              message: error.message,
            }
          );

          // Wait before retrying
          await sleep(delay);

          // Retry the request
          return this.client(config);
        }

        // Max retries exceeded or non-retryable error
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

  // Generic HTTP methods for direct API access
  async get<T = any>(url: string, config?: any): Promise<AxiosResponse<T>> {
    return this.client.get<T>(url, config);
  }

  async post<T = any>(url: string, data?: any, config?: any): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, data, config);
  }

  async put<T = any>(url: string, data?: any, config?: any): Promise<AxiosResponse<T>> {
    return this.client.put<T>(url, data, config);
  }

  async delete<T = any>(url: string, config?: any): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(url, config);
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
    const response = await this.client.get<Site>(`/api/v1/sites/${id}/`);
    return response.data;
  }

  async createSite(data: Partial<Site>): Promise<Site> {
    const response = await this.client.post<Site>('/api/v1/sites/', data);
    return response.data;
  }

  async updateSite(id: string, data: Partial<Site>): Promise<Site> {
    const response = await this.client.put<Site>(`/api/v1/sites/${id}/`, data);
    return response.data;
  }

  async deleteSite(id: string): Promise<void> {
    await this.client.delete(`/api/v1/sites/${id}/`);
  }

  // Device endpoints
  async getDevices(params?: { site_id?: string }): Promise<Device[]> {
    const response = await this.client.get<Device[]>('/api/v1/devices/', { params });
    return response.data;
  }

  async getDevice(id: string): Promise<Device> {
    const response = await this.client.get<Device>(`/api/v1/devices/${id}/`);
    return response.data;
  }

  async createDevice(data: Partial<Device>): Promise<Device> {
    const response = await this.client.post<Device>('/api/v1/devices/', data);
    return response.data;
  }

  async updateDevice(id: string, data: Partial<Device>): Promise<Device> {
    const response = await this.client.put<Device>(`/api/v1/devices/${id}/`, data);
    return response.data;
  }

  async deleteDevice(id: string): Promise<void> {
    await this.client.delete(`/api/v1/devices/${id}/`);
  }

  // Tag endpoints
  async getTags(params?: { device_id?: string }): Promise<Tag[]> {
    // Use the PostgreSQL tags endpoint to get all configured tags (not InfluxDB active tags)
    const response = await this.client.get<Tag[]>('/api/v1/tags/', { params });
    return response.data || [];
  }

  async getTag(id: string): Promise<Tag> {
    const response = await this.client.get<Tag>(`/api/v1/tags/${id}/`);
    return response.data;
  }

  async createTag(data: Partial<Tag>): Promise<Tag> {
    const response = await this.client.post<Tag>('/api/v1/tags/', data);
    return response.data;
  }

  async updateTag(id: string, data: Partial<Tag>): Promise<Tag> {
    const response = await this.client.put<Tag>(`/api/v1/tags/${id}/`, data);
    return response.data;
  }

  async deleteTag(id: string): Promise<void> {
    await this.client.delete(`/api/v1/tags/${id}/`);
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
    // Use /alarms/active endpoint for active alarms (more efficient)
    if (params?.active === true) {
      const response = await this.client.get<AlarmEvent[]>('/api/v1/alarms/active');
      return response.data;
    }
    // For non-active params, use /history endpoint
    const response = await this.client.get<AlarmEvent[]>('/api/v1/alarms/history', { params });
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
