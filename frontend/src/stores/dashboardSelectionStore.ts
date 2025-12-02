/**
 * 🎯 Dashboard Selection Store - Cross-Filtering & Drill-Through
 * ===============================================================
 *
 * Gerencia seleção de KPIs e drill-through entre componentes.
 * Inspirado no Power BI Cross-Filtering.
 *
 * Features:
 * - Seleção de KPI para drill-through
 * - Highlight de elementos relacionados
 * - Histórico de navegação
 * - Contexto de análise
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

// ========================================
// Types
// ========================================

export type KPIType =
  | 'oee'
  | 'availability'
  | 'performance'
  | 'quality'
  | 'energy'
  | 'production'
  | 'alarms'
  | 'mtbf'
  | 'mttr'
  | 'anomalies'
  | 'efficiency'
  | 'cost';

export interface KPISelection {
  type: KPIType;
  value: number;
  label: string;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  metadata?: Record<string, any>;
}

export interface DrillThroughContext {
  sourceKPI: KPIType;
  sourceValue: number;
  targetPage?: string;
  filters: {
    equipments?: string[];
    timeRange?: { start: Date; end: Date };
    status?: string[];
  };
}

export interface HighlightState {
  equipmentIds: string[];
  tagIds: string[];
  chartElements: string[]; // IDs of chart bars/points to highlight
}

export interface DashboardSelectionState {
  // KPI Selection
  selectedKPI: KPISelection | null;
  hoveredKPI: KPIType | null;

  // Drill-through
  drillThroughContext: DrillThroughContext | null;
  drillThroughHistory: DrillThroughContext[];

  // Cross-filter highlight
  highlight: HighlightState;

  // Comparison mode
  comparisonMode: boolean;
  comparisonKPIs: KPISelection[];

  // Tooltip context
  tooltipData: {
    visible: boolean;
    x: number;
    y: number;
    content: any;
  } | null;
}

export interface DashboardSelectionActions {
  // KPI Selection
  selectKPI: (kpi: KPISelection) => void;
  clearKPISelection: () => void;
  setHoveredKPI: (type: KPIType | null) => void;

  // Drill-through
  startDrillThrough: (context: DrillThroughContext) => void;
  exitDrillThrough: () => void;
  goBackDrillThrough: () => void;

  // Cross-filter highlight
  setHighlight: (highlight: Partial<HighlightState>) => void;
  clearHighlight: () => void;

  // Comparison
  toggleComparisonMode: () => void;
  addToComparison: (kpi: KPISelection) => void;
  removeFromComparison: (type: KPIType) => void;
  clearComparison: () => void;

  // Tooltip
  showTooltip: (x: number, y: number, content: any) => void;
  hideTooltip: () => void;

  // Reset
  resetAll: () => void;
}

// ========================================
// Default State
// ========================================

const defaultHighlight: HighlightState = {
  equipmentIds: [],
  tagIds: [],
  chartElements: [],
};

const defaultState: DashboardSelectionState = {
  selectedKPI: null,
  hoveredKPI: null,
  drillThroughContext: null,
  drillThroughHistory: [],
  highlight: defaultHighlight,
  comparisonMode: false,
  comparisonKPIs: [],
  tooltipData: null,
};

// ========================================
// Store Creation
// ========================================

export const useDashboardSelection = create<DashboardSelectionState & DashboardSelectionActions>()(
  subscribeWithSelector((set, get) => ({
    ...defaultState,

    // KPI Selection
    selectKPI: (kpi) => {
      const state = get();
      // Toggle selection if same KPI is clicked
      if (state.selectedKPI?.type === kpi.type) {
        set({ selectedKPI: null, highlight: defaultHighlight });
      } else {
        set({
          selectedKPI: kpi,
          // Auto-highlight related elements based on KPI type
          highlight: getHighlightForKPI(kpi.type, kpi.metadata),
        });
      }
    },

    clearKPISelection: () =>
      set({ selectedKPI: null, highlight: defaultHighlight }),

    setHoveredKPI: (type) =>
      set({ hoveredKPI: type }),

    // Drill-through
    startDrillThrough: (context) =>
      set((state) => ({
        drillThroughContext: context,
        drillThroughHistory: state.drillThroughContext
          ? [...state.drillThroughHistory, state.drillThroughContext]
          : state.drillThroughHistory,
      })),

    exitDrillThrough: () =>
      set({
        drillThroughContext: null,
        drillThroughHistory: [],
        selectedKPI: null,
        highlight: defaultHighlight,
      }),

    goBackDrillThrough: () =>
      set((state) => {
        const history = [...state.drillThroughHistory];
        const previousContext = history.pop();
        return {
          drillThroughContext: previousContext || null,
          drillThroughHistory: history,
        };
      }),

    // Cross-filter highlight
    setHighlight: (highlight) =>
      set((state) => ({
        highlight: { ...state.highlight, ...highlight },
      })),

    clearHighlight: () =>
      set({ highlight: defaultHighlight }),

    // Comparison mode
    toggleComparisonMode: () =>
      set((state) => ({
        comparisonMode: !state.comparisonMode,
        comparisonKPIs: state.comparisonMode ? [] : state.comparisonKPIs,
      })),

    addToComparison: (kpi) =>
      set((state) => {
        if (state.comparisonKPIs.length >= 4) return state; // Max 4 KPIs
        if (state.comparisonKPIs.some(k => k.type === kpi.type)) return state;
        return { comparisonKPIs: [...state.comparisonKPIs, kpi] };
      }),

    removeFromComparison: (type) =>
      set((state) => ({
        comparisonKPIs: state.comparisonKPIs.filter(k => k.type !== type),
      })),

    clearComparison: () =>
      set({ comparisonKPIs: [], comparisonMode: false }),

    // Tooltip
    showTooltip: (x, y, content) =>
      set({ tooltipData: { visible: true, x, y, content } }),

    hideTooltip: () =>
      set({ tooltipData: null }),

    // Reset
    resetAll: () => set(defaultState),
  }))
);

// ========================================
// Helper Functions
// ========================================

function getHighlightForKPI(type: KPIType, metadata?: Record<string, any>): HighlightState {
  // Define which elements to highlight based on KPI type
  const highlight: HighlightState = {
    equipmentIds: [],
    tagIds: [],
    chartElements: [],
  };

  if (metadata?.equipmentIds) {
    highlight.equipmentIds = metadata.equipmentIds;
  }

  if (metadata?.tagIds) {
    highlight.tagIds = metadata.tagIds;
  }

  // Add chart element IDs based on KPI type
  switch (type) {
    case 'oee':
    case 'availability':
    case 'performance':
    case 'quality':
      highlight.chartElements = ['oee-chart', 'equipment-chart'];
      break;
    case 'energy':
      highlight.chartElements = ['energy-chart', 'consumption-chart'];
      break;
    case 'alarms':
      highlight.chartElements = ['alarms-chart', 'severity-chart'];
      break;
    case 'anomalies':
      highlight.chartElements = ['anomaly-chart', 'ml-chart'];
      break;
  }

  return highlight;
}

// ========================================
// Selector Hooks
// ========================================

export const useSelectedKPI = () =>
  useDashboardSelection((state) => state.selectedKPI);

export const useHoveredKPI = () =>
  useDashboardSelection((state) => state.hoveredKPI);

export const useDrillThroughContext = () =>
  useDashboardSelection((state) => state.drillThroughContext);

export const useHighlight = () =>
  useDashboardSelection((state) => state.highlight);

export const useComparisonMode = () =>
  useDashboardSelection((state) => ({
    enabled: state.comparisonMode,
    kpis: state.comparisonKPIs,
  }));

export const useTooltipData = () =>
  useDashboardSelection((state) => state.tooltipData);

// Check if an element should be highlighted
export const useIsHighlighted = (elementId: string, elementType: 'equipment' | 'tag' | 'chart') =>
  useDashboardSelection((state) => {
    const { highlight } = state;
    switch (elementType) {
      case 'equipment':
        return highlight.equipmentIds.length === 0 || highlight.equipmentIds.includes(elementId);
      case 'tag':
        return highlight.tagIds.length === 0 || highlight.tagIds.includes(elementId);
      case 'chart':
        return highlight.chartElements.length === 0 || highlight.chartElements.includes(elementId);
      default:
        return true;
    }
  });

// Check if element should be dimmed (not highlighted when others are)
export const useIsDimmed = (elementId: string, elementType: 'equipment' | 'tag' | 'chart') =>
  useDashboardSelection((state) => {
    const { highlight, selectedKPI } = state;
    if (!selectedKPI) return false; // No selection, nothing dimmed

    switch (elementType) {
      case 'equipment':
        return highlight.equipmentIds.length > 0 && !highlight.equipmentIds.includes(elementId);
      case 'tag':
        return highlight.tagIds.length > 0 && !highlight.tagIds.includes(elementId);
      case 'chart':
        return highlight.chartElements.length > 0 && !highlight.chartElements.includes(elementId);
      default:
        return false;
    }
  });

export default useDashboardSelection;
