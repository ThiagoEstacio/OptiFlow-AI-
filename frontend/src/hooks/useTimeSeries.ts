/**
 * Time Series Data Hook
 */
import { useState, useCallback } from 'react';
import api from '../api/client';
import { API_ENDPOINTS } from '../api/config';
import type { TimeSeriesPoint, TimeSeriesQuery } from '../types';

export const useTimeSeries = () => {
  const [data, setData] = useState<TimeSeriesPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Query single tag
  const querySingleTag = useCallback(
    async (
      tagId: string,
      startTime: Date,
      endTime?: Date,
      aggregation?: string,
      interval?: string
    ) => {
      setLoading(true);
      setError(null);

      try {
        const params = {
          start_time: startTime.toISOString(),
          end_time: endTime?.toISOString(),
          aggregation,
          interval,
        };

        const response = await api.get(`${API_ENDPOINTS.TIMESERIES}/tags/${tagId}`, {
          params,
        });
        setData(response.data.data || []);
        return response.data;
      } catch (err: any) {
        setError(err.message || 'Failed to fetch time series data');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // Query multiple tags
  const queryMultipleTags = useCallback(async (query: TimeSeriesQuery) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post(API_ENDPOINTS.TIMESERIES_QUERY, query);
      return response.data;
    } catch (err: any) {
      setError(err.message || 'Failed to fetch time series data');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Write data points
  const writePoints = useCallback(async (points: TimeSeriesPoint[]) => {
    try {
      const response = await api.post(`${API_ENDPOINTS.TIMESERIES}/batch`, points);
      return response.data;
    } catch (err: any) {
      throw new Error(err.message || 'Failed to write time series data');
    }
  }, []);

  return {
    data,
    loading,
    error,
    querySingleTag,
    queryMultipleTags,
    writePoints,
  };
};
