export enum TagDataType {
  BOOLEAN = "boolean",
  INTEGER = "integer",
  FLOAT = "float",
  STRING = "string",
  DOUBLE = "double",
}

export enum TagCategory {
  PROCESS = "process",
  ENERGY = "energy",
  QUALITY = "quality",
  PRODUCTION = "production",
  MAINTENANCE = "maintenance",
  ALARM = "alarm",
  SETPOINT = "setpoint",
  STATUS = "status",
}

export interface Tag {
  id: string;
  device_id: string;
  name: string;
  description?: string;
  address: string;
  data_type: TagDataType;
  unit?: string;
  category: TagCategory;
  is_active: boolean;
  min_value?: number;
  max_value?: number;
  engineering_min?: number;
  engineering_max?: number;
  scale: number;
  offset: number;
  scan_rate_ms: number;
  deadband?: number;
  enable_quality_check: boolean;
  last_value?: string;
  last_quality?: string;
  last_timestamp?: string;
  data_points_count: number;
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface TagWithDevice extends Tag {
  device_name: string;
  device_protocol: string;
  site_id: string;
}

export interface TagValue {
  tag_id: string;
  value: any;
  quality: string;
  timestamp: string;
}
