/**
 * 📊 IBCS Components - International Business Communication Standards
 * ===================================================================
 *
 * Biblioteca de componentes de visualização seguindo padrões IBCS.
 *
 * Componentes:
 * - IBCSBarChart: Gráfico de barras com comparativo AC/PY/PL
 * - IBCSLineChart: Gráfico de linhas temporal
 * - IBCSWaterfallChart: Gráfico waterfall/bridge
 * - IBCSKPICard: Card de KPI profissional
 *
 * Padrões IBCS implementados:
 * - Preto para dados atuais (AC)
 * - Cinza/outline para ano anterior (PY)
 * - Hachurado para plano (PL)
 * - Verde para variação positiva
 * - Vermelho para variação negativa
 */

// Theme and utilities
export {
  IBCSColors,
  IBCSTypography,
  IBCSPatterns,
  IBCSChartDefaults,
  getVarianceColor,
  formatVariance,
  formatIBCSNumber,
  generatePatternId,
} from './theme';

export type { IBCSDataPoint, IBCSChartProps } from './theme';

// Chart components
export { IBCSBarChart } from './IBCSBarChart';
export { IBCSLineChart } from './IBCSLineChart';
export type { IBCSTimeSeriesPoint } from './IBCSLineChart';
export { IBCSWaterfallChart } from './IBCSWaterfallChart';
export { IBCSKPICard, IBCSKPIGrid } from './IBCSKPICard';
