/**
 * Application Constants
 * =====================
 * Centralized configuration for the OptiFlow application
 */

// Refresh intervals in milliseconds
export const REFRESH_INTERVALS = {
  REALTIME: 2000,        // 2 seconds - for real-time data streams
  ALARMS: 5000,          // 5 seconds - for critical alarm updates
  FAST: 10000,           // 10 seconds - for frequently changing data
  MEDIUM: 20000,         // 20 seconds - for medium-frequency updates
  DASHBOARD: 30000,      // 30 seconds - for dashboard updates
  SLOW: 45000,           // 45 seconds - for slower updates
  ANALYTICS: 60000,      // 1 minute - for analytics data
  REPORTS: 300000,       // 5 minutes - for reports and slow-changing data
} as const;

// Time range options for historical data
export const TIME_RANGES = [
  { label: '15 min', value: 15, unit: 'minutes' as const },
  { label: '30 min', value: 30, unit: 'minutes' as const },
  { label: '1 hora', value: 1, unit: 'hours' as const },
  { label: '6 horas', value: 6, unit: 'hours' as const },
  { label: '12 horas', value: 12, unit: 'hours' as const },
  { label: '24 horas', value: 24, unit: 'hours' as const },
  { label: '7 dias', value: 7, unit: 'days' as const },
  { label: '30 dias', value: 30, unit: 'days' as const },
] as const;

// Severity levels
export const SEVERITY_LEVELS = {
  CRITICAL: 'critical',
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low',
  INFO: 'info',
} as const;

export type SeverityLevel = typeof SEVERITY_LEVELS[keyof typeof SEVERITY_LEVELS];

// Health/Status levels
export const HEALTH_STATUS = {
  HEALTHY: 'healthy',
  WARNING: 'warning',
  CRITICAL: 'critical',
  UNKNOWN: 'unknown',
  DEGRADED: 'degraded',
} as const;

export type HealthStatus = typeof HEALTH_STATUS[keyof typeof HEALTH_STATUS];

// Trend indicators
export const TREND_DIRECTION = {
  UP: 'up',
  DOWN: 'down',
  STABLE: 'stable',
} as const;

export type TrendDirection = typeof TREND_DIRECTION[keyof typeof TREND_DIRECTION];

// API Endpoints base paths
export const API_PATHS = {
  ALARMS: '/api/v1/alarms',
  ANALYTICS: '/api/v1/analytics',
  TAGS: '/api/v1/tags',
  REPORTS: '/api/v1/reports',
  DASHBOARD: '/api/v1/dashboard',
  INSIGHTS: '/api/v1/insights',
  GATEWAY: '/api/v1/gateway',
} as const;

// Chart configurations
export const CHART_DEFAULTS = {
  ANIMATION_DURATION: 300,
  MAX_DATA_POINTS: 100,
  GRID_COLOR: '#e5e7eb',
  AXIS_COLOR: '#9ca3af',
} as const;

// Pagination defaults
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [10, 25, 50, 100] as const,
} as const;

// WebSocket configuration
export const WEBSOCKET = {
  RECONNECT_DELAY: 3000,
  MAX_RECONNECT_ATTEMPTS: 5,
  PING_INTERVAL: 30000,
} as const;
