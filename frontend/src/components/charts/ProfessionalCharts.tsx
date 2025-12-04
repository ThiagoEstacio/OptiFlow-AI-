/**
 * Professional Chart Components - Enterprise Quality v2.0
 * ========================================================
 *
 * Componentes de gráficos profissionais usando Recharts + Tailwind
 *
 * v2.0 Improvements:
 * - Colorblind-safe palette with pattern support
 * - Unit formatters for Y-axis
 * - Enhanced accessibility with ARIA labels
 * - ISA-101 compliant color coding
 */
import React, { useMemo, useId } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
  ReferenceLine,
} from 'recharts';
import { TrendingUp, TrendingDown, Minus, MoreVertical, Download, Maximize2, RefreshCw, AlertCircle } from 'lucide-react';

// ============================================
// COLORBLIND-SAFE PALETTE (ISA-101 Compliant)
// ============================================
// Using colors distinguishable by people with color vision deficiency
export const COLORBLIND_SAFE_PALETTE = {
  // Primary colors - distinguishable in all color blindness types
  blue: '#0077BB',      // Safe blue
  orange: '#EE7733',    // Safe orange (visible in protanopia/deuteranopia)
  cyan: '#33BBEE',      // Safe cyan
  magenta: '#EE3377',   // Safe magenta
  yellow: '#CCBB44',    // Safe yellow (distinct from orange)
  teal: '#009988',      // Safe teal
  gray: '#BBBBBB',      // Neutral gray
  black: '#000000',     // Black for contrast
};

// ISA-101 Status Colors (with high contrast)
export const ISA101_COLORS = {
  normal: '#2E7D32',    // Green - Normal operation
  warning: '#ED6C02',   // Orange - Warning
  critical: '#D32F2F',  // Red - Critical/Alarm
  info: '#0288D1',      // Blue - Information
  inactive: '#9E9E9E',  // Gray - Inactive/Unknown
};

// Chart color array (colorblind-safe)
export const CHART_COLORS = [
  COLORBLIND_SAFE_PALETTE.blue,
  COLORBLIND_SAFE_PALETTE.orange,
  COLORBLIND_SAFE_PALETTE.teal,
  COLORBLIND_SAFE_PALETTE.magenta,
  COLORBLIND_SAFE_PALETTE.cyan,
  COLORBLIND_SAFE_PALETTE.yellow,
  COLORBLIND_SAFE_PALETTE.gray,
];

// Pattern definitions for additional differentiation
export const CHART_PATTERNS = [
  'solid',
  'dashed',
  'dotted',
  'dashdot',
];

// ============================================
// UNIT FORMATTERS
// ============================================
export type UnitType = 'temperature' | 'pressure' | 'flow' | 'percent' | 'power' | 'current' | 'voltage' | 'speed' | 'count' | 'currency' | 'none';

export const formatValueWithUnit = (value: number, unit: UnitType): string => {
  const formatters: Record<UnitType, (v: number) => string> = {
    temperature: (v) => `${v.toFixed(1)} °C`,
    pressure: (v) => `${v.toFixed(2)} bar`,
    flow: (v) => `${v.toFixed(1)} m³/h`,
    percent: (v) => `${v.toFixed(1)}%`,
    power: (v) => v >= 1000 ? `${(v / 1000).toFixed(2)} MW` : `${v.toFixed(1)} kW`,
    current: (v) => `${v.toFixed(1)} A`,
    voltage: (v) => `${v.toFixed(0)} V`,
    speed: (v) => `${v.toFixed(0)} rpm`,
    count: (v) => v.toLocaleString('pt-BR'),
    currency: (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v),
    none: (v) => v.toLocaleString('pt-BR'),
  };
  return formatters[unit](value);
};

export const getUnitLabel = (unit: UnitType): string => {
  const labels: Record<UnitType, string> = {
    temperature: '°C',
    pressure: 'bar',
    flow: 'm³/h',
    percent: '%',
    power: 'kW',
    current: 'A',
    voltage: 'V',
    speed: 'rpm',
    count: '',
    currency: 'R$',
    none: '',
  };
  return labels[unit];
};

// ============================================
// CUSTOM TOOLTIP (Enhanced)
// ============================================
interface EnhancedTooltipProps extends TooltipProps<number, string> {
  unit?: UnitType;
}

const CustomTooltip: React.FC<EnhancedTooltipProps> = ({ active, payload, label, unit = 'none' }) => {
  if (!active || !payload || !payload.length) return null;

  return (
    <div
      className="bg-white/95 backdrop-blur-sm border border-slate-200 rounded-lg shadow-lg p-3 min-w-[160px]"
      role="tooltip"
      aria-live="polite"
    >
      <p className="text-sm font-semibold text-slate-800 mb-2 border-b border-slate-100 pb-1">{label}</p>
      {payload.map((entry, index) => (
        <div key={index} className="flex items-center justify-between gap-4 text-sm py-0.5">
          <div className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-sm border border-slate-300"
              style={{ backgroundColor: entry.color }}
              aria-hidden="true"
            />
            <span className="text-slate-600">{entry.name}</span>
          </div>
          <span className="font-semibold text-slate-800">
            {typeof entry.value === 'number'
              ? formatValueWithUnit(entry.value, unit)
              : entry.value
            }
          </span>
        </div>
      ))}
    </div>
  );
};

// ============================================
// SVG PATTERN DEFINITIONS
// ============================================
const PatternDefinitions: React.FC<{ id: string }> = ({ id }) => (
  <defs>
    <pattern id={`${id}-stripe`} patternUnits="userSpaceOnUse" width="4" height="4" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="4" stroke="currentColor" strokeWidth="2" />
    </pattern>
    <pattern id={`${id}-dots`} patternUnits="userSpaceOnUse" width="6" height="6">
      <circle cx="3" cy="3" r="1.5" fill="currentColor" />
    </pattern>
    <pattern id={`${id}-crosshatch`} patternUnits="userSpaceOnUse" width="8" height="8">
      <path d="M0,0 L8,8 M8,0 L0,8" stroke="currentColor" strokeWidth="1" />
    </pattern>
  </defs>
);

// ============================================
// CARD WRAPPER (Enhanced)
// ============================================
interface ChartCardProps {
  title: string;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  children: React.ReactNode;
  onRefresh?: () => void;
  onDownload?: () => void;
  onFullscreen?: () => void;
  className?: string;
  lastUpdated?: Date;
  isDemo?: boolean;
}

export const ChartCard: React.FC<ChartCardProps> = ({
  title,
  subtitle,
  trend,
  trendValue,
  children,
  onRefresh,
  onDownload,
  onFullscreen,
  className = '',
  lastUpdated,
  isDemo = false,
}) => {
  const [menuOpen, setMenuOpen] = React.useState(false);

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor = trend === 'up' ? 'text-emerald-600 bg-emerald-50' :
                     trend === 'down' ? 'text-red-600 bg-red-50' :
                     'text-slate-500 bg-slate-50';

  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow ${className}`}
      role="region"
      aria-label={title}
    >
      {/* Header */}
      <div className="flex items-start justify-between p-4 pb-2">
        <div className="flex items-start gap-3">
          {trend && (
            <div className={`p-2 rounded-lg ${trendColor}`} aria-hidden="true">
              <TrendIcon className="w-5 h-5" />
            </div>
          )}
          <div>
            <h3 className="text-base font-semibold text-slate-800">{title}</h3>
            <div className="flex items-center gap-2 mt-0.5 flex-wrap">
              {subtitle && <span className="text-sm text-slate-500">{subtitle}</span>}
              {trendValue && (
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${trendColor}`}>
                  {trendValue}
                </span>
              )}
              {lastUpdated && (
                <span className="text-xs text-slate-400">
                  Atualizado: {lastUpdated.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
              {isDemo && (
                <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  Demo
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Actions Menu */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
            aria-label="Opções do gráfico"
            aria-expanded={menuOpen}
          >
            <MoreVertical className="w-5 h-5" aria-hidden="true" />
          </button>

          {menuOpen && (
            <div className="absolute right-0 top-full mt-1 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-10 min-w-[140px]">
              {onRefresh && (
                <button
                  onClick={() => { onRefresh(); setMenuOpen(false); }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 focus-visible:bg-slate-50"
                >
                  <RefreshCw className="w-4 h-4" aria-hidden="true" /> Atualizar
                </button>
              )}
              {onDownload && (
                <button
                  onClick={() => { onDownload(); setMenuOpen(false); }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 focus-visible:bg-slate-50"
                >
                  <Download className="w-4 h-4" aria-hidden="true" /> Download
                </button>
              )}
              {onFullscreen && (
                <button
                  onClick={() => { onFullscreen(); setMenuOpen(false); }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 focus-visible:bg-slate-50"
                >
                  <Maximize2 className="w-4 h-4" aria-hidden="true" /> Tela cheia
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Chart Content */}
      <div className="px-4 pb-4">
        {children}
      </div>
    </div>
  );
};

// ============================================
// PROFESSIONAL DONUT CHART
// ============================================
interface DonutChartData {
  name: string;
  value: number;
  color?: string;
}

interface ProfessionalDonutChartProps {
  data: DonutChartData[];
  colors?: string[];
  height?: number;
  innerRadius?: number;
  outerRadius?: number;
  showLabels?: boolean;
  showLegend?: boolean;
  title?: string;
  subtitle?: string;
  unit?: UnitType;
}

export const ProfessionalDonutChart: React.FC<ProfessionalDonutChartProps> = ({
  data,
  colors = CHART_COLORS,
  height = 220,
  innerRadius = 60,
  outerRadius = 90,
  showLabels = false,
  showLegend = true,
  unit = 'none',
}) => {
  const chartId = useId();
  const total = useMemo(() => data.reduce((sum, item) => sum + item.value, 0), [data]);

  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
    if (!showLabels || percent < 0.05) return null;
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 1.4;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text
        x={x}
        y={y}
        fill="#475569"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        className="text-xs font-medium"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <div role="img" aria-label={`Gráfico de rosca mostrando ${data.length} categorias`}>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <PatternDefinitions id={chartId} />
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            paddingAngle={2}
            dataKey="value"
            label={showLabels ? renderCustomLabel : undefined}
            labelLine={false}
            animationDuration={800}
            animationBegin={0}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color || colors[index % colors.length]}
                stroke="white"
                strokeWidth={2}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip unit={unit} />} />
        </PieChart>
      </ResponsiveContainer>

      {/* Accessible Legend */}
      {showLegend && (
        <div className="flex flex-wrap justify-center gap-4 mt-3" role="list" aria-label="Legenda">
          {data.map((item, idx) => (
            <div key={item.name} className="flex items-center gap-2" role="listitem">
              <div
                className="w-3 h-3 rounded-sm border border-slate-300"
                style={{ backgroundColor: item.color || colors[idx % colors.length] }}
                aria-hidden="true"
              />
              <span className="text-sm text-slate-600">
                {item.name}: <span className="font-semibold">{formatValueWithUnit(item.value, unit)}</span>
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ============================================
// PROFESSIONAL BAR CHART (Enhanced)
// ============================================
interface BarChartData {
  [key: string]: string | number;
}

interface ProfessionalBarChartProps {
  data: BarChartData[];
  xAxisKey: string;
  categories: string[];
  colors?: string[];
  height?: number;
  stacked?: boolean;
  showGrid?: boolean;
  showLegend?: boolean;
  unit?: UnitType;
  yAxisLabel?: string;
}

export const ProfessionalBarChart: React.FC<ProfessionalBarChartProps> = ({
  data,
  xAxisKey,
  categories,
  colors = CHART_COLORS,
  height = 220,
  stacked = false,
  showGrid = true,
  showLegend = true,
  unit = 'none',
  yAxisLabel,
}) => {
  const unitLabel = yAxisLabel || getUnitLabel(unit);

  return (
    <div role="img" aria-label={`Gráfico de barras com ${categories.length} categorias`}>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 10, right: 10, left: unitLabel ? 20 : 0, bottom: 0 }}>
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e2e8f0"
              vertical={false}
            />
          )}
          <XAxis
            dataKey={xAxisKey}
            tick={{ fontSize: 12, fill: '#475569' }}
            stroke="#e2e8f0"
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#475569' }}
            stroke="#e2e8f0"
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
            tickFormatter={(value) => formatValueWithUnit(value, unit)}
            label={unitLabel ? { value: unitLabel, angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#64748b', fontSize: 11 } } : undefined}
          />
          <Tooltip content={<CustomTooltip unit={unit} />} />
          {showLegend && (
            <Legend
              wrapperStyle={{ paddingTop: 16 }}
              formatter={(value) => <span className="text-sm text-slate-600">{value}</span>}
            />
          )}
          {categories.map((category, index) => (
            <Bar
              key={category}
              dataKey={category}
              fill={colors[index % colors.length]}
              stackId={stacked ? 'stack' : undefined}
              radius={stacked ? (index === categories.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]) : [4, 4, 0, 0]}
              animationDuration={800}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

// ============================================
// PROFESSIONAL AREA CHART (Enhanced)
// ============================================
interface AreaChartData {
  [key: string]: string | number;
}

interface ProfessionalAreaChartProps {
  data: AreaChartData[];
  xAxisKey: string;
  dataKey: string;
  color?: string;
  height?: number;
  showGrid?: boolean;
  gradientOpacity?: number;
  unit?: UnitType;
  yAxisLabel?: string;
  referenceLines?: Array<{ y: number; label: string; color: string }>;
}

export const ProfessionalAreaChart: React.FC<ProfessionalAreaChartProps> = ({
  data,
  xAxisKey,
  dataKey,
  color = COLORBLIND_SAFE_PALETTE.blue,
  height = 220,
  showGrid = true,
  gradientOpacity = 0.3,
  unit = 'none',
  yAxisLabel,
  referenceLines = [],
}) => {
  const chartId = useId();
  const gradientId = `gradient-${chartId}`;
  const unitLabel = yAxisLabel || getUnitLabel(unit);

  return (
    <div role="img" aria-label={`Gráfico de área mostrando ${dataKey}`}>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: unitLabel ? 20 : 0, bottom: 0 }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={gradientOpacity} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e2e8f0"
              vertical={false}
            />
          )}
          <XAxis
            dataKey={xAxisKey}
            tick={{ fontSize: 12, fill: '#475569' }}
            stroke="#e2e8f0"
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#475569' }}
            stroke="#e2e8f0"
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
            tickFormatter={(value) => formatValueWithUnit(value, unit)}
            label={unitLabel ? { value: unitLabel, angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#64748b', fontSize: 11 } } : undefined}
          />
          <Tooltip content={<CustomTooltip unit={unit} />} />

          {/* Reference lines for limits/targets */}
          {referenceLines.map((ref, idx) => (
            <ReferenceLine
              key={idx}
              y={ref.y}
              stroke={ref.color}
              strokeDasharray="5 5"
              label={{ value: ref.label, fill: ref.color, fontSize: 10, position: 'right' }}
            />
          ))}

          <Area
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            strokeWidth={2}
            fill={`url(#${gradientId})`}
            animationDuration={800}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

// ============================================
// PROFESSIONAL LINE CHART (Enhanced with patterns)
// ============================================
interface LineChartData {
  [key: string]: string | number;
}

interface LineConfig {
  dataKey: string;
  color?: string;
  name?: string;
  strokeWidth?: number;
  dot?: boolean;
  strokeDasharray?: string;
}

interface ProfessionalLineChartProps {
  data: LineChartData[];
  xAxisKey: string;
  lines: LineConfig[];
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
  unit?: UnitType;
  yAxisLabel?: string;
  referenceLines?: Array<{ y: number; label: string; color: string }>;
}

// Stroke patterns for colorblind accessibility
const STROKE_PATTERNS = ['0', '5 5', '2 2', '10 5 2 5'];

export const ProfessionalLineChart: React.FC<ProfessionalLineChartProps> = ({
  data,
  xAxisKey,
  lines,
  height = 220,
  showGrid = true,
  showLegend = true,
  unit = 'none',
  yAxisLabel,
  referenceLines = [],
}) => {
  const unitLabel = yAxisLabel || getUnitLabel(unit);

  return (
    <div role="img" aria-label={`Gráfico de linhas com ${lines.length} séries`}>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 10, right: 10, left: unitLabel ? 20 : 0, bottom: 0 }}>
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e2e8f0"
              vertical={false}
            />
          )}
          <XAxis
            dataKey={xAxisKey}
            tick={{ fontSize: 12, fill: '#475569' }}
            stroke="#e2e8f0"
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#475569' }}
            stroke="#e2e8f0"
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
            tickFormatter={(value) => formatValueWithUnit(value, unit)}
            label={unitLabel ? { value: unitLabel, angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#64748b', fontSize: 11 } } : undefined}
          />
          <Tooltip content={<CustomTooltip unit={unit} />} />

          {showLegend && (
            <Legend
              wrapperStyle={{ paddingTop: 16 }}
              formatter={(value, entry) => {
                const lineIndex = lines.findIndex(l => l.name === value || l.dataKey === value);
                const pattern = STROKE_PATTERNS[lineIndex % STROKE_PATTERNS.length];
                return (
                  <span className="text-sm text-slate-600 inline-flex items-center gap-1">
                    {pattern !== '0' && <span className="text-xs text-slate-400">({pattern === '5 5' ? '- -' : pattern === '2 2' ? '...' : '-.'})</span>}
                    {value}
                  </span>
                );
              }}
            />
          )}

          {/* Reference lines */}
          {referenceLines.map((ref, idx) => (
            <ReferenceLine
              key={idx}
              y={ref.y}
              stroke={ref.color}
              strokeDasharray="5 5"
              label={{ value: ref.label, fill: ref.color, fontSize: 10, position: 'right' }}
            />
          ))}

          {lines.map((line, index) => (
            <Line
              key={line.dataKey}
              type="monotone"
              dataKey={line.dataKey}
              name={line.name || line.dataKey}
              stroke={line.color || CHART_COLORS[index % CHART_COLORS.length]}
              strokeWidth={line.strokeWidth || 2}
              strokeDasharray={line.strokeDasharray || STROKE_PATTERNS[index % STROKE_PATTERNS.length]}
              dot={line.dot ?? false}
              animationDuration={800}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

// ============================================
// PROFESSIONAL MULTI-SERIES BAR CHART
// ============================================
interface MultiBarChartProps {
  data: BarChartData[];
  xAxisKey: string;
  bars: Array<{
    dataKey: string;
    name?: string;
    color?: string;
  }>;
  height?: number;
  stacked?: boolean;
  showGrid?: boolean;
  showLegend?: boolean;
  unit?: UnitType;
  yAxisLabel?: string;
}

export const ProfessionalMultiBarChart: React.FC<MultiBarChartProps> = ({
  data,
  xAxisKey,
  bars,
  height = 220,
  stacked = false,
  showGrid = true,
  showLegend = true,
  unit = 'none',
  yAxisLabel,
}) => {
  const unitLabel = yAxisLabel || getUnitLabel(unit);

  return (
    <div role="img" aria-label={`Gráfico de barras múltiplas com ${bars.length} séries`}>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 10, right: 10, left: unitLabel ? 20 : 0, bottom: 0 }}>
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e2e8f0"
              vertical={false}
            />
          )}
          <XAxis
            dataKey={xAxisKey}
            tick={{ fontSize: 12, fill: '#475569' }}
            stroke="#e2e8f0"
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#475569' }}
            stroke="#e2e8f0"
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
            tickFormatter={(value) => formatValueWithUnit(value, unit)}
            label={unitLabel ? { value: unitLabel, angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#64748b', fontSize: 11 } } : undefined}
          />
          <Tooltip content={<CustomTooltip unit={unit} />} />
          {showLegend && (
            <Legend
              wrapperStyle={{ paddingTop: 16 }}
              formatter={(value) => <span className="text-sm text-slate-600">{value}</span>}
            />
          )}
          {bars.map((bar, index) => (
            <Bar
              key={bar.dataKey}
              dataKey={bar.dataKey}
              name={bar.name || bar.dataKey}
              fill={bar.color || CHART_COLORS[index % CHART_COLORS.length]}
              stackId={stacked ? 'stack' : undefined}
              radius={[4, 4, 0, 0]}
              animationDuration={800}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

// ============================================
// PROFESSIONAL PREDICTION CHART
// ============================================
interface PredictionChartData {
  [key: string]: string | number | null;
}

interface ProfessionalPredictionChartProps {
  data: PredictionChartData[];
  xAxisKey: string;
  actualDataKey: string;
  predictionDataKey: string;
  upperBoundKey?: string;
  lowerBoundKey?: string;
  actualColor?: string;
  predictionColor?: string;
  bandColor?: string;
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
  unit?: UnitType;
  yAxisLabel?: string;
}

export const ProfessionalPredictionChart: React.FC<ProfessionalPredictionChartProps> = ({
  data,
  xAxisKey,
  actualDataKey,
  predictionDataKey,
  upperBoundKey,
  lowerBoundKey,
  actualColor = COLORBLIND_SAFE_PALETTE.blue,
  predictionColor = COLORBLIND_SAFE_PALETTE.orange,
  bandColor = COLORBLIND_SAFE_PALETTE.orange,
  height = 320,
  showGrid = true,
  showLegend = true,
  unit = 'none',
  yAxisLabel,
}) => {
  const chartId = useId();
  const actualGradientId = `${chartId}-actual`;
  const predictionGradientId = `${chartId}-pred`;
  const bandGradientId = `${chartId}-band`;
  const unitLabel = yAxisLabel || getUnitLabel(unit);

  return (
    <div role="img" aria-label="Gráfico de predição com valor real e previsão ML">
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 10, right: 30, left: unitLabel ? 20 : 0, bottom: 0 }}>
          <defs>
            <linearGradient id={actualGradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={actualColor} stopOpacity={0.3} />
              <stop offset="95%" stopColor={actualColor} stopOpacity={0} />
            </linearGradient>
            <linearGradient id={predictionGradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={predictionColor} stopOpacity={0.3} />
              <stop offset="95%" stopColor={predictionColor} stopOpacity={0} />
            </linearGradient>
            <linearGradient id={bandGradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={bandColor} stopOpacity={0.15} />
              <stop offset="95%" stopColor={bandColor} stopOpacity={0.05} />
            </linearGradient>
          </defs>
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e2e8f0"
              vertical={false}
            />
          )}
          <XAxis
            dataKey={xAxisKey}
            tick={{ fontSize: 11, fill: '#475569' }}
            stroke="#e2e8f0"
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
            interval="preserveStartEnd"
            minTickGap={50}
          />
          <YAxis
            tick={{ fontSize: 11, fill: '#475569' }}
            stroke="#e2e8f0"
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
            domain={['dataMin - 5', 'dataMax + 5']}
            tickFormatter={(value) => formatValueWithUnit(value, unit)}
            label={unitLabel ? { value: unitLabel, angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#64748b', fontSize: 11 } } : undefined}
          />
          <Tooltip content={<CustomTooltip unit={unit} />} />
          {showLegend && (
            <Legend
              wrapperStyle={{ paddingTop: 16 }}
              formatter={(value) => <span className="text-sm text-slate-600">{value}</span>}
            />
          )}

          {/* Confidence band (Upper) */}
          {upperBoundKey && (
            <Area
              type="monotone"
              dataKey={upperBoundKey}
              name="Limite Superior"
              stroke="transparent"
              fill={`url(#${bandGradientId})`}
              strokeWidth={0}
              animationDuration={800}
              connectNulls={false}
            />
          )}

          {/* Confidence band (Lower) */}
          {lowerBoundKey && (
            <Area
              type="monotone"
              dataKey={lowerBoundKey}
              name="Limite Inferior"
              stroke={bandColor}
              strokeWidth={1}
              strokeDasharray="4 4"
              strokeOpacity={0.5}
              fill="transparent"
              animationDuration={800}
              connectNulls={false}
            />
          )}

          {/* Actual data - solid line */}
          <Area
            type="monotone"
            dataKey={actualDataKey}
            name="Valor Real"
            stroke={actualColor}
            strokeWidth={2}
            fill={`url(#${actualGradientId})`}
            animationDuration={800}
            connectNulls={false}
            dot={{ fill: actualColor, r: 2 }}
          />

          {/* Prediction line - dashed for colorblind differentiation */}
          <Area
            type="monotone"
            dataKey={predictionDataKey}
            name="Predição ML"
            stroke={predictionColor}
            strokeWidth={2.5}
            strokeDasharray="5 5"
            fill={`url(#${predictionGradientId})`}
            animationDuration={800}
            connectNulls={true}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

// ============================================
// PROFESSIONAL SPARK CHART
// ============================================
interface SparkChartData {
  value: number;
  [key: string]: number;
}

interface ProfessionalSparkChartProps {
  data: SparkChartData[];
  dataKey?: string;
  color?: string;
  height?: number;
  width?: number;
  className?: string;
}

export const ProfessionalSparkChart: React.FC<ProfessionalSparkChartProps> = ({
  data,
  dataKey = 'value',
  color = COLORBLIND_SAFE_PALETTE.blue,
  height = 40,
  width = 96,
  className = '',
}) => {
  const chartId = useId();
  const gradientId = `spark-${chartId}`;

  return (
    <div className={className} style={{ width, height }} role="img" aria-label="Mini gráfico de tendência">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.4} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            strokeWidth={1.5}
            fill={`url(#${gradientId})`}
            animationDuration={500}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

// ============================================
// PROFESSIONAL RADIAL GAUGE
// ============================================
interface RadialGaugeProps {
  value: number;
  min?: number;
  max?: number;
  target?: number;
  label?: string;
  unit?: string;
  size?: number;
  thickness?: number;
  showTicks?: boolean;
  zones?: Array<{ from: number; to: number; color: string }>;
  className?: string;
}

export const ProfessionalRadialGauge: React.FC<RadialGaugeProps> = ({
  value,
  min = 0,
  max = 100,
  target,
  label,
  unit = '%',
  size = 180,
  thickness = 20,
  showTicks = true,
  zones,
  className = '',
}) => {
  const chartId = useId();

  // Calculate percentage and angle
  const percentage = Math.min(Math.max((value - min) / (max - min), 0), 1);
  const startAngle = -135;
  const endAngle = 135;
  const totalAngle = endAngle - startAngle;
  const currentAngle = startAngle + (percentage * totalAngle);

  // SVG calculations
  const center = size / 2;
  const radius = (size - thickness) / 2 - 10;
  const innerRadius = radius - thickness;

  // Convert angle to radians and calculate path
  const polarToCartesian = (angle: number, r: number) => {
    const rad = (angle * Math.PI) / 180;
    return {
      x: center + r * Math.cos(rad),
      y: center + r * Math.sin(rad),
    };
  };

  // Arc path helper
  const describeArc = (startAng: number, endAng: number, r: number) => {
    const start = polarToCartesian(startAng, r);
    const end = polarToCartesian(endAng, r);
    const largeArcFlag = endAng - startAng <= 180 ? 0 : 1;
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArcFlag} 1 ${end.x} ${end.y}`;
  };

  // Get color based on value and zones
  const getValueColor = () => {
    if (zones) {
      for (const zone of zones) {
        if (value >= zone.from && value <= zone.to) {
          return zone.color;
        }
      }
    }
    // Default color scale
    if (percentage >= 0.8) return ISA101_COLORS.normal;
    if (percentage >= 0.5) return ISA101_COLORS.warning;
    return ISA101_COLORS.critical;
  };

  // Default zones if not provided
  const defaultZones = zones || [
    { from: min, to: min + (max - min) * 0.3, color: ISA101_COLORS.critical },
    { from: min + (max - min) * 0.3, to: min + (max - min) * 0.7, color: ISA101_COLORS.warning },
    { from: min + (max - min) * 0.7, to: max, color: ISA101_COLORS.normal },
  ];

  // Tick marks
  const tickCount = 5;
  const tickAngles = Array.from({ length: tickCount + 1 }, (_, i) =>
    startAngle + (i * totalAngle / tickCount)
  );

  return (
    <div className={`inline-flex flex-col items-center ${className}`} role="img" aria-label={`Gauge: ${value}${unit}`}>
      <svg width={size} height={size * 0.7} viewBox={`0 0 ${size} ${size * 0.85}`}>
        {/* Background arc with zones */}
        {defaultZones.map((zone, idx) => {
          const zoneStart = startAngle + ((zone.from - min) / (max - min)) * totalAngle;
          const zoneEnd = startAngle + ((zone.to - min) / (max - min)) * totalAngle;
          return (
            <path
              key={idx}
              d={describeArc(zoneStart, zoneEnd, radius)}
              fill="none"
              stroke={zone.color}
              strokeWidth={thickness}
              strokeLinecap="butt"
              opacity={0.2}
            />
          );
        })}

        {/* Value arc */}
        <path
          d={describeArc(startAngle, currentAngle, radius)}
          fill="none"
          stroke={getValueColor()}
          strokeWidth={thickness}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.5s ease-out' }}
        />

        {/* Tick marks */}
        {showTicks && tickAngles.map((angle, idx) => {
          const outer = polarToCartesian(angle, radius + 5);
          const inner = polarToCartesian(angle, radius - thickness - 3);
          const tickValue = min + (idx * (max - min) / tickCount);
          const labelPos = polarToCartesian(angle, radius - thickness - 15);
          return (
            <g key={idx}>
              <line
                x1={outer.x}
                y1={outer.y}
                x2={inner.x}
                y2={inner.y}
                stroke="#94a3b8"
                strokeWidth={1.5}
              />
              <text
                x={labelPos.x}
                y={labelPos.y}
                textAnchor="middle"
                dominantBaseline="middle"
                className="text-[9px] fill-slate-500"
              >
                {tickValue.toFixed(0)}
              </text>
            </g>
          );
        })}

        {/* Target indicator */}
        {target !== undefined && (
          <>
            {(() => {
              const targetAngle = startAngle + ((target - min) / (max - min)) * totalAngle;
              const outer = polarToCartesian(targetAngle, radius + 8);
              const inner = polarToCartesian(targetAngle, radius - thickness - 5);
              return (
                <line
                  x1={outer.x}
                  y1={outer.y}
                  x2={inner.x}
                  y2={inner.y}
                  stroke="#1e293b"
                  strokeWidth={2}
                  strokeDasharray="3 2"
                />
              );
            })()}
          </>
        )}

        {/* Center value display */}
        <text
          x={center}
          y={center + 10}
          textAnchor="middle"
          className="text-2xl font-bold"
          fill={getValueColor()}
        >
          {value.toFixed(1)}
        </text>
        <text
          x={center}
          y={center + 28}
          textAnchor="middle"
          className="text-xs fill-slate-500"
        >
          {unit}
        </text>
      </svg>
      {label && (
        <span className="text-sm font-medium text-slate-700 mt-1">{label}</span>
      )}
    </div>
  );
};

// ============================================
// PROFESSIONAL TREEMAP CHART
// ============================================
interface TreemapNode {
  name: string;
  value: number;
  color?: string;
  children?: TreemapNode[];
}

interface TreemapProps {
  data: TreemapNode[];
  height?: number;
  colors?: string[];
  showLabels?: boolean;
  onNodeClick?: (node: TreemapNode) => void;
  className?: string;
}

export const ProfessionalTreemap: React.FC<TreemapProps> = ({
  data,
  height = 300,
  colors = CHART_COLORS,
  showLabels = true,
  onNodeClick,
  className = '',
}) => {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = React.useState({ width: 400, height });

  React.useEffect(() => {
    if (containerRef.current) {
      const { width } = containerRef.current.getBoundingClientRect();
      setDimensions({ width, height });
    }
  }, [height]);

  // Simple treemap layout algorithm (squarified)
  const calculateLayout = (
    nodes: TreemapNode[],
    x: number,
    y: number,
    width: number,
    height: number
  ): Array<{ node: TreemapNode; x: number; y: number; width: number; height: number; color: string }> => {
    const totalValue = nodes.reduce((sum, n) => sum + n.value, 0);
    const result: Array<{ node: TreemapNode; x: number; y: number; width: number; height: number; color: string }> = [];

    let currentX = x;
    let currentY = y;
    const isHorizontal = width > height;

    nodes.forEach((node, idx) => {
      const ratio = node.value / totalValue;
      const color = node.color || colors[idx % colors.length];

      if (isHorizontal) {
        const nodeWidth = width * ratio;
        result.push({
          node,
          x: currentX,
          y: currentY,
          width: nodeWidth,
          height: height,
          color,
        });
        currentX += nodeWidth;
      } else {
        const nodeHeight = height * ratio;
        result.push({
          node,
          x: currentX,
          y: currentY,
          width: width,
          height: nodeHeight,
          color,
        });
        currentY += nodeHeight;
      }
    });

    return result;
  };

  const layout = calculateLayout(data, 0, 0, dimensions.width, dimensions.height);
  const total = data.reduce((sum, n) => sum + n.value, 0);

  return (
    <div
      ref={containerRef}
      className={`relative ${className}`}
      style={{ height }}
      role="img"
      aria-label={`Treemap com ${data.length} categorias`}
    >
      <svg width="100%" height={height}>
        {layout.map((item, idx) => (
          <g
            key={idx}
            onClick={() => onNodeClick?.(item.node)}
            style={{ cursor: onNodeClick ? 'pointer' : 'default' }}
          >
            <rect
              x={item.x + 1}
              y={item.y + 1}
              width={Math.max(0, item.width - 2)}
              height={Math.max(0, item.height - 2)}
              fill={item.color}
              rx={4}
              className="hover:opacity-80 transition-opacity"
            />
            {showLabels && item.width > 60 && item.height > 40 && (
              <>
                <text
                  x={item.x + item.width / 2}
                  y={item.y + item.height / 2 - 8}
                  textAnchor="middle"
                  className="text-xs font-semibold fill-white drop-shadow-sm"
                  style={{ pointerEvents: 'none' }}
                >
                  {item.node.name}
                </text>
                <text
                  x={item.x + item.width / 2}
                  y={item.y + item.height / 2 + 8}
                  textAnchor="middle"
                  className="text-[10px] fill-white/80"
                  style={{ pointerEvents: 'none' }}
                >
                  {item.node.value.toLocaleString('pt-BR')} ({((item.node.value / total) * 100).toFixed(1)}%)
                </text>
              </>
            )}
          </g>
        ))}
      </svg>
    </div>
  );
};

// ============================================
// WHY BUTTON - EXPLAINABILITY COMPONENT
// ============================================
interface WhyButtonProps {
  metricName: string;
  value: number | string;
  explanation?: string;
  factors?: Array<{ factor: string; impact: 'positive' | 'negative' | 'neutral'; weight: number }>;
  onRequestExplanation?: () => void;
  loading?: boolean;
  className?: string;
}

export const WhyButton: React.FC<WhyButtonProps> = ({
  metricName,
  value,
  explanation,
  factors,
  onRequestExplanation,
  loading = false,
  className = '',
}) => {
  const [isOpen, setIsOpen] = React.useState(false);

  const handleClick = () => {
    if (!explanation && !factors && onRequestExplanation) {
      onRequestExplanation();
    }
    setIsOpen(!isOpen);
  };

  return (
    <div className={`relative inline-block ${className}`}>
      <button
        onClick={handleClick}
        className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400"
        aria-label={`Por que ${metricName} é ${value}?`}
        disabled={loading}
      >
        {loading ? (
          <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : (
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        )}
        <span>Por quê?</span>
      </button>

      {isOpen && (explanation || factors) && (
        <div className="absolute z-50 top-full left-0 mt-2 w-72 bg-white rounded-lg shadow-xl border border-slate-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-slate-800">
              Explicação: {metricName}
            </h4>
            <button
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-slate-600"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          {explanation && (
            <p className="text-sm text-slate-600 mb-3">{explanation}</p>
          )}

          {factors && factors.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-slate-500 uppercase">Fatores Contribuintes:</p>
              {factors.map((factor, idx) => (
                <div key={idx} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${
                      factor.impact === 'positive' ? 'bg-emerald-500' :
                      factor.impact === 'negative' ? 'bg-red-500' : 'bg-slate-400'
                    }`} />
                    <span className="text-slate-700">{factor.factor}</span>
                  </div>
                  <span className={`font-medium ${
                    factor.impact === 'positive' ? 'text-emerald-600' :
                    factor.impact === 'negative' ? 'text-red-600' : 'text-slate-500'
                  }`}>
                    {factor.impact === 'positive' ? '+' : factor.impact === 'negative' ? '-' : ''}
                    {(factor.weight * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Arrow */}
          <div className="absolute -top-2 left-4 w-4 h-4 bg-white border-l border-t border-slate-200 transform rotate-45" />
        </div>
      )}
    </div>
  );
};

// ============================================
// EXPORTS
// ============================================
export default {
  ChartCard,
  ProfessionalDonutChart,
  ProfessionalBarChart,
  ProfessionalAreaChart,
  ProfessionalLineChart,
  ProfessionalMultiBarChart,
  ProfessionalPredictionChart,
  ProfessionalSparkChart,
  ProfessionalRadialGauge,
  ProfessionalTreemap,
  WhyButton,
  // Utilities
  COLORBLIND_SAFE_PALETTE,
  ISA101_COLORS,
  CHART_COLORS,
  formatValueWithUnit,
  getUnitLabel,
};
