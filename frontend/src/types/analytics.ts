/**
 * Analytics Types
 *
 * Centralized type definitions for analytics queries and results
 */

export interface AnalyticsQuery {
  tags: string[];
  start_time: string;
  end_time: string;
  aggregation?: 'avg' | 'min' | 'max' | 'sum' | 'count';
  interval?: string;
  filters?: Record<string, any>;
}

export interface AggregationResult {
  tag_id: string;
  timestamp: string;
  value: number;
  function: string;
  field: string;
  values: Array<{
    tag_id?: string;
    timestamp: string;
    value: number;
  }>;
}

export interface AnalyticsResponse {
  query: AnalyticsQuery;
  aggregations: AggregationResult[];
  count: number;
}
