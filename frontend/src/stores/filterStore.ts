/**
 * 🎯 Filter Store - Sprint 6: Cross-Filtering
 * ============================================
 *
 * Global state management for dashboard filters using Zustand.
 * Enables cross-filtering between charts and components.
 *
 * Features:
 * - Time range selection (global)
 * - Equipment/Asset filtering
 * - Area filtering
 * - Tag selection
 * - URL state synchronization
 * - Cross-filter events
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { subscribeWithSelector } from 'zustand/middleware';

// ========================================
// Types
// ========================================

export type TimeRangePreset = '1h' | '4h' | '8h' | '24h' | '7d' | '30d' | 'custom';

export interface TimeRange {
  preset: TimeRangePreset;
  start: Date | null;
  end: Date | null;
}

export interface FilterState {
  // Time filters
  timeRange: TimeRange;

  // Asset hierarchy filters
  selectedSites: string[];
  selectedAreas: string[];
  selectedEquipments: string[];
  selectedTags: string[];

  // Status filters
  selectedStatuses: ('running' | 'stopped' | 'idle' | 'maintenance' | 'alarm')[];

  // OEE-specific filters
  oeeThreshold: number | null; // Filter equipment below this OEE
  showOnlyCritical: boolean;

  // Cross-filter source tracking
  lastFilterSource: string | null; // Which component triggered the filter
  crossFilterEnabled: boolean;

  // Drill-down context
  drillDownPath: Array<{
    type: 'site' | 'area' | 'equipment' | 'tag';
    id: string;
    name: string;
  }>;
}

export interface FilterActions {
  // Time range
  setTimeRange: (range: TimeRange) => void;
  setTimeRangePreset: (preset: TimeRangePreset) => void;

  // Asset selection
  setSites: (sites: string[]) => void;
  setAreas: (areas: string[]) => void;
  setEquipments: (equipments: string[]) => void;
  setTags: (tags: string[]) => void;
  toggleEquipment: (equipmentId: string) => void;
  toggleArea: (areaId: string) => void;

  // Status filters
  setStatuses: (statuses: FilterState['selectedStatuses']) => void;
  toggleStatus: (status: FilterState['selectedStatuses'][number]) => void;

  // OEE filters
  setOeeThreshold: (threshold: number | null) => void;
  setShowOnlyCritical: (show: boolean) => void;

  // Cross-filtering
  applyChartFilter: (source: string, equipmentIds: string[]) => void;
  setCrossFilterEnabled: (enabled: boolean) => void;

  // Drill-down
  drillDown: (type: FilterState['drillDownPath'][number]['type'], id: string, name: string) => void;
  drillUp: (steps?: number) => void;
  resetDrillDown: () => void;

  // Reset
  resetFilters: () => void;
  resetTimeRange: () => void;
}

// ========================================
// Default State
// ========================================

const getDefaultTimeRange = (): TimeRange => ({
  preset: '24h',
  start: new Date(Date.now() - 24 * 60 * 60 * 1000),
  end: new Date(),
});

const defaultState: FilterState = {
  timeRange: getDefaultTimeRange(),
  selectedSites: [],
  selectedAreas: [],
  selectedEquipments: [],
  selectedTags: [],
  selectedStatuses: [],
  oeeThreshold: null,
  showOnlyCritical: false,
  lastFilterSource: null,
  crossFilterEnabled: true,
  drillDownPath: [],
};

// ========================================
// Helper Functions
// ========================================

const getTimeRangeFromPreset = (preset: TimeRangePreset): TimeRange => {
  const now = new Date();
  let start: Date;

  switch (preset) {
    case '1h':
      start = new Date(now.getTime() - 1 * 60 * 60 * 1000);
      break;
    case '4h':
      start = new Date(now.getTime() - 4 * 60 * 60 * 1000);
      break;
    case '8h':
      start = new Date(now.getTime() - 8 * 60 * 60 * 1000);
      break;
    case '24h':
      start = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      break;
    case '7d':
      start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      break;
    case '30d':
      start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      break;
    case 'custom':
      return { preset: 'custom', start: null, end: null };
    default:
      start = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  }

  return { preset, start, end: now };
};

// ========================================
// Store Creation
// ========================================

export const useFilterStore = create<FilterState & FilterActions>()(
  subscribeWithSelector(
    persist(
      (set, get) => ({
        ...defaultState,

        // Time range actions
        setTimeRange: (range) =>
          set({ timeRange: range, lastFilterSource: 'timeRange' }),

        setTimeRangePreset: (preset) =>
          set({
            timeRange: getTimeRangeFromPreset(preset),
            lastFilterSource: 'timeRange',
          }),

        // Asset selection actions
        setSites: (sites) =>
          set({
            selectedSites: sites,
            // Clear child selections when parent changes
            selectedAreas: [],
            selectedEquipments: [],
            selectedTags: [],
            lastFilterSource: 'sites',
          }),

        setAreas: (areas) =>
          set({
            selectedAreas: areas,
            // Clear child selections
            selectedEquipments: [],
            selectedTags: [],
            lastFilterSource: 'areas',
          }),

        setEquipments: (equipments) =>
          set({
            selectedEquipments: equipments,
            selectedTags: [],
            lastFilterSource: 'equipments',
          }),

        setTags: (tags) =>
          set({
            selectedTags: tags,
            lastFilterSource: 'tags',
          }),

        toggleEquipment: (equipmentId) =>
          set((state) => {
            const isSelected = state.selectedEquipments.includes(equipmentId);
            return {
              selectedEquipments: isSelected
                ? state.selectedEquipments.filter((id) => id !== equipmentId)
                : [...state.selectedEquipments, equipmentId],
              lastFilterSource: 'equipments',
            };
          }),

        toggleArea: (areaId) =>
          set((state) => {
            const isSelected = state.selectedAreas.includes(areaId);
            return {
              selectedAreas: isSelected
                ? state.selectedAreas.filter((id) => id !== areaId)
                : [...state.selectedAreas, areaId],
              selectedEquipments: [], // Clear equipment selection
              lastFilterSource: 'areas',
            };
          }),

        // Status filters
        setStatuses: (statuses) =>
          set({ selectedStatuses: statuses, lastFilterSource: 'statuses' }),

        toggleStatus: (status) =>
          set((state) => {
            const isSelected = state.selectedStatuses.includes(status);
            return {
              selectedStatuses: isSelected
                ? state.selectedStatuses.filter((s) => s !== status)
                : [...state.selectedStatuses, status],
              lastFilterSource: 'statuses',
            };
          }),

        // OEE filters
        setOeeThreshold: (threshold) =>
          set({ oeeThreshold: threshold, lastFilterSource: 'oeeThreshold' }),

        setShowOnlyCritical: (show) =>
          set({ showOnlyCritical: show, lastFilterSource: 'critical' }),

        // Cross-filtering from chart clicks
        applyChartFilter: (source, equipmentIds) => {
          const state = get();
          if (!state.crossFilterEnabled) return;

          set({
            selectedEquipments: equipmentIds,
            lastFilterSource: source,
          });
        },

        setCrossFilterEnabled: (enabled) =>
          set({ crossFilterEnabled: enabled }),

        // Drill-down navigation
        drillDown: (type, id, name) =>
          set((state) => ({
            drillDownPath: [...state.drillDownPath, { type, id, name }],
            // Update relevant selection based on type
            ...(type === 'site' && { selectedSites: [id] }),
            ...(type === 'area' && { selectedAreas: [id] }),
            ...(type === 'equipment' && { selectedEquipments: [id] }),
            ...(type === 'tag' && { selectedTags: [id] }),
            lastFilterSource: 'drillDown',
          })),

        drillUp: (steps = 1) =>
          set((state) => {
            const newPath = state.drillDownPath.slice(0, -steps);
            const lastItem = newPath[newPath.length - 1];

            // Clear selections below the current drill-down level
            let clearedSelections = {};
            if (!lastItem) {
              clearedSelections = {
                selectedSites: [],
                selectedAreas: [],
                selectedEquipments: [],
                selectedTags: [],
              };
            } else {
              switch (lastItem.type) {
                case 'site':
                  clearedSelections = {
                    selectedAreas: [],
                    selectedEquipments: [],
                    selectedTags: [],
                  };
                  break;
                case 'area':
                  clearedSelections = {
                    selectedEquipments: [],
                    selectedTags: [],
                  };
                  break;
                case 'equipment':
                  clearedSelections = { selectedTags: [] };
                  break;
              }
            }

            return {
              drillDownPath: newPath,
              ...clearedSelections,
              lastFilterSource: 'drillUp',
            };
          }),

        resetDrillDown: () =>
          set({
            drillDownPath: [],
            selectedSites: [],
            selectedAreas: [],
            selectedEquipments: [],
            selectedTags: [],
            lastFilterSource: 'resetDrillDown',
          }),

        // Reset all filters
        resetFilters: () =>
          set({
            ...defaultState,
            timeRange: getDefaultTimeRange(),
            lastFilterSource: 'reset',
          }),

        resetTimeRange: () =>
          set({
            timeRange: getDefaultTimeRange(),
            lastFilterSource: 'resetTime',
          }),
      }),
      {
        name: 'optiflow-filters',
        storage: createJSONStorage(() => sessionStorage),
        partialize: (state) => ({
          // Only persist these fields
          timeRange: state.timeRange,
          selectedSites: state.selectedSites,
          selectedAreas: state.selectedAreas,
          selectedEquipments: state.selectedEquipments,
          crossFilterEnabled: state.crossFilterEnabled,
        }),
      }
    )
  )
);

// ========================================
// Selector Hooks for Performance
// ========================================

export const useTimeRange = () => useFilterStore((state) => state.timeRange);
export const useSelectedEquipments = () => useFilterStore((state) => state.selectedEquipments);
export const useSelectedAreas = () => useFilterStore((state) => state.selectedAreas);
export const useDrillDownPath = () => useFilterStore((state) => state.drillDownPath);
export const useCrossFilterEnabled = () => useFilterStore((state) => state.crossFilterEnabled);

// Combined selector for API queries
export const useFilterParams = () =>
  useFilterStore((state) => ({
    timeRange: state.timeRange,
    equipments: state.selectedEquipments,
    areas: state.selectedAreas,
    tags: state.selectedTags,
    statuses: state.selectedStatuses,
    oeeThreshold: state.oeeThreshold,
    showOnlyCritical: state.showOnlyCritical,
  }));

// Check if any filter is active
export const useHasActiveFilters = () =>
  useFilterStore(
    (state) =>
      state.selectedSites.length > 0 ||
      state.selectedAreas.length > 0 ||
      state.selectedEquipments.length > 0 ||
      state.selectedTags.length > 0 ||
      state.selectedStatuses.length > 0 ||
      state.oeeThreshold !== null ||
      state.showOnlyCritical
  );

export default useFilterStore;
