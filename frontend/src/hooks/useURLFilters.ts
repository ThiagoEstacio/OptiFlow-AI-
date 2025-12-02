/**
 * 🔗 useURLFilters - URL State Synchronization
 * =============================================
 *
 * Syncs filter state with URL query parameters.
 * Enables shareable filtered views and browser history navigation.
 *
 * URL Parameters:
 * - t: time range preset (1h, 4h, 8h, 24h, 7d, 30d)
 * - eq: equipment IDs (comma-separated)
 * - area: area IDs (comma-separated)
 * - status: status filters (comma-separated)
 * - oee: OEE threshold
 * - critical: show only critical (1/0)
 */

import { useEffect, useCallback, useRef } from 'react';
import { useSearchParams, useLocation } from 'react-router-dom';
import { useFilterStore, TimeRangePreset } from '../stores/filterStore';

interface URLFilterOptions {
  enabled?: boolean;
  syncOnMount?: boolean;
  debounceMs?: number;
}

export const useURLFilters = (options: URLFilterOptions = {}) => {
  const { enabled = true, syncOnMount = true, debounceMs = 300 } = options;

  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const isInitialMount = useRef(true);
  const debounceTimeout = useRef<NodeJS.Timeout>();

  // Get filter actions and state
  const {
    timeRange,
    selectedEquipments,
    selectedAreas,
    selectedStatuses,
    oeeThreshold,
    showOnlyCritical,
    setTimeRangePreset,
    setEquipments,
    setAreas,
    setStatuses,
    setOeeThreshold,
    setShowOnlyCritical,
  } = useFilterStore();

  // Parse URL params and apply to store (on mount)
  const syncFromURL = useCallback(() => {
    const t = searchParams.get('t') as TimeRangePreset | null;
    const eq = searchParams.get('eq');
    const area = searchParams.get('area');
    const status = searchParams.get('status');
    const oee = searchParams.get('oee');
    const critical = searchParams.get('critical');

    if (t && ['1h', '4h', '8h', '24h', '7d', '30d'].includes(t)) {
      setTimeRangePreset(t);
    }

    if (eq) {
      setEquipments(eq.split(',').filter(Boolean));
    }

    if (area) {
      setAreas(area.split(',').filter(Boolean));
    }

    if (status) {
      const validStatuses = ['running', 'stopped', 'idle', 'maintenance', 'alarm'] as const;
      const parsed = status.split(',').filter((s): s is typeof validStatuses[number] =>
        validStatuses.includes(s as any)
      );
      setStatuses(parsed);
    }

    if (oee) {
      const threshold = parseFloat(oee);
      if (!isNaN(threshold) && threshold >= 0 && threshold <= 100) {
        setOeeThreshold(threshold);
      }
    }

    if (critical === '1') {
      setShowOnlyCritical(true);
    }
  }, [
    searchParams,
    setTimeRangePreset,
    setEquipments,
    setAreas,
    setStatuses,
    setOeeThreshold,
    setShowOnlyCritical,
  ]);

  // Sync store state to URL (debounced)
  const syncToURL = useCallback(() => {
    if (!enabled) return;

    if (debounceTimeout.current) {
      clearTimeout(debounceTimeout.current);
    }

    debounceTimeout.current = setTimeout(() => {
      const params = new URLSearchParams();

      // Time range
      if (timeRange.preset !== '24h') {
        params.set('t', timeRange.preset);
      }

      // Equipments
      if (selectedEquipments.length > 0) {
        params.set('eq', selectedEquipments.join(','));
      }

      // Areas
      if (selectedAreas.length > 0) {
        params.set('area', selectedAreas.join(','));
      }

      // Statuses
      if (selectedStatuses.length > 0) {
        params.set('status', selectedStatuses.join(','));
      }

      // OEE threshold
      if (oeeThreshold !== null) {
        params.set('oee', oeeThreshold.toString());
      }

      // Critical only
      if (showOnlyCritical) {
        params.set('critical', '1');
      }

      // Only update if params changed
      const currentParams = searchParams.toString();
      const newParams = params.toString();

      if (currentParams !== newParams) {
        setSearchParams(params, { replace: true });
      }
    }, debounceMs);
  }, [
    enabled,
    debounceMs,
    timeRange.preset,
    selectedEquipments,
    selectedAreas,
    selectedStatuses,
    oeeThreshold,
    showOnlyCritical,
    searchParams,
    setSearchParams,
  ]);

  // Sync from URL on mount
  useEffect(() => {
    if (syncOnMount && isInitialMount.current && searchParams.toString()) {
      syncFromURL();
    }
    isInitialMount.current = false;
  }, [syncOnMount, syncFromURL, searchParams]);

  // Sync to URL when filters change (after initial mount)
  useEffect(() => {
    if (!isInitialMount.current && enabled) {
      syncToURL();
    }
  }, [
    enabled,
    timeRange.preset,
    selectedEquipments,
    selectedAreas,
    selectedStatuses,
    oeeThreshold,
    showOnlyCritical,
    syncToURL,
  ]);

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceTimeout.current) {
        clearTimeout(debounceTimeout.current);
      }
    };
  }, []);

  // Generate shareable URL
  const getShareableURL = useCallback(() => {
    const baseURL = window.location.origin + location.pathname;
    const params = new URLSearchParams();

    if (timeRange.preset !== '24h') {
      params.set('t', timeRange.preset);
    }
    if (selectedEquipments.length > 0) {
      params.set('eq', selectedEquipments.join(','));
    }
    if (selectedAreas.length > 0) {
      params.set('area', selectedAreas.join(','));
    }
    if (selectedStatuses.length > 0) {
      params.set('status', selectedStatuses.join(','));
    }
    if (oeeThreshold !== null) {
      params.set('oee', oeeThreshold.toString());
    }
    if (showOnlyCritical) {
      params.set('critical', '1');
    }

    const queryString = params.toString();
    return queryString ? `${baseURL}?${queryString}` : baseURL;
  }, [
    location.pathname,
    timeRange.preset,
    selectedEquipments,
    selectedAreas,
    selectedStatuses,
    oeeThreshold,
    showOnlyCritical,
  ]);

  // Copy shareable URL to clipboard
  const copyShareableURL = useCallback(async () => {
    const url = getShareableURL();
    try {
      await navigator.clipboard.writeText(url);
      return true;
    } catch {
      console.error('Failed to copy URL to clipboard');
      return false;
    }
  }, [getShareableURL]);

  return {
    syncFromURL,
    syncToURL,
    getShareableURL,
    copyShareableURL,
  };
};

export default useURLFilters;
