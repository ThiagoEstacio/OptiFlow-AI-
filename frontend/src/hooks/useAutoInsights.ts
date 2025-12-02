/**
 * useAutoInsights Hook
 *
 * Provides automatic insights from the AI Agent:
 * - MTBF/MTTR for PCM (Maintenance)
 * - Failure Prediction for Predictive Maintenance
 * - SPC/CEP for Quality Control
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  MTBFMTTRResult,
  FailurePrediction,
  SPCLimits,
  getMTBFMTTR,
  predictFailure,
  calculateSPCLimits
} from '../api/insights';

// ========================================
// Types
// ========================================

interface UseAutoInsightsOptions {
  equipmentId?: string;
  qualityTagId?: string;
  specificationLimits?: {
    usl?: number;
    lsl?: number;
    target?: number;
  };
  autoRefresh?: boolean;
  refreshInterval?: number; // seconds
  mtbfDuration?: '7d' | '30d' | '90d' | '180d' | '365d';
  predictionHorizon?: '24h' | '7d' | '14d' | '30d';
  spcDuration?: '1h' | '6h' | '12h' | '24h' | '7d' | '30d';
}

interface InsightsState {
  mtbf: {
    data: MTBFMTTRResult | null;
    loading: boolean;
    error: string | null;
  };
  prediction: {
    data: FailurePrediction | null;
    loading: boolean;
    error: string | null;
  };
  spc: {
    data: SPCLimits | null;
    loading: boolean;
    error: string | null;
  };
  lastUpdate: Date | null;
  isRefreshing: boolean;
}

interface UseAutoInsightsReturn extends InsightsState {
  refreshMTBF: () => Promise<void>;
  refreshPrediction: () => Promise<void>;
  refreshSPC: () => Promise<void>;
  refreshAll: () => Promise<void>;
  hasAnyData: boolean;
  hasCriticalInsights: boolean;
  criticalCount: number;
}

// ========================================
// Hook Implementation
// ========================================

export const useAutoInsights = (options: UseAutoInsightsOptions = {}): UseAutoInsightsReturn => {
  const {
    equipmentId,
    qualityTagId,
    specificationLimits,
    autoRefresh = true,
    refreshInterval = 60,
    mtbfDuration = '30d',
    predictionHorizon = '7d',
    spcDuration = '24h'
  } = options;

  const [state, setState] = useState<InsightsState>({
    mtbf: { data: null, loading: false, error: null },
    prediction: { data: null, loading: false, error: null },
    spc: { data: null, loading: false, error: null },
    lastUpdate: null,
    isRefreshing: false
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);

  // Fetch MTBF/MTTR
  const refreshMTBF = useCallback(async () => {
    if (!equipmentId) return;

    setState(prev => ({
      ...prev,
      mtbf: { ...prev.mtbf, loading: true, error: null }
    }));

    try {
      const data = await getMTBFMTTR(equipmentId, { duration: mtbfDuration });

      if (isMountedRef.current) {
        setState(prev => ({
          ...prev,
          mtbf: { data, loading: false, error: null },
          lastUpdate: new Date()
        }));
      }
    } catch (err: any) {
      if (isMountedRef.current) {
        setState(prev => ({
          ...prev,
          mtbf: { ...prev.mtbf, loading: false, error: err.message || 'Erro ao buscar MTBF/MTTR' }
        }));
      }
    }
  }, [equipmentId, mtbfDuration]);

  // Fetch Prediction
  const refreshPrediction = useCallback(async () => {
    if (!equipmentId) return;

    setState(prev => ({
      ...prev,
      prediction: { ...prev.prediction, loading: true, error: null }
    }));

    try {
      const data = await predictFailure(equipmentId, { predictionHorizon });

      if (isMountedRef.current) {
        setState(prev => ({
          ...prev,
          prediction: { data, loading: false, error: null },
          lastUpdate: new Date()
        }));
      }
    } catch (err: any) {
      if (isMountedRef.current) {
        setState(prev => ({
          ...prev,
          prediction: { ...prev.prediction, loading: false, error: err.message || 'Erro na predição' }
        }));
      }
    }
  }, [equipmentId, predictionHorizon]);

  // Fetch SPC
  const refreshSPC = useCallback(async () => {
    if (!qualityTagId) return;

    setState(prev => ({
      ...prev,
      spc: { ...prev.spc, loading: true, error: null }
    }));

    try {
      const data = await calculateSPCLimits(qualityTagId, {
        duration: spcDuration,
        specificationLimits
      });

      if (isMountedRef.current) {
        setState(prev => ({
          ...prev,
          spc: { data, loading: false, error: null },
          lastUpdate: new Date()
        }));
      }
    } catch (err: any) {
      if (isMountedRef.current) {
        setState(prev => ({
          ...prev,
          spc: { ...prev.spc, loading: false, error: err.message || 'Erro no CEP' }
        }));
      }
    }
  }, [qualityTagId, spcDuration, specificationLimits]);

  // Refresh all data
  const refreshAll = useCallback(async () => {
    setState(prev => ({ ...prev, isRefreshing: true }));

    await Promise.all([
      equipmentId ? refreshMTBF() : Promise.resolve(),
      equipmentId ? refreshPrediction() : Promise.resolve(),
      qualityTagId ? refreshSPC() : Promise.resolve()
    ]);

    if (isMountedRef.current) {
      setState(prev => ({ ...prev, isRefreshing: false }));
    }
  }, [refreshMTBF, refreshPrediction, refreshSPC, equipmentId, qualityTagId]);

  // Initial load
  useEffect(() => {
    refreshAll();
  }, [equipmentId, qualityTagId]);

  // Auto-refresh setup
  useEffect(() => {
    if (autoRefresh && (equipmentId || qualityTagId)) {
      intervalRef.current = setInterval(refreshAll, refreshInterval * 1000);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh, refreshInterval, refreshAll, equipmentId, qualityTagId]);

  // Cleanup on unmount
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Computed values
  const hasAnyData = !!(state.mtbf.data || state.prediction.data || state.spc.data);

  const hasCriticalInsights =
    state.mtbf.data?.reliability_classification === 'Crítico' ||
    state.prediction.data?.overall_risk_level === 'critical' ||
    state.prediction.data?.overall_risk_level === 'high' ||
    state.spc.data?.stability_assessment?.status === 'Instável';

  const criticalCount =
    (state.mtbf.data?.reliability_classification === 'Crítico' ? 1 : 0) +
    (state.prediction.data?.overall_risk_level === 'critical' ? 1 : 0) +
    (state.prediction.data?.overall_risk_level === 'high' ? 1 : 0) +
    (state.spc.data?.stability_assessment?.status === 'Instável' ? 1 : 0);

  return {
    ...state,
    refreshMTBF,
    refreshPrediction,
    refreshSPC,
    refreshAll,
    hasAnyData,
    hasCriticalInsights,
    criticalCount
  };
};

// ========================================
// Helper Hook: useEquipmentInsights
// ========================================

export const useEquipmentInsights = (equipmentId: string, autoRefresh = true) => {
  return useAutoInsights({
    equipmentId,
    autoRefresh,
    refreshInterval: 120 // 2 minutes for equipment
  });
};

// ========================================
// Helper Hook: useQualityInsights
// ========================================

export const useQualityInsights = (
  tagId: string,
  specLimits?: { usl?: number; lsl?: number },
  autoRefresh = true
) => {
  return useAutoInsights({
    qualityTagId: tagId,
    specificationLimits: specLimits,
    autoRefresh,
    refreshInterval: 60 // 1 minute for quality
  });
};

export default useAutoInsights;
