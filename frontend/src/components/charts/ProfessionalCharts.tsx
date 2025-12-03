/**
 * Professional Chart Components - Enterprise Quality without MUI
 * ==============================================================
 *
 * Componentes de gráficos profissionais usando Recharts + Tailwind
 * Qualidade equivalente ao MUI, sem dependência do Emotion
 */
import React, { useMemo } from 'react';
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
} from 'recharts';
import { TrendingUp, TrendingDown, Minus, MoreVertical, Download, Maximize2, RefreshCw } from 'lucide-react';

// ============================================
// THEME / COLORS
// ============================================
const COLORS = {
  primary: '#3b82f6',
  secondary: '#8b5cf6',
  success: '#10b981',
  error: '#ef4444',
  warning: '#f59e0b',
  info: '#06b6d4',
  rose: '#f43f5e',
  orange: '#f97316',
  amber: '#f59e0b',
  blue: '#3b82f6',
};

const CHART_COLORS = [
  '#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444',
  '#06b6d4', '#ec4899', '#14b8a6', '#f97316', '#6366f1',
];

const DONUT_COLORS = {
  rose: '#f43f5e',
  orange: '#f97316',
  amber: '#f59e0b',
  blue: '#3b82f6',
  emerald: '#10b981',
  violet: '#8b5cf6',
  cyan: '#06b6d4',
  pink: '#ec4899',
};

// ============================================
// CUSTOM TOOLTIP
// ============================================
const CustomTooltip: React.FC<TooltipProps<number, string>> = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="bg-white/95 backdrop-blur-sm border border-slate-200 rounded-lg shadow-lg p-3 min-w-[140px]">
      <p className="text-sm font-semibold text-slate-800 mb-2">{label}</p>
      {payload.map((entry, index) => (
        <div key={index} className="flex items-center justify-between gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-slate-600">{entry.name}</span>
          </div>
          <span className="font-semibold text-slate-800">
            {typeof entry.value === 'number' ? entry.value.toLocaleString('pt-BR') : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
};

// ============================================
// CARD WRAPPER
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
}) => {
  const [menuOpen, setMenuOpen] = React.useState(false);

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor = trend === 'up' ? 'text-emerald-500 bg-emerald-50' :
                     trend === 'down' ? 'text-red-500 bg-red-50' :
                     'text-slate-500 bg-slate-50';

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow ${className}`}>
      {/* Header */}
      <div className="flex items-start justify-between p-4 pb-2">
        <div className="flex items-start gap-3">
          {trend && (
            <div className={`p-2 rounded-lg ${trendColor}`}>
              <TrendIcon className="w-5 h-5" />
            </div>
          )}
          <div>
            <h3 className="text-base font-semibold text-slate-800">{title}</h3>
            <div className="flex items-center gap-2 mt-0.5">
              {subtitle && <span className="text-sm text-slate-500">{subtitle}</span>}
              {trendValue && (
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${trendColor}`}>
                  {trendValue}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Actions Menu */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
          >
            <MoreVertical className="w-5 h-5" />
          </button>

          {menuOpen && (
            <div className="absolute right-0 top-full mt-1 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-10 min-w-[140px]">
              {onRefresh && (
                <button
                  onClick={() => { onRefresh(); setMenuOpen(false); }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
                >
                  <RefreshCw className="w-4 h-4" /> Atualizar
                </button>
              )}
              {onDownload && (
                <button
                  onClick={() => { onDownload(); setMenuOpen(false); }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
                >
                  <Download className="w-4 h-4" /> Download
                </button>
              )}
              {onFullscreen && (
                <button
                  onClick={() => { onFullscreen(); setMenuOpen(false); }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
                >
                  <Maximize2 className="w-4 h-4" /> Tela cheia
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
}

export const ProfessionalDonutChart: React.FC<ProfessionalDonutChartProps> = ({
  data,
  colors = ['#f43f5e', '#f97316', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6'],
  height = 220,
  innerRadius = 60,
  outerRadius = 90,
  showLabels = false,
  showLegend = true,
  title,
  subtitle,
}) => {
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
        fill="#64748b"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        className="text-xs font-medium"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <div>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
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
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>

      {/* Custom Legend */}
      {showLegend && (
        <div className="flex flex-wrap justify-center gap-4 mt-3">
          {data.map((item, idx) => (
            <div key={item.name} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: item.color || colors[idx % colors.length] }}
              />
              <span className="text-sm text-slate-600">
                {item.name}: <span className="font-semibold">{item.value}</span>
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ============================================
// PROFESSIONAL BAR CHART
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
  title?: string;
  subtitle?: string;
}

export const ProfessionalBarChart: React.FC<ProfessionalBarChartProps> = ({
  data,
  xAxisKey,
  categories,
  colors = ['#f43f5e', '#f97316', '#f59e0b', '#3b82f6', '#10b981'],
  height = 220,
  stacked = false,
  showGrid = true,
  showLegend = true,
}) => {
  return (
    <div>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e2e8f0"
              vertical={false}
            />
          )}
          <XAxis
            dataKey={xAxisKey}
            tick={{ fontSize: 12, fill: '#64748b' }}
            stroke="#e2e8f0"
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#64748b' }}
            stroke="#e2e8f0"
            tickLine={false}
            axisLine={{ stroke: '#e2e8f0' }}
          />
          <Tooltip content={<CustomTooltip />} />
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
// PROFESSIONAL AREA CHART
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
  title?: string;
  subtitle?: string;
}

export const ProfessionalAreaChart: React.FC<ProfessionalAreaChartProps> = ({
  data,
  xAxisKey,
  dataKey,
  color = '#3b82f6',
  height = 220,
  showGrid = true,
  gradientOpacity = 0.3,
}) => {
  const gradientId = `gradient-${dataKey}`;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
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
          tick={{ fontSize: 12, fill: '#64748b' }}
          stroke="#e2e8f0"
          tickLine={false}
          axisLine={{ stroke: '#e2e8f0' }}
        />
        <YAxis
          tick={{ fontSize: 12, fill: '#64748b' }}
          stroke="#e2e8f0"
          tickLine={false}
          axisLine={{ stroke: '#e2e8f0' }}
        />
        <Tooltip content={<CustomTooltip />} />
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
  );
};

// ============================================
// PROFESSIONAL LINE CHART
// ============================================
interface LineChartData {
  [key: string]: string | number;
}

interface ProfessionalLineChartProps {
  data: LineChartData[];
  xAxisKey: string;
  lines: Array<{
    dataKey: string;
    color?: string;
    name?: string;
    strokeWidth?: number;
    dot?: boolean;
  }>;
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
}

export const ProfessionalLineChart: React.FC<ProfessionalLineChartProps> = ({
  data,
  xAxisKey,
  lines,
  height = 220,
  showGrid = true,
  showLegend = true,
}) => {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        {showGrid && (
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#e2e8f0"
            vertical={false}
          />
        )}
        <XAxis
          dataKey={xAxisKey}
          tick={{ fontSize: 12, fill: '#64748b' }}
          stroke="#e2e8f0"
          tickLine={false}
          axisLine={{ stroke: '#e2e8f0' }}
        />
        <YAxis
          tick={{ fontSize: 12, fill: '#64748b' }}
          stroke="#e2e8f0"
          tickLine={false}
          axisLine={{ stroke: '#e2e8f0' }}
        />
        <Tooltip content={<CustomTooltip />} />
        {showLegend && (
          <Legend
            wrapperStyle={{ paddingTop: 16 }}
            formatter={(value) => <span className="text-sm text-slate-600">{value}</span>}
          />
        )}
        {lines.map((line, index) => (
          <Line
            key={line.dataKey}
            type="monotone"
            dataKey={line.dataKey}
            name={line.name || line.dataKey}
            stroke={line.color || CHART_COLORS[index % CHART_COLORS.length]}
            strokeWidth={line.strokeWidth || 2}
            dot={line.dot ?? false}
            animationDuration={800}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
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
}

export const ProfessionalMultiBarChart: React.FC<MultiBarChartProps> = ({
  data,
  xAxisKey,
  bars,
  height = 220,
  stacked = false,
  showGrid = true,
  showLegend = true,
}) => {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        {showGrid && (
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#e2e8f0"
            vertical={false}
          />
        )}
        <XAxis
          dataKey={xAxisKey}
          tick={{ fontSize: 12, fill: '#64748b' }}
          stroke="#e2e8f0"
          tickLine={false}
          axisLine={{ stroke: '#e2e8f0' }}
        />
        <YAxis
          tick={{ fontSize: 12, fill: '#64748b' }}
          stroke="#e2e8f0"
          tickLine={false}
          axisLine={{ stroke: '#e2e8f0' }}
        />
        <Tooltip content={<CustomTooltip />} />
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
  );
};

// ============================================
// PROFESSIONAL PREDICTION CHART (with confidence band)
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
}

export const ProfessionalPredictionChart: React.FC<ProfessionalPredictionChartProps> = ({
  data,
  xAxisKey,
  actualDataKey,
  predictionDataKey,
  upperBoundKey,
  lowerBoundKey,
  actualColor = '#3b82f6',
  predictionColor = '#8b5cf6',
  bandColor = '#8b5cf6',
  height = 320,
  showGrid = true,
  showLegend = true,
}) => {
  const actualGradientId = 'prediction-actual-gradient';
  const predictionGradientId = 'prediction-pred-gradient';
  const bandGradientId = 'prediction-band-gradient';

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
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
          tick={{ fontSize: 11, fill: '#64748b' }}
          stroke="#e2e8f0"
          tickLine={false}
          axisLine={{ stroke: '#e2e8f0' }}
          interval="preserveStartEnd"
          minTickGap={50}
        />
        <YAxis
          tick={{ fontSize: 11, fill: '#64748b' }}
          stroke="#e2e8f0"
          tickLine={false}
          axisLine={{ stroke: '#e2e8f0' }}
          domain={['dataMin - 5', 'dataMax + 5']}
        />
        <Tooltip content={<CustomTooltip />} />
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

        {/* Actual data */}
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

        {/* Prediction line */}
        <Area
          type="monotone"
          dataKey={predictionDataKey}
          name="Predição ML"
          stroke={predictionColor}
          strokeWidth={2.5}
          fill={`url(#${predictionGradientId})`}
          animationDuration={800}
          connectNulls={true}
          strokeDasharray="0"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

// ============================================
// PROFESSIONAL SPARK CHART (Mini inline chart)
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
  color = '#3b82f6',
  height = 40,
  width = 96,
  className = '',
}) => {
  const gradientId = `spark-gradient-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className={className} style={{ width, height }}>
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

export default {
  ChartCard,
  ProfessionalDonutChart,
  ProfessionalBarChart,
  ProfessionalAreaChart,
  ProfessionalLineChart,
  ProfessionalMultiBarChart,
  ProfessionalPredictionChart,
  ProfessionalSparkChart,
};
