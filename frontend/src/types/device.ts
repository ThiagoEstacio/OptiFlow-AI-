export enum DeviceProtocol {
  OPC_UA = "opcua",
  MODBUS_TCP = "modbus_tcp",
  MODBUS_RTU = "modbus_rtu",
  MQTT = "mqtt",
  S7 = "s7",
  ETHERNET_IP = "ethernet_ip",
  HTTP = "http",
}

export enum DeviceStatus {
  CONNECTED = "connected",
  DISCONNECTED = "disconnected",
  ERROR = "error",
  UNKNOWN = "unknown",
}

export interface Device {
  id: string;
  site_id: string;
  name: string;
  description?: string;
  protocol: DeviceProtocol;
  connection_config: Record<string, any>;
  is_active: boolean;
  status: DeviceStatus;
  last_seen?: string;
  error_message?: string;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  firmware_version?: string;
  total_tags: number;
  data_points_collected: number;
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface DeviceCreate {
  site_id: string;
  name: string;
  description?: string;
  protocol: DeviceProtocol;
  connection_config: Record<string, any>;
  is_active?: boolean;
  manufacturer?: string;
  model?: string;
  serial_number?: string;
  firmware_version?: string;
  settings?: Record<string, any>;
}

export interface TestConnectionRequest {
  protocol: DeviceProtocol;
  connection_config: Record<string, any>;
}

export interface TestConnectionResponse {
  success: boolean;
  message?: string;
  server_info?: Record<string, any>;
  error?: string;
}

export interface BrowseTagsRequest {
  device_id?: string;
  protocol: DeviceProtocol;
  connection_config: Record<string, any>;
  max_depth?: number;
}

export interface BrowsedTag {
  name: string;
  display_name: string;
  browse_name: string;
  node_id: string;
  address: string;
  data_type: string;
  full_path: string;
  description: string;
  namespace_index: number;
  current_value?: string;
  quality?: string;
  timestamp?: string;
}

export interface BrowseTagsResponse {
  success: boolean;
  tags: BrowsedTag[];
  total: number;
  error?: string;
}

export interface ImportTagsRequest {
  device_id: string;
  tags: BrowsedTag[];
  auto_activate?: boolean;
  category?: string;
}
