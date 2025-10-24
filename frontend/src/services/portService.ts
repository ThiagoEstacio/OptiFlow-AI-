/**
 * SmartPort API Service
 * All port-related API calls
 */
import apiClient from './api';
import type {
  Vessel,
  VesselCreate,
  VesselUpdate,
  VesselListResponse,
  VesselSearchParams,
  Berth,
  BerthCreate,
  BerthOccupancy,
  BerthCapacity,
  LoadingOperation,
  LoadingOperationCreate,
  LoadingOperationProgress,
  OperationStartRequest,
  OperationPauseRequest,
  OperationCompleteRequest,
  OperationDelayRequest,
  OperationSearchParams,
  PortEquipment,
  EquipmentSearchParams,
  EquipmentPerformance,
  PortKPI,
  PerformanceMetrics,
  CommodityAnalytics,
  TrendData,
  PaginatedResponse,
} from '@/types/port';

const PORT_BASE = '/port';

// ============================================================================
// Vessel Service
// ============================================================================

export const vesselService = {
  /**
   * List vessels with optional filters
   */
  async list(params?: VesselSearchParams): Promise<VesselListResponse> {
    const { data } = await apiClient.get<VesselListResponse>(`${PORT_BASE}/vessels`, {
      params,
    });
    return data;
  },

  /**
   * Get vessel by ID
   */
  async getById(id: string): Promise<Vessel> {
    const { data } = await apiClient.get<Vessel>(`${PORT_BASE}/vessels/${id}`);
    return data;
  },

  /**
   * Get vessel by IMO number
   */
  async getByIMO(imo: string): Promise<Vessel> {
    const { data } = await apiClient.get<Vessel>(`${PORT_BASE}/vessels/search/by-imo/${imo}`);
    return data;
  },

  /**
   * Create new vessel
   */
  async create(vessel: VesselCreate): Promise<Vessel> {
    const { data } = await apiClient.post<Vessel>(`${PORT_BASE}/vessels`, vessel);
    return data;
  },

  /**
   * Update vessel
   */
  async update(id: string, vessel: VesselUpdate): Promise<Vessel> {
    const { data } = await apiClient.put<Vessel>(`${PORT_BASE}/vessels/${id}`, vessel);
    return data;
  },

  /**
   * Update vessel status
   */
  async updateStatus(id: string, status: string): Promise<Vessel> {
    const { data } = await apiClient.patch<Vessel>(`${PORT_BASE}/vessels/${id}/status`, {
      status,
    });
    return data;
  },

  /**
   * Delete vessel
   */
  async delete(id: string): Promise<void> {
    await apiClient.delete(`${PORT_BASE}/vessels/${id}`);
  },

  /**
   * Get vessel operations
   */
  async getOperations(id: string): Promise<LoadingOperation[]> {
    const { data } = await apiClient.get<LoadingOperation[]>(
      `${PORT_BASE}/vessels/${id}/operations`
    );
    return data;
  },
};

// ============================================================================
// Berth Service
// ============================================================================

export const berthService = {
  /**
   * List all berths
   */
  async list(): Promise<Berth[]> {
    const { data } = await apiClient.get<Berth[]>(`${PORT_BASE}/berths`);
    return data;
  },

  /**
   * Get berth by ID
   */
  async getById(id: string): Promise<Berth> {
    const { data } = await apiClient.get<Berth>(`${PORT_BASE}/berths/${id}`);
    return data;
  },

  /**
   * Create new berth
   */
  async create(berth: BerthCreate): Promise<Berth> {
    const { data } = await apiClient.post<Berth>(`${PORT_BASE}/berths`, berth);
    return data;
  },

  /**
   * Get berth status
   */
  async getStatus(id: string): Promise<Berth> {
    const { data } = await apiClient.get<Berth>(`${PORT_BASE}/berths/${id}/status`);
    return data;
  },

  /**
   * Get berth occupancy timeline
   */
  async getOccupancy(id: string, fromDate?: string, toDate?: string): Promise<BerthOccupancy[]> {
    const { data } = await apiClient.get<BerthOccupancy[]>(
      `${PORT_BASE}/berths/${id}/occupancy`,
      {
        params: { from_date: fromDate, to_date: toDate },
      }
    );
    return data;
  },

  /**
   * Get berth capacity info
   */
  async getCapacity(id: string): Promise<BerthCapacity> {
    const { data } = await apiClient.get<BerthCapacity>(`${PORT_BASE}/berths/${id}/capacity`);
    return data;
  },
};

// ============================================================================
// Loading Operation Service
// ============================================================================

export const operationService = {
  /**
   * List operations with filters
   */
  async list(params?: OperationSearchParams): Promise<PaginatedResponse<LoadingOperation>> {
    const { data } = await apiClient.get<PaginatedResponse<LoadingOperation>>(
      `${PORT_BASE}/operations`,
      { params }
    );
    return data;
  },

  /**
   * Get operation by ID
   */
  async getById(id: string): Promise<LoadingOperation> {
    const { data } = await apiClient.get<LoadingOperation>(`${PORT_BASE}/operations/${id}`);
    return data;
  },

  /**
   * Create new operation
   */
  async create(operation: LoadingOperationCreate): Promise<LoadingOperation> {
    const { data } = await apiClient.post<LoadingOperation>(
      `${PORT_BASE}/operations`,
      operation
    );
    return data;
  },

  /**
   * Get operation progress (real-time)
   */
  async getProgress(id: string): Promise<LoadingOperationProgress> {
    const { data } = await apiClient.get<LoadingOperationProgress>(
      `${PORT_BASE}/operations/${id}/progress`
    );
    return data;
  },

  /**
   * Start operation
   */
  async start(id: string, request?: OperationStartRequest): Promise<LoadingOperation> {
    const { data } = await apiClient.post<LoadingOperation>(
      `${PORT_BASE}/operations/${id}/start`,
      request || {}
    );
    return data;
  },

  /**
   * Pause operation
   */
  async pause(id: string, request: OperationPauseRequest): Promise<LoadingOperation> {
    const { data } = await apiClient.post<LoadingOperation>(
      `${PORT_BASE}/operations/${id}/pause`,
      request
    );
    return data;
  },

  /**
   * Resume operation
   */
  async resume(id: string, notes?: string): Promise<LoadingOperation> {
    const { data } = await apiClient.post<LoadingOperation>(
      `${PORT_BASE}/operations/${id}/resume`,
      { notes }
    );
    return data;
  },

  /**
   * Complete operation
   */
  async complete(id: string, request?: OperationCompleteRequest): Promise<LoadingOperation> {
    const { data } = await apiClient.post<LoadingOperation>(
      `${PORT_BASE}/operations/${id}/complete`,
      request || {}
    );
    return data;
  },

  /**
   * Report operation delay
   */
  async reportDelay(id: string, request: OperationDelayRequest): Promise<LoadingOperation> {
    const { data } = await apiClient.post<LoadingOperation>(
      `${PORT_BASE}/operations/${id}/delay`,
      request
    );
    return data;
  },

  /**
   * Delete operation
   */
  async delete(id: string): Promise<void> {
    await apiClient.delete(`${PORT_BASE}/operations/${id}`);
  },
};

// ============================================================================
// Equipment Service
// ============================================================================

export const equipmentService = {
  /**
   * List equipment with filters
   */
  async list(params?: EquipmentSearchParams): Promise<PaginatedResponse<PortEquipment>> {
    const { data } = await apiClient.get<PaginatedResponse<PortEquipment>>(
      `${PORT_BASE}/equipment`,
      { params }
    );
    return data;
  },

  /**
   * Get equipment by ID
   */
  async getById(id: string): Promise<PortEquipment> {
    const { data } = await apiClient.get<PortEquipment>(`${PORT_BASE}/equipment/${id}`);
    return data;
  },

  /**
   * Get equipment performance analytics
   */
  async getPerformance(id: string): Promise<EquipmentPerformance> {
    const { data } = await apiClient.get<EquipmentPerformance>(
      `${PORT_BASE}/analytics/equipment/${id}`
    );
    return data;
  },
};

// ============================================================================
// Analytics Service
// ============================================================================

export const analyticsService = {
  /**
   * Get port KPIs
   */
  async getKPIs(fromDate?: string, toDate?: string): Promise<PortKPI> {
    const { data } = await apiClient.get<PortKPI>(`${PORT_BASE}/analytics/kpis`, {
      params: { from_date: fromDate, to_date: toDate },
    });
    return data;
  },

  /**
   * Get performance metrics
   */
  async getPerformance(
    period: 'day' | 'week' | 'month',
    fromDate?: string,
    toDate?: string
  ): Promise<PerformanceMetrics[]> {
    const { data } = await apiClient.get<PerformanceMetrics[]>(
      `${PORT_BASE}/analytics/performance`,
      {
        params: { period, from_date: fromDate, to_date: toDate },
      }
    );
    return data;
  },

  /**
   * Get commodity breakdown
   */
  async getCommodityBreakdown(fromDate?: string, toDate?: string): Promise<CommodityAnalytics[]> {
    const { data } = await apiClient.get<CommodityAnalytics[]>(
      `${PORT_BASE}/analytics/commodity-breakdown`,
      {
        params: { from_date: fromDate, to_date: toDate },
      }
    );
    return data;
  },

  /**
   * Get trend data
   */
  async getTrends(
    metric: string,
    period: 'hour' | 'day' | 'week',
    fromDate?: string,
    toDate?: string
  ): Promise<TrendData[]> {
    const { data } = await apiClient.get<TrendData[]>(`${PORT_BASE}/analytics/trends`, {
      params: { metric, period, from_date: fromDate, to_date: toDate },
    });
    return data;
  },
};

// ============================================================================
// Export all services
// ============================================================================

export const portAPI = {
  vessels: vesselService,
  berths: berthService,
  operations: operationService,
  equipment: equipmentService,
  analytics: analyticsService,
};

export default portAPI;
