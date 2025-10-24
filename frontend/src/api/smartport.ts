/**
 * SmartPort API Client
 *
 * API functions for SmartPort berths, vessels, and operations
 */
import { api } from './client';

// ============================================================================
// Types
// ============================================================================

export enum BerthType {
  CONTAINER = 'container',
  BULK = 'bulk',
  GENERAL_CARGO = 'general_cargo',
  RO_RO = 'ro_ro',
  TANKER = 'tanker',
  CRUISE = 'cruise',
}

export enum BerthStatus {
  AVAILABLE = 'available',
  OCCUPIED = 'occupied',
  RESERVED = 'reserved',
  MAINTENANCE = 'maintenance',
  UNAVAILABLE = 'unavailable',
}

export enum VesselType {
  CONTAINER_SHIP = 'container_ship',
  BULK_CARRIER = 'bulk_carrier',
  TANKER = 'tanker',
  GENERAL_CARGO = 'general_cargo',
  RO_RO = 'ro_ro',
  CRUISE_SHIP = 'cruise_ship',
  FERRY = 'ferry',
  TUGBOAT = 'tugboat',
  OTHER = 'other',
}

export enum VesselStatus {
  APPROACHING = 'approaching',
  ANCHORED = 'anchored',
  BERTHED = 'berthed',
  LOADING = 'loading',
  UNLOADING = 'unloading',
  DEPARTING = 'departing',
  DEPARTED = 'departed',
}

export enum OperationType {
  LOADING = 'loading',
  UNLOADING = 'unloading',
  BUNKERING = 'bunkering',
  MAINTENANCE = 'maintenance',
  INSPECTION = 'inspection',
  PASSENGER_OPERATION = 'passenger_operation',
}

export enum OperationStatus {
  SCHEDULED = 'scheduled',
  IN_PROGRESS = 'in_progress',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  DELAYED = 'delayed',
}

export interface Berth {
  id: string;
  name: string;
  code: string;
  berth_type: BerthType;
  status: BerthStatus;
  max_loa: number;
  max_beam: number;
  max_draft: number;
  max_displacement?: number;
  max_crane_capacity?: number;
  number_of_cranes: number;
  has_shore_power: boolean;
  has_fresh_water: boolean;
  has_bunker_facility: boolean;
  latitude: number;
  longitude: number;
  current_vessel_id?: string;
  occupation_start?: string;
  estimated_departure?: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Vessel {
  id: string;
  name: string;
  imo: string;
  mmsi?: string;
  call_sign?: string;
  flag?: string;
  vessel_type: VesselType;
  status: VesselStatus;
  loa: number;
  beam: number;
  draft: number;
  max_draft?: number;
  gross_tonnage?: number;
  deadweight_tonnage?: number;
  capacity_teu?: number;
  capacity_passengers?: number;
  capacity_vehicles?: number;
  capacity_cubic_meters?: number;
  eta?: string;
  ata?: string;
  etd?: string;
  atd?: string;
  last_latitude?: number;
  last_longitude?: number;
  last_position_update?: string;
  heading?: number;
  speed_knots?: number;
  origin_port?: string;
  destination_port?: string;
  voyage_number?: string;
  owner?: string;
  operator?: string;
  agent?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PortOperation {
  id: string;
  vessel_id: string;
  berth_id: string;
  operation_type: OperationType;
  status: OperationStatus;
  cargo_type?: string;
  containers_planned?: number;
  containers_completed: number;
  tonnage_planned?: number;
  tonnage_completed: number;
  cubic_meters_planned?: number;
  cubic_meters_completed: number;
  scheduled_start: string;
  actual_start?: string;
  estimated_end: string;
  actual_end?: string;
  cranes_assigned: number;
  workforce_assigned: number;
  productivity_rate?: number;
  downtime_hours: number;
  efficiency_percentage?: number;
  estimated_cost?: number;
  actual_cost?: number;
  currency: string;
  priority: number;
  weather_delay: boolean;
  equipment_delay: boolean;
  labor_delay: boolean;
  cargo_description?: string;
  special_requirements?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface PortKPIs {
  total_berths: number;
  available_berths: number;
  occupied_berths: number;
  berth_occupancy_rate: number;
  total_vessels: number;
  berthed_vessels: number;
  approaching_vessels: number;
  active_operations: number;
  completed_operations_today: number;
  containers_handled_today: number;
  average_berthing_time_hours: number;
  operational_efficiency: number;
}

// ============================================================================
// Berths API
// ============================================================================

export const berthsApi = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    berth_type?: BerthType;
    status?: BerthStatus;
    is_active?: boolean;
  }) => {
    const response = await api.get<Berth[]>('/smartport/berths', { params });
    return response.data;
  },

  listAvailable: async (params?: {
    berth_type?: BerthType;
    min_loa?: number;
    min_beam?: number;
    min_draft?: number;
  }) => {
    const response = await api.get<Berth[]>('/smartport/berths/available', { params });
    return response.data;
  },

  get: async (berthId: string) => {
    const response = await api.get<Berth>(`/smartport/berths/${berthId}`);
    return response.data;
  },

  create: async (data: Partial<Berth>) => {
    const response = await api.post<Berth>('/smartport/berths', data);
    return response.data;
  },

  update: async (berthId: string, data: Partial<Berth>) => {
    const response = await api.put<Berth>(`/smartport/berths/${berthId}`, data);
    return response.data;
  },

  delete: async (berthId: string) => {
    await api.delete(`/smartport/berths/${berthId}`);
  },

  getOccupancy: async (berthId: string) => {
    const response = await api.get(`/smartport/berths/${berthId}/occupancy`);
    return response.data;
  },

  getSummary: async () => {
    const response = await api.get('/smartport/berths/stats/summary');
    return response.data;
  },
};

// ============================================================================
// Vessels API
// ============================================================================

export const vesselsApi = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    vessel_type?: VesselType;
    status?: VesselStatus;
    search?: string;
  }) => {
    const response = await api.get<Vessel[]>('/smartport/vessels', { params });
    return response.data;
  },

  listInPort: async () => {
    const response = await api.get<Vessel[]>('/smartport/vessels/in-port');
    return response.data;
  },

  listExpectedArrivals: async (hours: number = 24) => {
    const response = await api.get<Vessel[]>('/smartport/vessels/expected-arrivals', {
      params: { hours },
    });
    return response.data;
  },

  get: async (vesselId: string) => {
    const response = await api.get<Vessel>(`/smartport/vessels/${vesselId}`);
    return response.data;
  },

  getByImo: async (imo: string) => {
    const response = await api.get<Vessel>(`/smartport/vessels/imo/${imo}`);
    return response.data;
  },

  create: async (data: Partial<Vessel>) => {
    const response = await api.post<Vessel>('/smartport/vessels', data);
    return response.data;
  },

  update: async (vesselId: string, data: Partial<Vessel>) => {
    const response = await api.put<Vessel>(`/smartport/vessels/${vesselId}`, data);
    return response.data;
  },

  updatePosition: async (
    vesselId: string,
    data: { latitude: number; longitude: number; heading?: number; speed_knots?: number }
  ) => {
    const response = await api.put<Vessel>(`/smartport/vessels/${vesselId}/position`, data);
    return response.data;
  },

  delete: async (vesselId: string) => {
    await api.delete(`/smartport/vessels/${vesselId}`);
  },

  getSummary: async () => {
    const response = await api.get('/smartport/vessels/stats/summary');
    return response.data;
  },
};

// ============================================================================
// Operations API
// ============================================================================

export const operationsApi = {
  list: async (params?: {
    skip?: number;
    limit?: number;
    operation_type?: OperationType;
    status?: OperationStatus;
    vessel_id?: string;
    berth_id?: string;
  }) => {
    const response = await api.get<PortOperation[]>('/smartport/operations', { params });
    return response.data;
  },

  listActive: async () => {
    const response = await api.get<PortOperation[]>('/smartport/operations/active');
    return response.data;
  },

  listToday: async () => {
    const response = await api.get<PortOperation[]>('/smartport/operations/today');
    return response.data;
  },

  listDelayed: async () => {
    const response = await api.get<PortOperation[]>('/smartport/operations/delayed');
    return response.data;
  },

  get: async (operationId: string) => {
    const response = await api.get<PortOperation>(`/smartport/operations/${operationId}`);
    return response.data;
  },

  create: async (data: Partial<PortOperation>) => {
    const response = await api.post<PortOperation>('/smartport/operations', data);
    return response.data;
  },

  update: async (operationId: string, data: Partial<PortOperation>) => {
    const response = await api.put<PortOperation>(`/smartport/operations/${operationId}`, data);
    return response.data;
  },

  updateProgress: async (
    operationId: string,
    data: {
      containers_completed?: number;
      tonnage_completed?: number;
      cubic_meters_completed?: number;
    }
  ) => {
    const response = await api.put<PortOperation>(
      `/smartport/operations/${operationId}/progress`,
      data
    );
    return response.data;
  },

  start: async (operationId: string) => {
    const response = await api.post<PortOperation>(`/smartport/operations/${operationId}/start`);
    return response.data;
  },

  complete: async (operationId: string) => {
    const response = await api.post<PortOperation>(`/smartport/operations/${operationId}/complete`);
    return response.data;
  },

  delete: async (operationId: string) => {
    await api.delete(`/smartport/operations/${operationId}`);
  },

  getPerformance: async (days: number = 30) => {
    const response = await api.get('/smartport/operations/stats/performance', {
      params: { days },
    });
    return response.data;
  },
};

// ============================================================================
// Dashboard API
// ============================================================================

export const dashboardApi = {
  getKPIs: async () => {
    const response = await api.get<PortKPIs>('/smartport/dashboard/kpis');
    return response.data;
  },

  getTimeline: async (hours: number = 24) => {
    const response = await api.get('/smartport/dashboard/timeline', {
      params: { hours },
    });
    return response.data;
  },

  getAlerts: async () => {
    const response = await api.get('/smartport/dashboard/alerts');
    return response.data;
  },
};
