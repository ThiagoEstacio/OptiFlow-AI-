/**
 * TypeScript Types for OptiFlow AI Platform
 */

// Common
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
  status?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// Auth
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  organization_id?: string;
}

// Organizations & Sites
export interface Organization {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Site {
  id: string;
  name: string;
  description?: string;
  location?: string;
  organization_id: string;
  created_at: string;
  updated_at: string;
}

// Devices & Tags
export interface Device {
  id: string;
  name: string;
  description?: string;
  device_type: string;
  connection_string?: string;
  site_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Tag {
  id: string;
  name: string;
  description?: string;
  tag_type: 'analog' | 'digital' | 'string';
  unit?: string;
  device_id: string;
  min_value?: number;
  max_value?: number;
  created_at: string;
  updated_at: string;
}

// Time Series
export interface TimeSeriesPoint {
  timestamp: string;
  value: number;
  quality?: string;
  tag_id?: string;
  device_id?: string;
}

export interface TimeSeriesQuery {
  tag_ids: string[];
  start_time: string;
  end_time?: string;
  aggregation?: 'mean' | 'sum' | 'min' | 'max' | 'first' | 'last';
  interval?: string;
}

// Analytics
export interface Statistics {
  count: number;
  mean: number;
  median: number;
  std: number;
  variance: number;
  min: number;
  max: number;
  range: number;
  percentiles: {
    p25: number;
    p50: number;
    p75: number;
    p90: number;
    p95: number;
    p99: number;
  };
  skewness: number;
  kurtosis: number;
}

export interface Anomaly extends TimeSeriesPoint {
  anomaly_score: number;
  method: 'zscore' | 'iqr' | 'mad';
}

export interface Trend {
  slope: number;
  intercept: number;
  r_squared: number;
  p_value: number;
  std_error: number;
  direction: 'increasing' | 'decreasing' | 'stable';
  strength: number;
  moving_average: number[];
}

export interface Forecast extends TimeSeriesPoint {
  type: 'forecast';
}

export interface Correlation {
  pearson: {
    correlation: number;
    p_value: number;
    significant: boolean;
  };
  spearman: {
    correlation: number;
    p_value: number;
    significant: boolean;
  };
  sample_size: number;
}

// Annotations
export type AnnotationType = 'comment' | 'event' | 'alarm' | 'maintenance' | 'observation' | 'issue';
export type AnnotationPriority = 'low' | 'medium' | 'high' | 'critical';

export interface Annotation {
  id: string;
  type: AnnotationType;
  priority: AnnotationPriority;
  title: string;
  description?: string;
  start_time: string;
  end_time?: string;
  device_id?: string;
  tag_id?: string;
  site_id?: string;
  tags: string[];
  metadata?: Record<string, any>;
  is_public: boolean;
  is_resolved: boolean;
  resolved_at?: string;
  resolved_by?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
  comments_count?: number;
}

export interface AnnotationComment {
  id: string;
  annotation_id: string;
  comment: string;
  created_by?: string;
  parent_comment_id?: string;
  created_at: string;
  updated_at: string;
  is_edited: boolean;
  replies?: AnnotationComment[];
}

// WebSocket
export interface WebSocketMessage {
  type: string;
  tag_id?: string;
  device_id?: string;
  room_id?: string;
  tag_ids?: string[];
  data?: any;
  timestamp?: string;
}

export interface TagUpdate {
  type: 'tag_update';
  tag_id: string;
  data: TimeSeriesPoint;
  timestamp: string;
}

export interface DeviceUpdate {
  type: 'device_update';
  device_id: string;
  data: any;
  timestamp: string;
}

// Dashboard
export interface DashboardWidget {
  id: string;
  type: 'line-chart' | 'bar-chart' | 'gauge' | 'table' | 'stat-card';
  title: string;
  tag_ids: string[];
  config: Record<string, any>;
  position: { x: number; y: number; w: number; h: number };
}

export interface Dashboard {
  id: string;
  name: string;
  description?: string;
  widgets: DashboardWidget[];
  created_at: string;
  updated_at: string;
}
