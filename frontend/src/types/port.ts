/**
 * TypeScript types for SmartPort API
 * Matches backend Pydantic schemas
 */

// ============================================================================
// Enums
// ============================================================================

export enum VesselType {
  BULK_CARRIER = 'bulk_carrier',
  CONTAINER = 'container',
  TANKER = 'tanker',
  RO_RO = 'ro_ro',
  GENERAL_CARGO = 'general_cargo',
  LNG = 'lng',
  CRUISE = 'cruise',
  OTHER = 'other',
}

export enum VesselStatus {
  SCHEDULED = 'scheduled',
  APPROACHING = 'approaching',
  ANCHORED = 'anchored',
  BERTHING = 'berthing',
  BERTHED = 'berthed',
  LOADING = 'loading',
  UNLOADING = 'unloading',
  COMPLETED = 'completed',
  DEPARTING = 'departing',
  DEPARTED = 'departed',
  CANCELLED = 'cancelled',
}

export enum BerthType {
  BULK = 'bulk',
  CONTAINER = 'container',
  LIQUID = 'liquid',
  GENERAL = 'general',
  MULTIPURPOSE = 'multipurpose',
}

export enum BerthStatus {
  AVAILABLE = 'available',
  OCCUPIED = 'occupied',
  RESERVED = 'reserved',
  MAINTENANCE = 'maintenance',
  UNAVAILABLE = 'unavailable',
}

export enum OperationStatus {
  PLANNED = 'planned',
  READY = 'ready',
  IN_PROGRESS = 'in_progress',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

export enum OperationType {
  LOADING = 'loading',
  UNLOADING = 'unloading',
}

export enum EquipmentType {
  CONVEYOR = 'conveyor',
  ELEVATOR = 'elevator',
  SHIPLOADER = 'shiploader',
  UNLOADER = 'unloader',
  CRANE = 'crane',
  WEIGHING_SCALE = 'weighing_scale',
  STACKER = 'stacker',
  RECLAIMER = 'reclaimer',
  OTHER = 'other',
}

export enum EquipmentStatus {
  OPERATING = 'operating',
  IDLE = 'idle',
  MAINTENANCE = 'maintenance',
  FAULT = 'fault',
  OFFLINE = 'offline',
}

// ============================================================================
// Base Models
// ============================================================================

export interface BaseModel {
  id: string;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// Vessel Types
// ============================================================================

export interface VesselSpecifications {
  length?: number;
  beam?: number;
  draft?: number;
  dwt?: number;
  gt?: number;
  max_draft?: number;
}

export interface Vessel extends BaseModel {
  site_id: string;
  imo_number: string;
  name: string;
  vessel_type: VesselType;
  flag?: string;
  status: VesselStatus;
  current_location?: string;
  current_berth_id?: string;
  specifications?: VesselSpecifications;
  eta?: string;
  ata?: string;
  etb?: string;
  atb?: string;
  etc?: string;
  atc?: string;
  etd?: string;
  atd?: string;
  agent?: string;
  notes?: string;
  metadata?: Record<string, any>;
}

export interface VesselCreate {
  imo_number: string;
  name: string;
  vessel_type: VesselType;
  flag?: string;
  status?: VesselStatus;
  current_location?: string;
  specifications?: VesselSpecifications;
  eta?: string;
  etb?: string;
  etc?: string;
  etd?: string;
  agent?: string;
  notes?: string;
}

export interface VesselUpdate {
  name?: string;
  flag?: string;
  status?: VesselStatus;
  current_location?: string;
  current_berth_id?: string;
  specifications?: VesselSpecifications;
  eta?: string;
  ata?: string;
  etb?: string;
  atb?: string;
  etc?: string;
  atc?: string;
  etd?: string;
  atd?: string;
  agent?: string;
  notes?: string;
}

export interface VesselListResponse {
  total: number;
  items: Vessel[];
}

// ============================================================================
// Berth Types
// ============================================================================

export interface Berth extends BaseModel {
  site_id: string;
  code: string;
  name: string;
  berth_type: BerthType;
  status: BerthStatus;
  max_vessel_length?: number;
  max_vessel_draft?: number;
  capacity_tons_per_hour?: number;
  number_of_conveyors?: number;
  number_of_shiploaders?: number;
  number_of_unloaders?: number;
  location?: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
  current_vessel_id?: string;
  notes?: string;
  metadata?: Record<string, any>;
}

export interface BerthCreate {
  code: string;
  name: string;
  berth_type: BerthType;
  status?: BerthStatus;
  max_vessel_length?: number;
  max_vessel_draft?: number;
  capacity_tons_per_hour?: number;
  number_of_conveyors?: number;
  number_of_shiploaders?: number;
  number_of_unloaders?: number;
  location?: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
  notes?: string;
}

export interface BerthOccupancy {
  berth_id: string;
  vessel_id?: string;
  vessel_name?: string;
  operation_id?: string;
  operation_number?: string;
  start_time: string;
  end_time?: string;
  status: BerthStatus;
}

export interface BerthCapacity {
  berth_id: string;
  capacity_tons_per_hour: number;
  current_utilization_percent?: number;
  available_capacity?: number;
  equipment_count: {
    conveyors: number;
    shiploaders: number;
    unloaders: number;
  };
}

// ============================================================================
// Loading Operation Types
// ============================================================================

export interface Cargo {
  id: string;
  commodity: string;
  grade?: string;
  quantity_tons: number;
  unit_price?: number;
  origin?: string;
  destination?: string;
  quality_specs?: Record<string, any>;
}

export interface OperationEvent {
  id: string;
  timestamp: string;
  event_type: string;
  description: string;
  user_id?: string;
  metadata?: Record<string, any>;
}

export interface LoadingOperation extends BaseModel {
  site_id: string;
  operation_number: string;
  operation_type: OperationType;
  status: OperationStatus;
  vessel_id: string;
  berth_id: string;
  planned_start_time: string;
  actual_start_time?: string;
  planned_end_time: string;
  actual_end_time?: string;
  planned_rate?: number;
  actual_rate?: number;
  current_rate?: number;
  total_planned_quantity?: number;
  total_actual_quantity?: number;
  efficiency?: number;
  downtime_hours?: number;
  working_hours?: number;
  is_delayed: boolean;
  delay_reason?: string;
  delay_minutes?: number;
  weather_conditions?: Record<string, any>;
  notes?: string;
  metadata?: Record<string, any>;
  cargos?: Cargo[];
  events?: OperationEvent[];
}

export interface LoadingOperationCreate {
  operation_number: string;
  operation_type: OperationType;
  vessel_id: string;
  berth_id: string;
  planned_start_time: string;
  planned_end_time: string;
  planned_rate?: number;
  total_planned_quantity?: number;
  cargos?: Omit<Cargo, 'id'>[];
  notes?: string;
}

export interface LoadingOperationProgress {
  operation_id: string;
  operation_number: string;
  status: OperationStatus;
  progress_percent: number;
  total_planned_quantity: number;
  total_actual_quantity: number;
  current_rate?: number;
  planned_rate?: number;
  actual_rate?: number;
  efficiency?: number;
  elapsed_hours?: number;
  estimated_completion_time?: string;
  is_delayed: boolean;
  delay_minutes?: number;
  working_hours?: number;
  downtime_hours?: number;
}

export interface OperationStartRequest {
  actual_start_time?: string;
  notes?: string;
}

export interface OperationPauseRequest {
  reason: string;
  notes?: string;
}

export interface OperationCompleteRequest {
  actual_end_time?: string;
  total_actual_quantity?: number;
  notes?: string;
}

export interface OperationDelayRequest {
  delay_reason: string;
  delay_minutes: number;
  notes?: string;
}

// ============================================================================
// Equipment Types
// ============================================================================

export interface MaintenanceRecord {
  id: string;
  maintenance_type: 'preventive' | 'corrective' | 'predictive';
  scheduled_date?: string;
  completed_date?: string;
  description: string;
  cost?: number;
  downtime_hours?: number;
  technician?: string;
  notes?: string;
}

export interface PortEquipment extends BaseModel {
  site_id: string;
  code: string;
  name: string;
  equipment_type: EquipmentType;
  status: EquipmentStatus;
  berth_id?: string;
  manufacturer?: string;
  model?: string;
  year_manufactured?: number;
  capacity?: number;
  health_score?: number;
  failure_probability?: number;
  last_maintenance_date?: string;
  next_maintenance_date?: string;
  operating_hours?: number;
  location?: string;
  specifications?: Record<string, any>;
  notes?: string;
  metadata?: Record<string, any>;
  maintenance_records?: MaintenanceRecord[];
}

// ============================================================================
// Analytics Types
// ============================================================================

export interface PortKPI {
  total_throughput_tons: number;
  total_operations: number;
  operations_in_progress: number;
  operations_completed: number;
  average_loading_rate: number;
  average_efficiency: number;
  total_vessels_processed: number;
  vessels_at_berth: number;
  vessels_at_anchor: number;
  berths_occupied: number;
  berths_available: number;
  average_turnaround_time_hours?: number;
  equipment_availability_percent?: number;
  period_start: string;
  period_end: string;
}

export interface PerformanceMetrics {
  period: string;
  throughput_tons: number;
  operations_count: number;
  average_efficiency: number;
  average_rate: number;
  downtime_hours: number;
  working_hours: number;
  vessel_count: number;
}

export interface EquipmentPerformance {
  equipment_id: string;
  equipment_code: string;
  equipment_name: string;
  status: EquipmentStatus;
  health_score: number;
  failure_probability: number;
  operating_hours: number;
  total_downtime_hours: number;
  availability_percent: number;
  maintenance_count: number;
  last_maintenance_date?: string;
  next_maintenance_date?: string;
  estimated_failure_date?: string;
  maintenance_cost_total?: number;
  predictive_insights?: {
    risk_level: 'low' | 'medium' | 'high' | 'critical';
    recommended_action: string;
    estimated_cost_preventive?: number;
    estimated_cost_corrective?: number;
    roi_preventive?: number;
  };
}

export interface CommodityAnalytics {
  commodity: string;
  total_quantity_tons: number;
  operations_count: number;
  average_rate: number;
  percentage_of_total: number;
}

export interface TrendData {
  timestamp: string;
  throughput?: number;
  efficiency?: number;
  loading_rate?: number;
  energy_consumption?: number;
  equipment_health?: number;
  [key: string]: string | number | undefined;
}

// ============================================================================
// API Response Wrappers
// ============================================================================

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  total: number;
  items: T[];
  page?: number;
  page_size?: number;
  has_more?: boolean;
}

// ============================================================================
// Filter/Search Parameters
// ============================================================================

export interface VesselSearchParams {
  status?: VesselStatus;
  vessel_type?: VesselType;
  current_berth_id?: string;
  from_date?: string;
  to_date?: string;
  search?: string;
  skip?: number;
  limit?: number;
}

export interface OperationSearchParams {
  status?: OperationStatus;
  operation_type?: OperationType;
  vessel_id?: string;
  berth_id?: string;
  from_date?: string;
  to_date?: string;
  is_delayed?: boolean;
  skip?: number;
  limit?: number;
}

export interface EquipmentSearchParams {
  status?: EquipmentStatus;
  equipment_type?: EquipmentType;
  berth_id?: string;
  min_health_score?: number;
  max_failure_probability?: number;
  skip?: number;
  limit?: number;
}
