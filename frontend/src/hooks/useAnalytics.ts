/**
 * Analytics Hooks
 */
import { useState, useCallback } from 'react';
import api from '../api/client';
import { API_ENDPOINTS } from '../api/config';
import type { Statistics, Anomaly, Trend, Forecast, Correlation } from '../types';

// Get Statistics
export const useStatistics = () => {
  const [data, setData] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatistics = useCallback(
    async (tagIds: string[], startTime: Date, endTime?: Date) => {
      setLoading(true);
      setError(null);

      try {
        const params = {
          tag_ids: tagIds,
          start_time: startTime.toISOString(),
          end_time: endTime?.toISOString(),
        };

        const response = await api.get(API_ENDPOINTS.ANALYTICS_STATS, { params });
        setData(response.data);
        return response.data;
      } catch (err: any) {
        setError(err.message || 'Failed to fetch statistics');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { data, loading, error, fetchStatistics };
};

// Detect Anomalies
export const useAnomalies = () => {
  const [data, setData] = useState<Anomaly[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const detectAnomalies = useCallback(
    async (
      tagId: string,
      startTime: Date,
      endTime?: Date,
      method: 'zscore' | 'iqr' | 'mad' = 'zscore',
      threshold: number = 3.0
    ) => {
      setLoading(true);
      setError(null);

      try {
        const params = {
          tag_id: tagId,
          start_time: startTime.toISOString(),
          end_time: endTime?.toISOString(),
          method,
          threshold,
        };

        const response = await api.get(API_ENDPOINTS.ANALYTICS_ANOMALIES, { params });
        setData(response.data.anomalies || []);
        return response.data;
      } catch (err: any) {
        setError(err.message || 'Failed to detect anomalies');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { data, loading, error, detectAnomalies };
};

// Calculate Trends
export const useTrends = () => {
  const [data, setData] = useState<Trend | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const calculateTrends = useCallback(
    async (tagId: string, startTime: Date, endTime?: Date, window: number = 10) => {
      setLoading(true);
      setError(null);

      try {
        const params = {
          tag_id: tagId,
          start_time: startTime.toISOString(),
          end_time: endTime?.toISOString(),
          window,
        };

        const response = await api.get(API_ENDPOINTS.ANALYTICS_TRENDS, { params });
        setData(response.data.trends);
        return response.data;
      } catch (err: any) {
        setError(err.message || 'Failed to calculate trends');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { data, loading, error, calculateTrends };
};

// Generate Forecast
export const useForecast = () => {
  const [data, setData] = useState<Forecast[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateForecast = useCallback(
    async (tagId: string, startTime: Date, endTime?: Date, periods: number = 10) => {
      setLoading(true);
      setError(null);

      try {
        const params = {
          tag_id: tagId,
          start_time: startTime.toISOString(),
          end_time: endTime?.toISOString(),
          periods,
        };

        const response = await api.get(API_ENDPOINTS.ANALYTICS_FORECAST, { params });
        setData(response.data.forecasts || []);
        return response.data;
      } catch (err: any) {
        setError(err.message || 'Failed to generate forecast');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { data, loading, error, generateForecast };
};

// Calculate Correlation
export const useCorrelation = () => {
  const [data, setData] = useState<Correlation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const calculateCorrelation = useCallback(
    async (tagId1: string, tagId2: string, startTime: Date, endTime?: Date) => {
      setLoading(true);
      setError(null);

      try {
        const params = {
          tag_id1: tagId1,
          tag_id2: tagId2,
          start_time: startTime.toISOString(),
          end_time: endTime?.toISOString(),
        };

        const response = await api.get(API_ENDPOINTS.ANALYTICS_CORRELATION, { params });
        setData(response.data.correlation);
        return response.data;
      } catch (err: any) {
        setError(err.message || 'Failed to calculate correlation');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { data, loading, error, calculateCorrelation };
};
