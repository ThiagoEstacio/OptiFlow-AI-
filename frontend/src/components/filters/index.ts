/**
 * 🎛️ Filter Components - Sprint 6
 * =================================
 *
 * Cross-filtering and navigation components.
 */

export { FilterBar } from './FilterBar';
export { DrillDownBreadcrumb } from './DrillDownBreadcrumb';
export { CrossFilterPanel } from './CrossFilterPanel';

// Re-export store hooks for convenience
export {
  useFilterStore,
  useTimeRange,
  useSelectedEquipments,
  useSelectedAreas,
  useDrillDownPath,
  useCrossFilterEnabled,
  useFilterParams,
  useHasActiveFilters,
} from '../../stores/filterStore';

// Re-export URL sync hook
export { useURLFilters } from '../../hooks/useURLFilters';

// Re-export dashboard selection hooks
export {
  useDashboardSelection,
  useSelectedKPI,
  useHoveredKPI,
  useDrillThroughContext,
  useHighlight,
  useComparisonMode,
  useIsHighlighted,
  useIsDimmed,
} from '../../stores/dashboardSelectionStore';

export type { KPIType, KPISelection } from '../../stores/dashboardSelectionStore';
