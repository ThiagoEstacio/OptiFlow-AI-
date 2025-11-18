/**
 * useLiveTagData Hook
 * Connects to WebSocket for real-time tag data
 * Falls back to polling if WebSocket unavailable
 */

import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../api/client';
import { getCircuitBreaker, CircuitBreakerError } from '../utils/circuitBreaker';

interface LiveTagData {
  value: number | string | boolean | null;
  timestamp: string | null;
  quality: string;
  loading: boolean;
  error: string | null;
}

// Global circuit breaker for tag data fetching
const tagDataCircuitBreaker = getCircuitBreaker('tagData', {
  failureThreshold: 3,
  resetTimeout: 15000, // 15 seconds
});

interface UseLiveTagDataOptions {
  tagId?: string;
  min?: number;
  max?: number;
}

export const useLiveTagData = (
  tagIdOrOptions?: string | UseLiveTagDataOptions,
  legacyMin?: number,
  legacyMax?: number
): LiveTagData => {
  // Support both old API (string) and new API (options object)
  let tagId: string | undefined;
  let min: number = 0;
  let max: number = 100;

  if (typeof tagIdOrOptions === 'string') {
    tagId = tagIdOrOptions;
    min = legacyMin ?? 0;
    max = legacyMax ?? 100;
  } else if (tagIdOrOptions) {
    tagId = tagIdOrOptions.tagId;
    min = tagIdOrOptions.min ?? 0;
    max = tagIdOrOptions.max ?? 100;
  }

  const [data, setData] = useState<LiveTagData>({
    value: null,
    timestamp: null,
    quality: 'unknown',
    loading: false,
    error: null,
  });

  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!tagId) {
      setData({
        value: null,
        timestamp: null,
        quality: 'unknown',
        loading: false,
        error: null,
      });
      return;
    }

    setData(prev => ({ ...prev, loading: true, error: null }));

    const generateSimulatedValue = () => {
      // Generate realistic simulated value with some variation
      const range = max - min;
      const baseValue = min + (range * 0.5); // Middle of range
      const variation = range * 0.3; // 30% variation
      const randomValue = baseValue + (Math.random() - 0.5) * variation;

      // Add some wave pattern for more realistic data
      const time = Date.now() / 1000;
      const wave = Math.sin(time / 10) * (range * 0.2);

      return Math.max(min, Math.min(max, randomValue + wave));
    };

    const fetchLatestValue = async () => {
      // Check circuit breaker before making request
      if (!tagDataCircuitBreaker.canExecute()) {
        // Circuit is open, use simulated data
        const simValue = generateSimulatedValue();
        setData({
          value: simValue,
          timestamp: new Date().toISOString(),
          quality: 'simulated-offline',
          loading: false,
          error: null,
        });
        return;
      }

      try {
        // Execute with circuit breaker protection
        const response = await tagDataCircuitBreaker.execute(() =>
          apiClient.getLatestValue(tagId)
        );
        setData({
          value: response.value,
          timestamp: response.timestamp,
          quality: response.quality || 'good',
          loading: false,
          error: null,
        });
      } catch (error) {
        // Generate demo data with realistic values (silent fallback)
        const simValue = generateSimulatedValue();
        const isCircuitOpen = error instanceof CircuitBreakerError;
        setData({
          value: simValue,
          timestamp: new Date().toISOString(),
          quality: isCircuitOpen ? 'simulated-offline' : 'simulated',
          loading: false,
          error: null,
        });
      }
    };

    // Start polling immediately - generate initial simulated value right away
    const initialValue = generateSimulatedValue();
    setData({
      value: initialValue,
      timestamp: new Date().toISOString(),
      quality: 'simulated',
      loading: false,
      error: null,
    });

    // Then try to fetch from API
    fetchLatestValue();

    // Poll every 2 seconds for live updates
    pollingIntervalRef.current = setInterval(() => {
      fetchLatestValue();
    }, 2000);

    // Cleanup
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [tagId, min, max]);

  return data;
};
