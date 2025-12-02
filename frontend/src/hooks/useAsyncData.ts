/**
 * useAsyncData Hook
 * ==================
 * Generic hook for async data fetching with loading, error handling,
 * auto-refresh, and caching capabilities.
 *
 * Replaces 15+ duplicate implementations across the codebase.
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { REFRESH_INTERVALS } from '../utils/constants';

export interface UseAsyncDataOptions<T> {
  /** Initial data value */
  initialData?: T | null;
  /** Auto-refresh interval in milliseconds (use REFRESH_INTERVALS constants) */
  refreshInterval?: number;
  /** Whether to enable auto-refresh */
  autoRefresh?: boolean;
  /** Whether to fetch on mount */
  fetchOnMount?: boolean;
  /** Dependencies that trigger a refetch when changed */
  deps?: any[];
  /** Callback on successful fetch */
  onSuccess?: (data: T) => void;
  /** Callback on error */
  onError?: (error: Error) => void;
  /** Whether to keep previous data while loading new data */
  keepPreviousData?: boolean;
  /** Retry count on failure */
  retryCount?: number;
  /** Retry delay in milliseconds */
  retryDelay?: number;
  /** Whether the hook is enabled (useful for conditional fetching) */
  enabled?: boolean;
}

export interface UseAsyncDataResult<T> {
  /** The fetched data */
  data: T | null;
  /** Whether data is currently being fetched */
  loading: boolean;
  /** Error message if fetch failed */
  error: string | null;
  /** Manually trigger a refresh */
  refresh: () => Promise<void>;
  /** Reset the state to initial values */
  reset: () => void;
  /** Whether initial fetch has completed */
  isInitialized: boolean;
  /** Last successful fetch timestamp */
  lastUpdated: Date | null;
  /** Whether currently retrying after a failure */
  isRetrying: boolean;
}

/**
 * Generic async data fetching hook
 *
 * @example
 * ```tsx
 * const { data, loading, error, refresh } = useAsyncData(
 *   async () => {
 *     const response = await apiClient.get('/api/v1/dashboard/stats');
 *     return response.data;
 *   },
 *   {
 *     refreshInterval: REFRESH_INTERVALS.DASHBOARD,
 *     autoRefresh: true,
 *     onError: (err) => showToast.error(err.message),
 *   }
 * );
 * ```
 */
export function useAsyncData<T>(
  fetcher: () => Promise<T>,
  options: UseAsyncDataOptions<T> = {}
): UseAsyncDataResult<T> {
  const {
    initialData = null,
    refreshInterval = REFRESH_INTERVALS.DASHBOARD,
    autoRefresh = false,
    fetchOnMount = true,
    deps = [],
    onSuccess,
    onError,
    keepPreviousData = false,
    retryCount = 0,
    retryDelay = 1000,
    enabled = true,
  } = options;

  const [data, setData] = useState<T | null>(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);

  // Refs to handle cleanup and prevent race conditions
  const isMountedRef = useRef(true);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef(0);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Memoize fetcher to prevent unnecessary recreations
  const stableFetcher = useCallback(fetcher, deps);

  const fetchData = useCallback(async (isRetry = false) => {
    if (!enabled) return;

    // Cancel any pending requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      if (!keepPreviousData || !isRetry) {
        setLoading(true);
      }
      if (isRetry) {
        setIsRetrying(true);
      }

      const result = await stableFetcher();

      if (isMountedRef.current) {
        setData(result);
        setError(null);
        setLastUpdated(new Date());
        setIsInitialized(true);
        retryCountRef.current = 0;
        onSuccess?.(result);
      }
    } catch (err: any) {
      if (!isMountedRef.current) return;

      // Don't treat abort as an error
      if (err.name === 'AbortError') return;

      const errorMessage = err.message || 'An error occurred while fetching data';

      // Handle retry logic
      if (retryCount > 0 && retryCountRef.current < retryCount) {
        retryCountRef.current++;
        console.warn(`Fetch failed, retrying (${retryCountRef.current}/${retryCount})...`);
        setTimeout(() => fetchData(true), retryDelay);
        return;
      }

      setError(errorMessage);
      onError?.(err);
      console.error('useAsyncData error:', err);
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
        setIsRetrying(false);
      }
    }
  }, [stableFetcher, enabled, keepPreviousData, retryCount, retryDelay, onSuccess, onError]);

  const refresh = useCallback(async () => {
    retryCountRef.current = 0;
    await fetchData();
  }, [fetchData]);

  const reset = useCallback(() => {
    setData(initialData);
    setError(null);
    setLoading(false);
    setIsInitialized(false);
    setLastUpdated(null);
    retryCountRef.current = 0;
  }, [initialData]);

  // Initial fetch on mount
  useEffect(() => {
    isMountedRef.current = true;

    if (fetchOnMount && enabled) {
      fetchData();
    }

    return () => {
      isMountedRef.current = false;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchOnMount, enabled, ...deps]);

  // Auto-refresh interval
  useEffect(() => {
    if (autoRefresh && enabled && refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [autoRefresh, enabled, refreshInterval, fetchData]);

  return {
    data,
    loading,
    error,
    refresh,
    reset,
    isInitialized,
    lastUpdated,
    isRetrying,
  };
}

/**
 * Hook for fetching multiple data sources in parallel
 *
 * @example
 * ```tsx
 * const { data, loading, error } = useParallelData({
 *   stats: () => apiClient.get('/api/v1/stats'),
 *   alerts: () => apiClient.get('/api/v1/alerts'),
 *   trends: () => apiClient.get('/api/v1/trends'),
 * });
 *
 * // data.stats, data.alerts, data.trends
 * ```
 */
export function useParallelData<T extends Record<string, () => Promise<any>>>(
  fetchers: T,
  options: Omit<UseAsyncDataOptions<any>, 'initialData'> = {}
): UseAsyncDataResult<{ [K in keyof T]: Awaited<ReturnType<T[K]>> }> {
  const keys = useMemo(() => Object.keys(fetchers), []);

  const combinedFetcher = useCallback(async () => {
    const results = await Promise.all(
      keys.map(key => fetchers[key]())
    );

    return keys.reduce((acc, key, index) => {
      acc[key] = results[index];
      return acc;
    }, {} as any);
  }, [keys, ...Object.values(fetchers)]);

  return useAsyncData(combinedFetcher, options);
}

/**
 * Hook for paginated data fetching
 */
export interface UsePaginatedDataOptions<T> extends UseAsyncDataOptions<T[]> {
  pageSize?: number;
  initialPage?: number;
}

export interface UsePaginatedDataResult<T> extends Omit<UseAsyncDataResult<T[]>, 'data'> {
  data: T[];
  page: number;
  pageSize: number;
  totalPages: number;
  totalItems: number;
  hasNextPage: boolean;
  hasPrevPage: boolean;
  nextPage: () => void;
  prevPage: () => void;
  goToPage: (page: number) => void;
  setPageSize: (size: number) => void;
}

export function usePaginatedData<T>(
  fetcher: (page: number, pageSize: number) => Promise<{ items: T[]; total: number }>,
  options: UsePaginatedDataOptions<T> = {}
): UsePaginatedDataResult<T> {
  const { pageSize: initialPageSize = 10, initialPage = 1, ...restOptions } = options;

  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSizeState] = useState(initialPageSize);
  const [totalItems, setTotalItems] = useState(0);

  const wrappedFetcher = useCallback(async () => {
    const result = await fetcher(page, pageSize);
    setTotalItems(result.total);
    return result.items;
  }, [fetcher, page, pageSize]);

  const result = useAsyncData(wrappedFetcher, {
    ...restOptions,
    deps: [page, pageSize, ...(restOptions.deps || [])],
  });

  const totalPages = Math.ceil(totalItems / pageSize);

  return {
    ...result,
    data: result.data || [],
    page,
    pageSize,
    totalPages,
    totalItems,
    hasNextPage: page < totalPages,
    hasPrevPage: page > 1,
    nextPage: () => setPage(p => Math.min(p + 1, totalPages)),
    prevPage: () => setPage(p => Math.max(p - 1, 1)),
    goToPage: (newPage: number) => setPage(Math.max(1, Math.min(newPage, totalPages))),
    setPageSize: (size: number) => {
      setPageSizeState(size);
      setPage(1); // Reset to first page when changing page size
    },
  };
}

export default useAsyncData;
