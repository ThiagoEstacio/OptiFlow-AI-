/**
 * 📊 Charts Components - Advanced Visualization
 * ==============================================
 *
 * Componentes de gráficos avançados para dashboards industriais.
 */

export { HybridTimeline } from './HybridTimeline';
export type {
  TimelineDataPoint,
  TimelineEvent,
  HybridTimelineProps,
} from './HybridTimeline';

export { HighPerformanceTrend } from './HighPerformanceTrend';
export type {
  TrendDataPoint,
  TrendSeries,
  HighPerformanceTrendProps,
} from './HighPerformanceTrend';

// Existing charts
export { default as MultiSeriesChart } from './MultiSeriesChart';
export { default as TimeSeriesChart } from './TimeSeriesChart';
