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
  // Utilities
  COLORBLIND_SAFE_PALETTE,
  ISA101_COLORS,
  CHART_COLORS,
  formatValueWithUnit,
  getUnitLabel,
};
