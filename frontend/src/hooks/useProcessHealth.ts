/**
 * useProcessHealth Hook
 *
 * Real-time process health monitoring with automatic anomaly detection
 * and AI-powered diagnostics. Monitors:
 * - Tag values and trends
 * - Equipment health status
 * - Process KPIs
 * - Anomalies and alerts
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { gatewayEdgeApi, RealtimeValue } from '../api/gatewayEdge';
import { apiClient } from '../api/client';

// ========================================
// Types
// ========================================

export type HealthStatus = 'healthy' | 'warning' | 'critical' | 'unknown';
export type TrendDirection = 'up' | 'down' | 'stable';
export type AlertSeverity = 'info' | 'low' | 'medium' | 'high' | 'critical';

export interface TagHealth {
  tagId: string;
  tagName: string;
  currentValue: number | null;
  unit?: string;
  status: HealthStatus;
  trend: TrendDirection;
  trendPercent: number;
  limits?: {
    low?: number;
    high?: number;
    lowLow?: number;
    highHigh?: number;
  };
  lastUpdate: Date | null;
  history: { value: number; timestamp: Date }[];
}

export interface ProcessAlert {
  id: string;
  type: 'anomaly' | 'threshold' | 'trend' | 'equipment' | 'prediction';
  severity: AlertSeverity;
  title: string;
  description: string;
  tagId?: string;
  equipmentId?: string;
  value?: number;
  threshold?: number;
  timestamp: Date;
  acknowledged: boolean;
  recommendations: string[];
  autoResolved?: boolean;
}

export interface EquipmentHealth {
  equipmentId: string;
  name: string;
  type: string;
  status: HealthStatus;
  isRunning: boolean;
  relatedTags: string[];
  alerts: ProcessAlert[];
  metrics: {
    availability?: number;
    efficiency?: number;
    oee?: number;
  };
}

export interface ProcessKPI {
  id: string;
  name: string;
  value: number;
  unit: string;
  target?: number;
  min?: number;
  max?: number;
  status: HealthStatus;
  trend: TrendDirection;
  trendPercent: number;
}

export interface ProcessHealthState {
  overallStatus: HealthStatus;
  tags: Record<string, TagHealth>;
  equipment: Record<string, EquipmentHealth>;
  alerts: ProcessAlert[];
  kpis: ProcessKPI[];
  lastUpdate: Date | null;
  isLoading: boolean;
  error: string | null;
  connectionStatus: 'connected' | 'connecting' | 'disconnected';
}

export interface UseProcessHealthOptions {
  tagIds?: string[];
  equipmentIds?: string[];
  refreshInterval?: number; // ms
  enableAnomalyDetection?: boolean;
  enablePredictions?: boolean;
  alertThresholds?: Record<string, { low?: number; high?: number; lowLow?: number; highHigh?: number }>;
}

// ========================================
// Anomaly Detection Logic
// ========================================

const detectAnomaly = (
  history: { value: number; timestamp: Date }[],
  currentValue: number
): { isAnomaly: boolean; severity: AlertSeverity; reason: string } => {
  if (history.length < 5) {
    return { isAnomaly: false, severity: 'info', reason: '' };
  }

  const values = history.map(h => h.value);
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const stdDev = Math.sqrt(values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length);

  const zScore = Math.abs((currentValue - mean) / (stdDev || 1));

  if (zScore > 4) {
    return {
      isAnomaly: true,
      severity: 'critical',
      reason: `Valor ${currentValue.toFixed(2)} está ${zScore.toFixed(1)} desvios padrões da média`
    };
  }
  if (zScore > 3) {
    return {
      isAnomaly: true,
      severity: 'high',
      reason: `Valor anômalo detectado (z-score: ${zScore.toFixed(1)})`
    };
  }
  if (zScore > 2.5) {
    return {
      isAnomaly: true,
      severity: 'medium',
      reason: `Valor levemente fora do padrão (z-score: ${zScore.toFixed(1)})`
    };
  }

  return { isAnomaly: false, severity: 'info', reason: '' };
};

const calculateTrend = (
  history: { value: number; timestamp: Date }[]
): { direction: TrendDirection; percent: number } => {
  if (history.length < 2) {
    return { direction: 'stable', percent: 0 };
  }

  const recentValues = history.slice(-10);
  const firstHalf = recentValues.slice(0, Math.floor(recentValues.length / 2));
  const secondHalf = recentValues.slice(Math.floor(recentValues.length / 2));

  const firstAvg = firstHalf.reduce((a, b) => a + b.value, 0) / firstHalf.length;
  const secondAvg = secondHalf.reduce((a, b) => a + b.value, 0) / secondHalf.length;

  const changePercent = firstAvg !== 0 ? ((secondAvg - firstAvg) / Math.abs(firstAvg)) * 100 : 0;

  if (Math.abs(changePercent) < 2) {
    return { direction: 'stable', percent: changePercent };
  }
  return {
    direction: changePercent > 0 ? 'up' : 'down',
    percent: changePercent
  };
};

const determineTagStatus = (
  value: number | null,
  limits?: TagHealth['limits']
): HealthStatus => {
  if (value === null) return 'unknown';
  if (!limits) return 'healthy';

  if (limits.lowLow !== undefined && value <= limits.lowLow) return 'critical';
  if (limits.highHigh !== undefined && value >= limits.highHigh) return 'critical';
  if (limits.low !== undefined && value <= limits.low) return 'warning';
  if (limits.high !== undefined && value >= limits.high) return 'warning';

  return 'healthy';
};

// ========================================
// Recommendation Generator
// ========================================

const generateRecommendations = (
  alert: Partial<ProcessAlert>,
  tagHealth?: TagHealth
): string[] => {
  const recommendations: string[] = [];

  switch (alert.type) {
    case 'threshold':
      if (alert.value !== undefined && alert.threshold !== undefined) {
        if (alert.value > alert.threshold) {
          recommendations.push(`Reduzir ${tagHealth?.tagName || 'valor'} para abaixo de ${alert.threshold}`);
          recommendations.push('Verificar se há obstruções ou falhas no sistema');
          recommendations.push('Considerar parada programada para inspeção');
        } else {
          recommendations.push(`Aumentar ${tagHealth?.tagName || 'valor'} para acima de ${alert.threshold}`);
          recommendations.push('Verificar alimentação do processo');
        }
      }
      break;

    case 'anomaly':
      recommendations.push('Investigar causa da variação anormal');
      recommendations.push('Verificar sensores e instrumentação');
      recommendations.push('Comparar com histórico de eventos similares');
      break;

    case 'trend':
      if (tagHealth?.trend === 'up') {
        recommendations.push('Monitorar tendência de aumento');
        recommendations.push('Preparar ação preventiva se continuar subindo');
      } else {
        recommendations.push('Monitorar tendência de queda');
        recommendations.push('Verificar possível perda de eficiência');
      }
      break;

    case 'equipment':
      recommendations.push('Verificar status do equipamento');
      recommendations.push('Consultar log de manutenção');
      recommendations.push('Acionar equipe de manutenção se necessário');
      break;

    case 'prediction':
      recommendations.push('Agendar manutenção preventiva');
      recommendations.push('Monitorar indicadores de desgaste');
      recommendations.push('Preparar peças de reposição');
      break;
  }

  return recommendations;
};

// ========================================
// Hook Implementation
// ========================================

export const useProcessHealth = (options: UseProcessHealthOptions = {}): ProcessHealthState & {
  refresh: () => Promise<void>;
  acknowledgeAlert: (alertId: string) => void;
  clearResolvedAlerts: () => void;
  getTagHealth: (tagId: string) => TagHealth | undefined;
  getEquipmentHealth: (equipmentId: string) => EquipmentHealth | undefined;
  getDiagnostic: (tagId: string) => Promise<string>;
} => {
  const {
    tagIds = [],
    equipmentIds = [],
    refreshInterval = 2000,
    enableAnomalyDetection = true,
    enablePredictions = false,
    alertThresholds = {}
  } = options;

  const [state, setState] = useState<ProcessHealthState>({
    overallStatus: 'unknown',
    tags: {},
    equipment: {},
    alerts: [],
    kpis: [],
    lastUpdate: null,
    isLoading: true,
    error: null,
    connectionStatus: 'connecting'
  });

  const historyRef = useRef<Record<string, { value: number; timestamp: Date }[]>>({});
  const alertIdCounter = useRef(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);

  // Generate unique alert ID
  const generateAlertId = useCallback(() => {
    alertIdCounter.current++;
    return `alert_${Date.now()}_${alertIdCounter.current}`;
  }, []);

  // Create or update alert
  const createAlert = useCallback((
    type: ProcessAlert['type'],
    severity: AlertSeverity,
    title: string,
    description: string,
    extra?: Partial<ProcessAlert>
  ): ProcessAlert => {
    const alert: ProcessAlert = {
      id: generateAlertId(),
      type,
      severity,
      title,
      description,
      timestamp: new Date(),
      acknowledged: false,
      recommendations: [],
      ...extra
    };
    alert.recommendations = generateRecommendations(alert);
    return alert;
  }, [generateAlertId]);

  // Fetch and process real-time data
  const fetchData = useCallback(async () => {
    try {
      // Get all real-time values from gateway
      const realtimeValues = await gatewayEdgeApi.getAllRealtimeValues();

      if (!isMountedRef.current) return;

      const newTags: Record<string, TagHealth> = {};
      const newAlerts: ProcessAlert[] = [];
      const timestamp = new Date();

      // Process each tag
      Object.entries(realtimeValues).forEach(([tagId, rtValue]) => {
        // Skip if we have specific tagIds and this isn't one
        if (tagIds.length > 0 && !tagIds.includes(tagId)) return;

        const value = typeof rtValue.value === 'number' ? rtValue.value : parseFloat(String(rtValue.value));
        const limits = alertThresholds[tagId];

        // Update history
        if (!historyRef.current[tagId]) {
          historyRef.current[tagId] = [];
        }
        historyRef.current[tagId].push({ value, timestamp });
        // Keep last 100 values
        if (historyRef.current[tagId].length > 100) {
          historyRef.current[tagId] = historyRef.current[tagId].slice(-100);
        }

        const history = historyRef.current[tagId];
        const trend = calculateTrend(history);
        const status = determineTagStatus(value, limits);

        // Create tag health entry
        newTags[tagId] = {
          tagId,
          tagName: tagId,
          currentValue: value,
          status,
          trend: trend.direction,
          trendPercent: trend.percent,
          limits,
          lastUpdate: timestamp,
          history: history.slice(-20) // Last 20 for display
        };

        // Check for threshold alerts
        if (status === 'critical') {
          const threshold = limits?.highHigh !== undefined && value >= limits.highHigh
            ? limits.highHigh
            : limits?.lowLow;
          newAlerts.push(createAlert(
            'threshold',
            'critical',
            `${tagId} em nível crítico`,
            `Valor atual: ${value.toFixed(2)} ${threshold !== undefined ? `(limite: ${threshold})` : ''}`,
            { tagId, value, threshold }
          ));
        } else if (status === 'warning') {
          const threshold = limits?.high !== undefined && value >= limits.high
            ? limits.high
            : limits?.low;
          newAlerts.push(createAlert(
            'threshold',
            'medium',
            `${tagId} em alerta`,
            `Valor atual: ${value.toFixed(2)} ${threshold !== undefined ? `(limite: ${threshold})` : ''}`,
            { tagId, value, threshold }
          ));
        }

        // Anomaly detection
        if (enableAnomalyDetection) {
          const anomaly = detectAnomaly(history, value);
          if (anomaly.isAnomaly) {
            newAlerts.push(createAlert(
              'anomaly',
              anomaly.severity,
              `Anomalia detectada em ${tagId}`,
              anomaly.reason,
              { tagId, value }
            ));
          }
        }

        // Trend alerts (significant changes)
        if (Math.abs(trend.percent) > 15) {
          newAlerts.push(createAlert(
            'trend',
            trend.percent > 20 ? 'high' : 'medium',
            `Tendência acentuada em ${tagId}`,
            `${trend.direction === 'up' ? 'Aumento' : 'Queda'} de ${Math.abs(trend.percent).toFixed(1)}% detectado`,
            { tagId, value }
          ));
        }
      });

      // Calculate overall status
      const tagStatuses = Object.values(newTags).map(t => t.status);
      let overallStatus: HealthStatus = 'healthy';
      if (tagStatuses.includes('critical')) {
        overallStatus = 'critical';
      } else if (tagStatuses.includes('warning')) {
        overallStatus = 'warning';
      } else if (tagStatuses.every(s => s === 'unknown')) {
        overallStatus = 'unknown';
      }

      // Calculate KPIs
      const kpis: ProcessKPI[] = [];

      // Calculate process efficiency if we have flow data
      const flowTags = Object.values(newTags).filter(t =>
        t.tagId.toLowerCase().includes('flow') || t.tagId.toLowerCase().includes('vazao')
      );
      if (flowTags.length > 0) {
        const avgFlow = flowTags.reduce((sum, t) => sum + (t.currentValue || 0), 0) / flowTags.length;
        kpis.push({
          id: 'avg_flow',
          name: 'Vazão Média',
          value: avgFlow,
          unit: 't/h',
          target: 100,
          status: avgFlow < 50 ? 'warning' : 'healthy',
          trend: 'stable',
          trendPercent: 0
        });
      }

      // Temperature average
      const tempTags = Object.values(newTags).filter(t =>
        t.tagId.toLowerCase().includes('temp') || t.tagId.toLowerCase().includes('temperatura')
      );
      if (tempTags.length > 0) {
        const avgTemp = tempTags.reduce((sum, t) => sum + (t.currentValue || 0), 0) / tempTags.length;
        kpis.push({
          id: 'avg_temp',
          name: 'Temperatura Média',
          value: avgTemp,
          unit: '°C',
          max: 80,
          status: avgTemp > 70 ? 'warning' : avgTemp > 80 ? 'critical' : 'healthy',
          trend: 'stable',
          trendPercent: 0
        });
      }

      // Active alerts count as KPI
      kpis.push({
        id: 'active_alerts',
        name: 'Alertas Ativos',
        value: newAlerts.filter(a => a.severity === 'high' || a.severity === 'critical').length,
        unit: '',
        target: 0,
        status: newAlerts.some(a => a.severity === 'critical') ? 'critical' :
                newAlerts.some(a => a.severity === 'high') ? 'warning' : 'healthy',
        trend: 'stable',
        trendPercent: 0
      });

      setState(prev => ({
        ...prev,
        overallStatus,
        tags: newTags,
        alerts: [...newAlerts, ...prev.alerts.filter(a => a.acknowledged)].slice(0, 50),
        kpis,
        lastUpdate: timestamp,
        isLoading: false,
        error: null,
        connectionStatus: 'connected'
      }));

    } catch (error: any) {
      if (isMountedRef.current) {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: error.message || 'Erro ao buscar dados',
          connectionStatus: 'disconnected'
        }));
      }
    }
  }, [tagIds, alertThresholds, enableAnomalyDetection, createAlert]);

  // Manual refresh
  const refresh = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true }));
    await fetchData();
  }, [fetchData]);

  // Acknowledge alert
  const acknowledgeAlert = useCallback((alertId: string) => {
    setState(prev => ({
      ...prev,
      alerts: prev.alerts.map(a =>
        a.id === alertId ? { ...a, acknowledged: true } : a
      )
    }));
  }, []);

  // Clear resolved alerts
  const clearResolvedAlerts = useCallback(() => {
    setState(prev => ({
      ...prev,
      alerts: prev.alerts.filter(a => !a.acknowledged && !a.autoResolved)
    }));
  }, []);

  // Get tag health
  const getTagHealth = useCallback((tagId: string) => {
    return state.tags[tagId];
  }, [state.tags]);

  // Get equipment health
  const getEquipmentHealth = useCallback((equipmentId: string) => {
    return state.equipment[equipmentId];
  }, [state.equipment]);

  // Get AI diagnostic for a tag
  const getDiagnostic = useCallback(async (tagId: string): Promise<string> => {
    try {
      const tagHealth = state.tags[tagId];
      if (!tagHealth) return 'Tag não encontrada';

      const response = await apiClient.post('/api/v1/agent/dashboard/chat', {
        message: `Diagnóstico para ${tagId}: valor atual ${tagHealth.currentValue}, status ${tagHealth.status}, tendência ${tagHealth.trend}`,
      });

      return response.data.response || 'Diagnóstico não disponível';
    } catch {
      return 'Erro ao obter diagnóstico';
    }
  }, [state.tags]);

  // Setup polling
  useEffect(() => {
    isMountedRef.current = true;
    fetchData();

    intervalRef.current = setInterval(fetchData, refreshInterval);

    return () => {
      isMountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  return {
    ...state,
    refresh,
    acknowledgeAlert,
    clearResolvedAlerts,
    getTagHealth,
    getEquipmentHealth,
    getDiagnostic
  };
};

export default useProcessHealth;
