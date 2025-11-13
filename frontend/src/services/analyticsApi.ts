/**
 * Analytics API Service
 *
 * Handles all API calls to the analytics endpoints
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface QueryFilter {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'lt' | 'gte' | 'lte' | 'in' | 'between';
  value: any;
}

export interface QueryAggregation {
  function:
    | 'mean'
    | 'median'
    | 'mode'
    | 'min'
    | 'max'
    | 'sum'
    | 'count'
    | 'stddev'
    | 'variance'
    | 'percentile'
    | 'correlation'
    | 'moving_average'
    | 'cumulative_sum'
    | 'rate_of_change'
    | 'outlier_detection';
  field: string;
  window?: string;
  params?: Record<string, any>;
}

// Local interface for API usage (compatible with backend)
export interface AnalyticsQuery {
  tags: string[];
  start: string;
  end: string;
  filters?: QueryFilter[];
  aggregations: QueryAggregation[];
  group_by?: string[];
  limit?: number;
  include_raw_data?: boolean;
}

export interface AggregationResult {
  function: string;
  field: string;
  window?: string;
  values: Array<{
    timestamp: string;
    value: number;
    tag_id?: string;
  }>;
  summary?: {
    min?: number;
    max?: number;
    mean?: number;
    count?: number;
  };
}

export interface QueryResult {
  query_id: string;
  executed_at: string;
  execution_time_ms: number;
  tags: string[];
  aggregations: AggregationResult[];
  raw_data?: Array<{
    timestamp: string;
    tag_id: string;
    value: number;
    quality: string;
  }>;
  metadata: {
    total_records: number;
    time_range: {
      start: string;
      end: string;
    };
  };
}

export interface AnalyticsQueryResponse {
  success: boolean;
  message?: string;
  data?: QueryResult;
  error?: string;
}

export interface AggregationFunction {
  name: string;
  description: string;
  category: string;
  parameters?: Array<{
    name: string;
    type: string;
    required: boolean;
    description: string;
    default?: any;
  }>;
  example: string;
}

export interface QueryExample {
  name: string;
  description: string;
  use_case: string;
  query: AnalyticsQuery;
}

/**
 * Analytics API Client
 */
class AnalyticsApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/api/v1/analytics`;
  }

  /**
   * Get auth token from localStorage
   */
  private getAuthToken(): string | null {
    return localStorage.getItem('token');
  }

  /**
   * Get axios config with auth header
   */
  private getConfig() {
    const token = this.getAuthToken();
    return {
      headers: token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {},
    };
  }

  /**
   * Execute an analytics query
   */
  async executeQuery(query: AnalyticsQuery): Promise<QueryResult> {
    try {
      const response = await axios.post<AnalyticsQueryResponse>(
        `${this.baseUrl}/query`,
        query,
        this.getConfig()
      );

      if (!response.data.success || !response.data.data) {
        throw new Error(response.data.error || 'Query execution failed');
      }

      return response.data.data;
    } catch (error: any) {
      console.error('Analytics query error:', error);
      throw new Error(
        error.response?.data?.error || error.message || 'Failed to execute query'
      );
    }
  }

  /**
   * Get list of available aggregation functions
   */
  async getAvailableFunctions(): Promise<AggregationFunction[]> {
    try {
      const response = await axios.get<{ functions: AggregationFunction[] }>(
        `${this.baseUrl}/functions`,
        this.getConfig()
      );
      return response.data.functions;
    } catch (error: any) {
      console.error('Failed to fetch functions:', error);
      throw new Error('Failed to fetch available functions');
    }
  }

  /**
   * Get example queries
   */
  async getQueryExamples(): Promise<QueryExample[]> {
    try {
      const response = await axios.get<{ examples: QueryExample[] }>(
        `${this.baseUrl}/examples`,
        this.getConfig()
      );
      return response.data.examples;
    } catch (error: any) {
      console.error('Failed to fetch examples:', error);
      throw new Error('Failed to fetch query examples');
    }
  }

  /**
   * Save query to backend (TODO: implement endpoint)
   */
  async saveQuery(name: string, query: AnalyticsQuery): Promise<void> {
    // TODO: Implement when backend endpoint is ready
    // For now, save to localStorage
    const savedQueries = this.getSavedQueries();
    savedQueries[name] = {
      name,
      query,
      created_at: new Date().toISOString(),
    };
    localStorage.setItem('saved_analytics_queries', JSON.stringify(savedQueries));
  }

  /**
   * Get saved queries from localStorage
   */
  getSavedQueries(): Record<
    string,
    { name: string; query: AnalyticsQuery; created_at: string }
  > {
    const saved = localStorage.getItem('saved_analytics_queries');
    return saved ? JSON.parse(saved) : {};
  }

  /**
   * Delete saved query
   */
  deleteSavedQuery(name: string): void {
    const savedQueries = this.getSavedQueries();
    delete savedQueries[name];
    localStorage.setItem('saved_analytics_queries', JSON.stringify(savedQueries));
  }

  /**
   * Load query by name
   */
  loadQuery(name: string): AnalyticsQuery | null {
    const savedQueries = this.getSavedQueries();
    return savedQueries[name]?.query || null;
  }
}

// Export singleton instance
export const analyticsApi = new AnalyticsApiClient();

export default analyticsApi;
