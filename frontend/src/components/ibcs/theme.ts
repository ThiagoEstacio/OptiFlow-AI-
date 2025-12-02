/**
 * 📊 IBCS Theme - International Business Communication Standards
 * ==============================================================
 *
 * Padrões de cores e estilos para gráficos executivos profissionais.
 * Baseado no IBCS (International Business Communication Standards).
 *
 * Princípios IBCS:
 * - Preto/Cinza para dados atuais (AC - Actual)
 * - Contorno/Outline para dados anteriores (PY - Previous Year)
 * - Hachurado para dados de plano/orçamento (PL - Plan/Budget)
 * - Verde para variação positiva
 * - Vermelho para variação negativa
 * - Simplicidade e clareza acima de tudo
 */

// ========================================
// IBCS Color Palette
// ========================================

export const IBCSColors = {
  // Dados Primários
  actual: '#1a1a1a',           // AC - Preto sólido para dados atuais
  actualLight: '#4a4a4a',      // Variação mais clara

  // Dados Comparativos
  previousYear: '#808080',     // PY - Cinza para ano anterior
  previousYearOutline: '#666666', // Contorno para PY

  // Plano/Orçamento
  plan: '#999999',             // PL - Cinza claro com padrão hachurado
  budget: '#b3b3b3',           // BU - Orçamento
  forecast: '#cccccc',         // FC - Previsão

  // Variações
  positive: '#2E7D32',         // Verde escuro para positivo
  positiveLight: '#4CAF50',    // Verde claro
  negative: '#C62828',         // Vermelho escuro para negativo
  negativeLight: '#EF5350',    // Vermelho claro
  neutral: '#757575',          // Neutro/Sem variação

  // Elementos auxiliares
  gridLine: '#e0e0e0',
  axisLine: '#333333',
  labelText: '#333333',
  labelSecondary: '#666666',
  background: '#ffffff',
  highlight: '#FFF3E0',        // Destaque suave

  // Alertas (para alarmes/KPIs críticos)
  critical: '#B71C1C',
  warning: '#F57C00',
  good: '#388E3C',
} as const;

// ========================================
// IBCS Typography
// ========================================

export const IBCSTypography = {
  // Títulos
  title: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    fontSize: 16,
    fontWeight: 600,
    color: IBCSColors.labelText,
  },
  subtitle: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    fontSize: 12,
    fontWeight: 400,
    color: IBCSColors.labelSecondary,
  },

  // Valores
  value: {
    fontFamily: '"Roboto Mono", "Consolas", monospace',
    fontSize: 14,
    fontWeight: 600,
    color: IBCSColors.labelText,
  },
  valueSmall: {
    fontFamily: '"Roboto Mono", "Consolas", monospace',
    fontSize: 11,
    fontWeight: 500,
    color: IBCSColors.labelSecondary,
  },

  // Labels de eixos
  axisLabel: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    fontSize: 11,
    fontWeight: 400,
    color: IBCSColors.labelSecondary,
  },

  // Variações
  variance: {
    fontFamily: '"Roboto Mono", "Consolas", monospace',
    fontSize: 11,
    fontWeight: 600,
  },
} as const;

// ========================================
// IBCS Patterns (para hatching)
// ========================================

export const IBCSPatterns = {
  // SVG pattern para hachurado diagonal (Plan/Budget)
  diagonalHatch: `
    <pattern id="ibcs-hatch-plan" patternUnits="userSpaceOnUse" width="4" height="4">
      <path d="M-1,1 l2,-2 M0,4 l4,-4 M3,5 l2,-2"
            style="stroke:#666666; stroke-width:1"/>
    </pattern>
  `,

  // Padrão para Previous Year (outline)
  outline: {
    fill: 'none',
    stroke: IBCSColors.previousYearOutline,
    strokeWidth: 2,
  },

  // Padrão para Forecast (pontilhado)
  dotted: {
    strokeDasharray: '2,2',
  },
} as const;

// ========================================
// IBCS Chart Defaults
// ========================================

export const IBCSChartDefaults = {
  // Margens padrão
  margin: {
    top: 20,
    right: 30,
    bottom: 40,
    left: 60,
  },

  // Grid
  grid: {
    stroke: IBCSColors.gridLine,
    strokeDasharray: '3 3',
    horizontal: true,
    vertical: false,
  },

  // Eixos
  axis: {
    stroke: IBCSColors.axisLine,
    tickLine: false,
    axisLine: true,
  },

  // Tooltip
  tooltip: {
    backgroundColor: IBCSColors.background,
    border: `1px solid ${IBCSColors.gridLine}`,
    borderRadius: 4,
    boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
  },

  // Animação
  animation: {
    duration: 300,
    easing: 'ease-out',
  },
} as const;

// ========================================
// Utility Functions
// ========================================

/**
 * Retorna a cor apropriada para uma variação
 */
export const getVarianceColor = (variance: number): string => {
  if (variance > 0) return IBCSColors.positive;
  if (variance < 0) return IBCSColors.negative;
  return IBCSColors.neutral;
};

/**
 * Formata variação com sinal e símbolo
 */
export const formatVariance = (
  variance: number,
  format: 'percent' | 'absolute' | 'currency' = 'percent'
): string => {
  const sign = variance > 0 ? '+' : '';

  switch (format) {
    case 'percent':
      return `${sign}${variance.toFixed(1)}%`;
    case 'absolute':
      return `${sign}${variance.toLocaleString('pt-BR')}`;
    case 'currency':
      return `${sign}${variance.toLocaleString('pt-BR', {
        style: 'currency',
        currency: 'BRL',
      })}`;
    default:
      return `${sign}${variance}`;
  }
};

/**
 * Formata número para exibição IBCS (compacto)
 */
export const formatIBCSNumber = (
  value: number,
  options: {
    decimals?: number;
    compact?: boolean;
    unit?: string;
  } = {}
): string => {
  const { decimals = 1, compact = true, unit = '' } = options;

  if (compact && Math.abs(value) >= 1000000) {
    return `${(value / 1000000).toFixed(decimals)}M${unit}`;
  }
  if (compact && Math.abs(value) >= 1000) {
    return `${(value / 1000).toFixed(decimals)}k${unit}`;
  }

  return `${value.toFixed(decimals)}${unit}`;
};

/**
 * Gera ID único para patterns SVG
 */
export const generatePatternId = (prefix: string): string => {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
};

// ========================================
// IBCS Data Types
// ========================================

export interface IBCSDataPoint {
  label: string;
  actual: number;
  plan?: number;
  previousYear?: number;
  forecast?: number;
  variance?: number;
  variancePercent?: number;
}

export interface IBCSChartProps {
  data: IBCSDataPoint[];
  title?: string;
  subtitle?: string;
  unit?: string;
  height?: number;
  showVariance?: boolean;
  showLegend?: boolean;
  highlightNegative?: boolean;
}

export default {
  colors: IBCSColors,
  typography: IBCSTypography,
  patterns: IBCSPatterns,
  defaults: IBCSChartDefaults,
  getVarianceColor,
  formatVariance,
  formatIBCSNumber,
};
