/**
 * Extended Tags Types - PI Asset Framework style
 *
 * Types for tags with advanced features:
 * - Calculated/logical tags
 * - Historical archiving configuration
 * - Formulas and expressions
 * - Asset hierarchy integration
 */

export enum TagType {
  PHYSICAL = 'physical',
  CALCULATED = 'calculated',
  LOGICAL = 'logical',
  AGGREGATED = 'aggregated'
}

export enum ArchiveType {
  ON_CHANGE = 'on_change',
  PERIODIC = 'periodic',
  COMPRESSED = 'compressed'
}

export interface AlarmConfig {
  high_high?: number;
  high?: number;
  low?: number;
  low_low?: number;
  enabled?: boolean;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  message?: string;
}

export interface GatewayTagExtended {
  id: number;
  gateway_id?: number;
  tag_name: string;
  enabled: boolean;

  // Hierarchy
  asset_id?: string; // UUID
  tag_group?: string;

  // Tag type
  tag_type: TagType;

  // Physical tag fields
  address_config?: Record<string, any>;
  data_type: string;
  scale_factor: number;
  tag_offset: number;

  // Calculated/logical tag fields
  formula?: string;
  formula_tags?: any[]; // List of tag IDs
  condition?: string;

  // Units and limits
  unit?: string;
  min_value?: number;
  max_value?: number;

  // Historical archiving (PI-style)
  archive_enabled: boolean;
  archive_type: ArchiveType;
  archive_deadband?: number;
  archive_interval_seconds?: number;
  compression_deviation?: number;

  // Quality and alarms
  quality_enabled: boolean;
  alarm_enabled: boolean;
  alarm_config?: AlarmConfig;

  // Metadata
  description?: string;
  category?: string;
  properties?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface GatewayTagExtendedCreate {
  gateway_id?: number;
  tag_name: string;
  enabled?: boolean;
  asset_id?: string;
  tag_group?: string;
  tag_type?: TagType;
  address_config?: Record<string, any>;
  data_type?: string;
  scale_factor?: number;
  tag_offset?: number;
  formula?: string;
  formula_tags?: any[];
  condition?: string;
  unit?: string;
  min_value?: number;
  max_value?: number;
  archive_enabled?: boolean;
  archive_type?: ArchiveType;
  archive_deadband?: number;
  archive_interval_seconds?: number;
  compression_deviation?: number;
  quality_enabled?: boolean;
  alarm_enabled?: boolean;
  alarm_config?: AlarmConfig;
  description?: string;
  category?: string;
  properties?: Record<string, any>;
}

export interface GatewayTagExtendedUpdate {
  gateway_id?: number;
  tag_name?: string;
  enabled?: boolean;
  asset_id?: string;
  tag_group?: string;
  tag_type?: TagType;
  address_config?: Record<string, any>;
  data_type?: string;
  scale_factor?: number;
  tag_offset?: number;
  formula?: string;
  formula_tags?: any[];
  condition?: string;
  unit?: string;
  min_value?: number;
  max_value?: number;
  archive_enabled?: boolean;
  archive_type?: ArchiveType;
  archive_deadband?: number;
  archive_interval_seconds?: number;
  compression_deviation?: number;
  quality_enabled?: boolean;
  alarm_enabled?: boolean;
  alarm_config?: AlarmConfig;
  description?: string;
  category?: string;
  properties?: Record<string, any>;
}

export interface TagFormula {
  id: number;
  name: string;
  description?: string;
  formula_type: 'expression' | 'script' | 'sql' | 'aggregation';
  expression: string;
  input_tags?: any[];
  output_unit?: string;
  output_type?: string;
  execution_interval_seconds?: number;
  is_active: boolean;
  category?: string;
  tags_metadata?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface TagFormulaCreate {
  name: string;
  description?: string;
  formula_type: 'expression' | 'script' | 'sql' | 'aggregation';
  expression: string;
  input_tags?: any[];
  output_unit?: string;
  output_type?: string;
  execution_interval_seconds?: number;
  is_active?: boolean;
  category?: string;
  tags_metadata?: Record<string, any>;
}

export interface TagFormulaUpdate {
  name?: string;
  description?: string;
  formula_type?: 'expression' | 'script' | 'sql' | 'aggregation';
  expression?: string;
  input_tags?: any[];
  output_unit?: string;
  output_type?: string;
  execution_interval_seconds?: number;
  is_active?: boolean;
  category?: string;
  tags_metadata?: Record<string, any>;
}

export interface BulkTagOperation {
  tag_ids: number[];
  operation: 'enable' | 'disable' | 'delete' | 'move';
  target_asset_id?: string; // UUID
}

export interface TagImportItem {
  tag_name: string;
  asset_path: string;
  tag_type?: TagType;
  address_config: Record<string, any>;
  data_type?: string;
  unit?: string;
  description?: string;
  archive_enabled?: boolean;
}

export interface TagImportRequest {
  gateway_id: number;
  tags: TagImportItem[];
  overwrite_existing?: boolean;
}

// Filter options for listing tags
export interface ExtendedTagFilters {
  gateway_id?: number;
  asset_id?: string;
  tag_type?: TagType;
  enabled_only?: boolean;
  search?: string;
  skip?: number;
  limit?: number;
}

// Filter options for formulas
export interface FormulaFilters {
  formula_type?: string;
  is_active?: boolean;
  category?: string;
  skip?: number;
  limit?: number;
}
