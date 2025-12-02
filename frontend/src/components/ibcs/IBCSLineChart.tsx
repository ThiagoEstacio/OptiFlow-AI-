/**
 * 📈 IBCS Line Chart - Professional Time Series Chart
 * ====================================================
 *
 * Gráfico de linhas seguindo padrões IBCS:
 * - Linha sólida preta para Actual (AC)
 * - Linha cinza para Previous Year (PY)
 * - Linha pontilhada para Forecast (FC)
 * - Área sombreada para intervalo de confiança
 * - Reference lines para metas
 */

import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
  Legend,
} from 'recharts';
import { Box, Typography, Stack } from '@mui/material';
import {
  IBCSColors,
  IBCSTypography,
  IBCSChartDefaults,
  formatIBCSNumber,
  getVarianceColor,
  formatVariance,
} from './theme';

// ========================================
// Types
// ========================================

export interface IBCSTimeSeriesPoint {
  timestamp: string | Date;
  label?: string;
  actual?: number;
  plan?: number;
  previousYear?: number;
  forecast?: number;
  forecastLower?: number;
  forecastUpper?: number;
  target?: number;
}

interface IBCSLineChartProps {
  data: IBCSTimeSeriesPoint[];
  title?: string;
  subtitle?: string;
  unit?: string;
  height?: number;
  showPlan?: boolean;
  showPreviousYear?: boolean;
  showForecast?: boolean;
  showConfidenceInterval?: boolean;
  showTarget?: boolean;
  targetValue?: number;
  targetLabel?: string;
  dateFormat?: 'short' | 'medium' | 'long';
  compactNumbers?: boolean;
  showDots?: boolean;
  areaFill?: boolean;
}

// ========================================
// Date Formatter
// ========================================

const formatDate = (
  date: string | Date,
  format: 'short' | 'medium' | 'long'
): string => {
  const d = new Date(date);

  switch (format) {
    case 'short':
      return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
    case 'medium':
      return d.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short',
      });
    case 'long':
      return d.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short',
        year: '2-digit',
      });
    default:
      return d.toLocaleDateString('pt-BR');
  }
};

// ========================================
// Custom Tooltip
// ========================================

const IBCSLineTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{ value: number; name: string; dataKey: string; color: string; payload?: IBCSTimeSeriesPoint }>;
  label?: string;
  unit?: string;
}> = ({ active, payload, label, unit = '' }) => {
  if (!active || !payload || payload.length === 0) return null;

  const data = payload[0]?.payload as IBCSTimeSeriesPoint;

  return (
    <Box
      sx={{
        ...IBCSChartDefaults.tooltip,
        p: 1.5,
        minWidth: 160,
      }}
    >
      <Typography
        sx={{
          ...IBCSTypography.subtitle,
          fontWeight: 600,
          mb: 1,
          borderBottom: `1px solid ${IBCSColors.gridLine}`,
          pb: 0.5,
        }}
      >
        {data.label || formatDate(data.timestamp, 'medium')}
      </Typography>

      <Stack spacing={0.5}>
        {payload.map((entry, index) => (
          <Stack key={index} direction="row" justifyContent="space-between">
            <Stack direction="row" alignItems="center" spacing={0.5}>
              <Box
                sx={{
                  width: 10,
                  height: 3,
                  bgcolor: entry.color,
                  borderRadius: 0.5,
                }}
              />
              <Typography sx={IBCSTypography.valueSmall}>
                {entry.name}:
              </Typography>
            </Stack>
            <Typography sx={{ ...IBCSTypography.value, fontSize: 12 }}>
              {formatIBCSNumber(entry.value)} {unit}
            </Typography>
          </Stack>
        ))}

        {/* Variação vs Plan */}
        {data.actual !== undefined && data.plan !== undefined && (
          <Stack
            direction="row"
            justifyContent="space-between"
            sx={{
              mt: 0.5,
              pt: 0.5,
              borderTop: `1px solid ${IBCSColors.gridLine}`,
            }}
          >
            <Typography sx={IBCSTypography.valueSmall}>vs Plano:</Typography>
            <Typography
              sx={{
                ...IBCSTypography.variance,
                color: getVarianceColor(
                  ((data.actual - data.plan) / data.plan) * 100
                ),
              }}
            >
              {formatVariance(((data.actual - data.plan) / data.plan) * 100)}
            </Typography>
          </Stack>
        )}
      </Stack>
    </Box>
  );
};

// ========================================
// Custom Dot Component
// ========================================

const IBCSDot: React.FC<{
  cx?: number;
  cy?: number;
  value?: number;
  payload?: IBCSTimeSeriesPoint;
}> = ({ cx, cy }) => {
  if (cx === undefined || cy === undefined) return null;

  return (
    <circle
      cx={cx}
      cy={cy}
      r={3}
      fill={IBCSColors.actual}
      stroke={IBCSColors.background}
      strokeWidth={1}
    />
  );
};

// ========================================
// Main Component
// ========================================

export const IBCSLineChart: React.FC<IBCSLineChartProps> = ({
  data,
  title,
  subtitle,
  unit = '',
  height = 300,
  showPlan = false,
  showPreviousYear = false,
  showForecast = false,
  showConfidenceInterval = false,
  showTarget = false,
  targetValue,
  targetLabel,
  dateFormat = 'medium',
  compactNumbers = true,
  showDots = false,
  areaFill = false,
}) => {
  // Process data
  const processedData = useMemo(() => {
    return data.map((item) => ({
      ...item,
      formattedDate: formatDate(item.timestamp, dateFormat),
    }));
  }, [data, dateFormat]);

  // Calculate Y domain
  const yDomain = useMemo(() => {
    const values = processedData.flatMap((d) =>
      [
        d.actual,
        d.plan,
        d.previousYear,
        d.forecast,
        d.forecastUpper,
        d.forecastLower,
        targetValue,
      ].filter((v): v is number => v !== undefined)
    );
    const max = Math.max(...values);
    const min = Math.min(...values, 0);
    const padding = (max - min) * 0.1;
    return [Math.floor(min - padding), Math.ceil(max + padding)];
  }, [processedData, targetValue]);

  // Determine if we need ComposedChart (for confidence interval)
  const ChartComponent = showConfidenceInterval ? ComposedChart : LineChart;

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      {(title || subtitle) && (
        <Box sx={{ mb: 2 }}>
          {title && (
            <Typography sx={IBCSTypography.title}>{title}</Typography>
          )}
          {subtitle && (
            <Typography sx={IBCSTypography.subtitle}>{subtitle}</Typography>
          )}
        </Box>
      )}

      {/* Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <ChartComponent data={processedData} margin={IBCSChartDefaults.margin}>
          <defs>
            {/* Gradient for area fill */}
            <linearGradient id="ibcs-area-gradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={IBCSColors.actual} stopOpacity={0.15} />
              <stop offset="95%" stopColor={IBCSColors.actual} stopOpacity={0} />
            </linearGradient>

            {/* Gradient for confidence interval */}
            <linearGradient id="ibcs-confidence-gradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={IBCSColors.forecast} stopOpacity={0.3} />
              <stop offset="95%" stopColor={IBCSColors.forecast} stopOpacity={0.05} />
            </linearGradient>
          </defs>

          <CartesianGrid {...IBCSChartDefaults.grid} />

          <XAxis
            dataKey="formattedDate"
            tick={{ ...IBCSTypography.axisLabel }}
            axisLine={{ stroke: IBCSColors.axisLine }}
            tickLine={false}
          />

          <YAxis
            domain={yDomain}
            tick={{ ...IBCSTypography.axisLabel }}
            axisLine={{ stroke: IBCSColors.axisLine }}
            tickLine={false}
            tickFormatter={(value) =>
              compactNumbers
                ? formatIBCSNumber(value, { unit })
                : value.toLocaleString('pt-BR')
            }
          />

          <Tooltip content={<IBCSLineTooltip unit={unit} />} />

          {/* Target Line */}
          {showTarget && targetValue !== undefined && (
            <ReferenceLine
              y={targetValue}
              stroke={IBCSColors.positive}
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{
                value: targetLabel || `Meta: ${formatIBCSNumber(targetValue)}`,
                position: 'insideTopRight',
                fill: IBCSColors.positive,
                fontSize: 11,
                fontWeight: 600,
              }}
            />
          )}

          {/* Confidence Interval Area */}
          {showConfidenceInterval && (
            <Area
              type="monotone"
              dataKey="forecastUpper"
              stroke="none"
              fill="url(#ibcs-confidence-gradient)"
              connectNulls
            />
          )}

          {/* Previous Year Line */}
          {showPreviousYear && (
            <Line
              type="monotone"
              dataKey="previousYear"
              stroke={IBCSColors.previousYear}
              strokeWidth={2}
              dot={false}
              name="Ano Anterior"
              connectNulls
            />
          )}

          {/* Plan Line */}
          {showPlan && (
            <Line
              type="monotone"
              dataKey="plan"
              stroke={IBCSColors.plan}
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              name="Plano"
              connectNulls
            />
          )}

          {/* Forecast Line */}
          {showForecast && (
            <Line
              type="monotone"
              dataKey="forecast"
              stroke={IBCSColors.forecast}
              strokeWidth={2}
              strokeDasharray="3 3"
              dot={false}
              name="Previsão"
              connectNulls
            />
          )}

          {/* Area Fill (optional) */}
          {areaFill && (
            <Area
              type="monotone"
              dataKey="actual"
              stroke="none"
              fill="url(#ibcs-area-gradient)"
              connectNulls
            />
          )}

          {/* Actual Line */}
          <Line
            type="monotone"
            dataKey="actual"
            stroke={IBCSColors.actual}
            strokeWidth={2.5}
            dot={showDots ? <IBCSDot /> : false}
            activeDot={{ r: 5, fill: IBCSColors.actual }}
            name="Atual"
            connectNulls
          />

          <Legend
            wrapperStyle={{
              paddingTop: 16,
            }}
            iconType="line"
            formatter={(value) => (
              <span style={{ ...IBCSTypography.axisLabel, marginLeft: 4 }}>
                {value}
              </span>
            )}
          />
        </ChartComponent>
      </ResponsiveContainer>

      {/* Summary Stats */}
      <Stack
        direction="row"
        spacing={4}
        justifyContent="center"
        sx={{
          mt: 2,
          pt: 2,
          borderTop: `1px solid ${IBCSColors.gridLine}`,
        }}
      >
        {/* Current Value */}
        {processedData.length > 0 && (
          <Stack alignItems="center">
            <Typography sx={IBCSTypography.axisLabel}>Último Valor</Typography>
            <Typography sx={IBCSTypography.value}>
              {formatIBCSNumber(processedData[processedData.length - 1].actual)} {unit}
            </Typography>
          </Stack>
        )}

        {/* Average */}
        <Stack alignItems="center">
          <Typography sx={IBCSTypography.axisLabel}>Média</Typography>
          <Typography sx={IBCSTypography.value}>
            {formatIBCSNumber(
              processedData.reduce((sum, d) => sum + d.actual, 0) /
                processedData.length
            )}{' '}
            {unit}
          </Typography>
        </Stack>

        {/* Min/Max */}
        <Stack alignItems="center">
          <Typography sx={IBCSTypography.axisLabel}>Mín / Máx</Typography>
          <Typography sx={IBCSTypography.value}>
            {formatIBCSNumber(Math.min(...processedData.map((d) => d.actual)))} /{' '}
            {formatIBCSNumber(Math.max(...processedData.map((d) => d.actual)))}
          </Typography>
        </Stack>

        {/* Trend */}
        {processedData.length >= 2 && (
          <Stack alignItems="center">
            <Typography sx={IBCSTypography.axisLabel}>Tendência</Typography>
            <Typography
              sx={{
                ...IBCSTypography.variance,
                color: getVarianceColor(
                  processedData[processedData.length - 1].actual -
                    processedData[0].actual
                ),
              }}
            >
              {formatVariance(
                ((processedData[processedData.length - 1].actual -
                  processedData[0].actual) /
                  processedData[0].actual) *
                  100
              )}
            </Typography>
          </Stack>
        )}
      </Stack>
    </Box>
  );
};

export default IBCSLineChart;
