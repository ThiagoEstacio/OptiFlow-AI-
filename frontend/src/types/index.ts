/**
 * TypeScript type definitions for OptiFlow Platform
 */

// User types
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "engineer" | "operator" | "viewer";
  is_active: boolean;
  is_superuser: boolean;
  organization_id?: string;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

// Organization types
export interface Organization {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
  settings?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Site types
export type SiteType = "smartport" | "smartmine" | "smartsteel";

export interface Site {
  id: string;
  name: string;
  site_type: SiteType;
  organization_id: string;
  description?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  postal_code?: string;
  latitude?: number;
  longitude?: number;
  timezone?: string;
  is_active: boolean;
  settings?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Device types
export type DeviceProtocol = "opc_ua" | "modbus" | "mqtt" | "s7" | "ethernet_ip" | "http";

export interface Device {
  id: string;
  name: string;
  site_id: string;
  device_type: string;
  protocol: DeviceProtocol;
  description?: string;
  ip_address?: string;
  port?: number;
  connection_config?: Record<string, any>;
  scan_rate?: number;
  enabled: boolean;
  status?: string;
  last_seen?: string;
  error_count?: number;
  last_error?: string;
  settings?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Tag types
export type TagDataType = "boolean" | "integer" | "float" | "string" | "double";
export type TagCategory = "process" | "energy" | "quality" | "production" | "maintenance" | "alarm" | "setpoint" | "status";

export interface Tag {
  id: string;
  name: string;
  device_id: string;
  description?: string;
  address: string;
  data_type: TagDataType;
  unit?: string;
  category?: TagCategory;
  scan_rate?: number;
  deadband?: number;
  scaling_factor?: number;
  scaling_offset?: number;
  min_value?: number;
  max_value?: number;
  enabled: boolean;
  settings?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Timeseries types
export interface TimeseriesDataPoint {
  timestamp: string;
  value: number | string | boolean;
  quality?: string;
}

export interface TimeseriesQueryParams {
  tag_id: string;
  start?: string;
  end?: string;
  range?: string;  // e.g., "1h", "24h", "7d"
  aggregation?: "mean" | "min" | "max" | "sum" | "count";
  window?: string;  // e.g., "1m", "5m", "1h"
}

export interface TimeseriesData {
  tag_id: string;
  data: TimeseriesDataPoint[];
}

// Alarm types
export type AlarmType = "high_limit" | "low_limit" | "rate_of_change" | "deviation" | "predictive" | "custom";
export type AlarmSeverity = "critical" | "high" | "medium" | "low";

export interface AlarmDefinition {
  id: string;
  name: string;
  tag_id: string;
  alarm_type: AlarmType;
  severity: AlarmSeverity;
  description?: string;
  setpoint: number;
  deadband?: number;
  delay?: number;
  enabled: boolean;
  notification_enabled: boolean;
  notification_emails?: string[];
  notification_sms?: string[];
  message_template?: string;
  created_at: string;
  updated_at: string;
}

export interface AlarmEvent {
  id: string;
  alarm_definition_id: string;
  tag_id: string;
  triggered_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  value: number;
  message: string;
  acknowledged_by?: string;
  is_active: boolean;
}

// Dashboard types
export interface DashboardStats {
  total_devices: number;
  active_devices: number;
  total_tags: number;
  active_alarms: number;
  data_points_today: number;
}

// Chart types
export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
  fill?: boolean;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// Form types
export interface FormErrors {
  [key: string]: string | string[];
}

// WebSocket types
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface TagUpdate {
  tag_id: string;
  tag_name: string;
  value: any;
  quality: string;
  timestamp: string;
}

export interface AlarmUpdate {
  alarm_id: string;
  alarm_name: string;
  severity: AlarmSeverity;
  message: string;
  timestamp: string;
}
