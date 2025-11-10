/**
 * Gateway Configuration Types
 * Matching backend schemas from app/schemas/gateway_config.py
 */

export type GatewayType = "opcua" | "modbus_tcp" | "siemens_s7" | "rockwell_eip";

export interface GatewayTag {
  id: number;
  gateway_id: number;
  tag_name: string;
  enabled: boolean;
  address_config: Record<string, any>;
  data_type: string;
  scale_factor: number;
  offset: number;
  unit?: string;
  description?: string;
  created_at: string;
}

export interface GatewayTagCreate {
  tag_name: string;
  enabled?: boolean;
  address_config: Record<string, any>;
  data_type: string;
  scale_factor?: number;
  offset?: number;
  unit?: string;
  description?: string;
}

export interface GatewayConfig {
  id: number;
  name: string;
  gateway_type: GatewayType;
  enabled: boolean;
  connection_config: Record<string, any>;
  polling_interval_ms: number;
  max_retries: number;
  base_retry_delay: number;
  max_buffer_size: number;
  description?: string;
  created_at: string;
  updated_at?: string;
  tags: GatewayTag[];
}

export interface GatewayConfigList {
  id: number;
  name: string;
  gateway_type: GatewayType;
  enabled: boolean;
  description?: string;
  tags_count: number;
  created_at: string;
}

export interface GatewayConfigCreate {
  name: string;
  gateway_type: GatewayType;
  enabled?: boolean;
  connection_config: Record<string, any>;
  polling_interval_ms?: number;
  max_retries?: number;
  base_retry_delay?: number;
  max_buffer_size?: number;
  description?: string;
  tags?: GatewayTagCreate[];
}

export interface OPCUADiscoveryRequest {
  endpoint: string;
  namespace_index?: number;
  tag_filter?: string;
}

export interface OPCUANamespace {
  index: number;
  uri: string;
}

export interface OPCUADiscoveredTag {
  tag_name: string;
  display_name: string;
  address: string;
  data_type?: string;
  description?: string;
  readable: boolean;
  writable: boolean;
  current_value?: string;
}

export interface OPCUADiscoveryResponse {
  success: boolean;
  endpoint: string;
  namespaces: OPCUANamespace[];
  tags: OPCUADiscoveredTag[];
  tag_count: number;
  error?: string;
}

export interface OPCUADiscoveryImportRequest {
  gateway_name: string;
  endpoint: string;
  namespace_index?: number;
  tag_filter?: string;
  polling_interval_ms?: number;
  description?: string;
}
