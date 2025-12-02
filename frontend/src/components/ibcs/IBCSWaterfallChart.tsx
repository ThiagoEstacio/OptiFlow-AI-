/**
 * 📊 IBCS Waterfall Chart - Bridge Chart for Variance Analysis
 * ============================================================
 *
 * Gráfico waterfall/bridge seguindo padrões IBCS:
 * - Barras cinza para valores base
 * - Verde para contribuições positivas
 * - Vermelho para contribuições negativas
 * - Conectores entre barras
 * - Totais destacados
 */

import React, { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
  LabelList,
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

interface WaterfallDataPoint {
  label: string;
  value: number;
  type: 'start' | 'positive' | 'negative' | 'subtotal' | 'total';
  description?: string;
}

interface IBCSWaterfallChartProps {
  data: WaterfallDataPoint[];
  title?: string;
  subtitle?: string;
  unit?: string;
  height?: number;
  showConnectors?: boolean;
  showDataLabels?: boolean;
  compactNumbers?: boolean;
}

// ========================================
// Process Waterfall Data
// ========================================

interface ProcessedWaterfallPoint {
  label: string;
  value: number;
  type: WaterfallDataPoint['type'];
  description?: string;
  start: number;
  end: number;
  displayValue: number;
  isNegative: boolean;
}

const processWaterfallData = (
  data: WaterfallDataPoint[]
): ProcessedWaterfallPoint[] => {
  let runningTotal = 0;

  return data.map((item) => {
    let start: number;
    let end: number;
    let displayValue: number;

    if (item.type === 'start') {
      start = 0;
      end = item.value;
      displayValue = item.value;
      runningTotal = item.value;
    } else if (item.type === 'total' || item.type === 'subtotal') {
      start = 0;
      end = runningTotal;
      displayValue = runningTotal;
    } else {
      if (item.value >= 0) {
        start = runningTotal;
        end = runningTotal + item.value;
      } else {
        start = runningTotal + item.value;
        end = runningTotal;
      }
      displayValue = item.value;
      runningTotal += item.value;
    }

    return {
      ...item,
      start,
      end,
      displayValue,
      isNegative: item.value < 0,
    };
  });
};

// ========================================
// Custom Tooltip
// ========================================

const WaterfallTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{ payload: ProcessedWaterfallPoint }>;
  unit?: string;
}> = ({ active, payload, unit = '' }) => {
  if (!active || !payload || payload.length === 0) return null;

  const data = payload[0]?.payload;
  if (!data) return null;

  return (
    <Box
      sx={{
        ...IBCSChartDefaults.tooltip,
        p: 1.5,
        minWidth: 150,
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
        {data.label}
      </Typography>

      <Stack spacing={0.5}>
        <Stack direction="row" justifyContent="space-between">
          <Typography sx={IBCSTypography.valueSmall}>Valor:</Typography>
          <Typography
            sx={{
              ...IBCSTypography.value,
              fontSize: 12,
              color:
                data.type === 'positive'
                  ? IBCSColors.positive
                  : data.type === 'negative'
                  ? IBCSColors.negative
                  : IBCSColors.labelText,
            }}
          >
            {data.displayValue > 0 ? '+' : ''}
            {formatIBCSNumber(data.displayValue)} {unit}
          </Typography>
        </Stack>

        {(data.type === 'total' || data.type === 'subtotal') && (
          <Stack direction="row" justifyContent="space-between">
            <Typography sx={IBCSTypography.valueSmall}>Acumulado:</Typography>
            <Typography sx={{ ...IBCSTypography.value, fontSize: 12 }}>
              {formatIBCSNumber(data.end)} {unit}
            </Typography>
          </Stack>
        )}

        {data.description && (
          <Typography
            sx={{
              ...IBCSTypography.axisLabel,
              mt: 0.5,
              pt: 0.5,
              borderTop: `1px solid ${IBCSColors.gridLine}`,
            }}
          >
            {data.description}
          </Typography>
        )}
      </Stack>
    </Box>
  );
};

// ========================================
// Custom Bar Shape with Connector
// ========================================

const WaterfallBar: React.FC<{
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  payload?: ProcessedWaterfallPoint;
  showConnector?: boolean;
  nextY?: number;
}> = ({ x = 0, y = 0, width = 0, height = 0, payload, showConnector, nextY }) => {
  if (!payload) return null;

  const getBarColor = () => {
    switch (payload.type) {
      case 'start':
        return IBCSColors.actual;
      case 'total':
      case 'subtotal':
        return IBCSColors.actual;
      case 'positive':
        return IBCSColors.positive;
      case 'negative':
        return IBCSColors.negative;
      default:
        return IBCSColors.actual;
    }
  };

  const isTotal = payload.type === 'total' || payload.type === 'subtotal';

  return (
    <g>
      {/* Main Bar */}
      <rect
        x={x}
        y={y}
        width={width}
        height={Math.abs(height)}
        fill={getBarColor()}
        rx={isTotal ? 0 : 2}
        ry={isTotal ? 0 : 2}
      />

      {/* Total/Subtotal indicator line */}
      {isTotal && (
        <line
          x1={x - 4}
          y1={y + Math.abs(height)}
          x2={x + width + 4}
          y2={y + Math.abs(height)}
          stroke={IBCSColors.actual}
          strokeWidth={3}
        />
      )}

      {/* Connector to next bar */}
      {showConnector && nextY !== undefined && (
        <line
          x1={x + width}
          y1={y}
          x2={x + width + 20}
          y2={y}
          stroke={IBCSColors.gridLine}
          strokeWidth={1}
          strokeDasharray="3 2"
        />
      )}
    </g>
  );
};

// ========================================
// Main Component
// ========================================

export const IBCSWaterfallChart: React.FC<IBCSWaterfallChartProps> = ({
  data,
  title,
  subtitle,
  unit = '',
  height = 350,
  showConnectors = true,
  showDataLabels = true,
  compactNumbers = true,
}) => {
  // Process data for waterfall visualization
  const processedData = useMemo(() => processWaterfallData(data), [data]);

  // Calculate Y domain
  const yDomain = useMemo(() => {
    const allValues = processedData.flatMap((d) => [d.start, d.end]);
    const max = Math.max(...allValues);
    const min = Math.min(...allValues, 0);
    const padding = (max - min) * 0.15;
    return [Math.floor(min - padding), Math.ceil(max + padding)];
  }, [processedData]);

  // Calculate variance summary
  const summary = useMemo(() => {
    const positiveSum = processedData
      .filter((d) => d.type === 'positive')
      .reduce((sum, d) => sum + d.displayValue, 0);
    const negativeSum = processedData
      .filter((d) => d.type === 'negative')
      .reduce((sum, d) => sum + d.displayValue, 0);
    const startValue =
      processedData.find((d) => d.type === 'start')?.displayValue || 0;
    const endValue =
      processedData.find((d) => d.type === 'total')?.end ||
      processedData[processedData.length - 1]?.end ||
      0;
    const netChange = endValue - startValue;
    const netChangePercent = startValue !== 0 ? (netChange / startValue) * 100 : 0;

    return {
      positiveSum,
      negativeSum,
      netChange,
      netChangePercent,
      startValue,
      endValue,
    };
  }, [processedData]);

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
        <BarChart
          data={processedData}
          margin={{ ...IBCSChartDefaults.margin, bottom: 60 }}
        >
          <CartesianGrid {...IBCSChartDefaults.grid} />

          <XAxis
            dataKey="label"
            tick={{ ...IBCSTypography.axisLabel }}
            axisLine={{ stroke: IBCSColors.axisLine }}
            tickLine={false}
            angle={-45}
            textAnchor="end"
            height={60}
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

          <Tooltip content={<WaterfallTooltip unit={unit} />} />

          {/* Zero Reference Line */}
          <ReferenceLine y={0} stroke={IBCSColors.axisLine} strokeWidth={1} />

          {/* Invisible bar for positioning (from 0 to start) */}
          <Bar
            dataKey="start"
            stackId="stack"
            fill="transparent"
            isAnimationActive={false}
          />

          {/* Actual bar (from start to end) */}
          <Bar
            dataKey={(d: ProcessedWaterfallPoint) => d.end - d.start}
            stackId="stack"
            isAnimationActive={true}
            animationDuration={500}
          >
            {processedData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={
                  entry.type === 'positive'
                    ? IBCSColors.positive
                    : entry.type === 'negative'
                    ? IBCSColors.negative
                    : IBCSColors.actual
                }
              />
            ))}

            {/* Data Labels */}
            {showDataLabels && (
              <LabelList
                dataKey="displayValue"
                position="top"
                formatter={(value: number) => {
                  const formatted = compactNumbers
                    ? formatIBCSNumber(Math.abs(value))
                    : Math.abs(value).toLocaleString('pt-BR');
                  return value >= 0 ? `+${formatted}` : `-${formatted}`;
                }}
                style={{
                  ...IBCSTypography.valueSmall,
                  fontWeight: 600,
                }}
                fill={(entry: ProcessedWaterfallPoint) =>
                  entry.type === 'positive'
                    ? IBCSColors.positive
                    : entry.type === 'negative'
                    ? IBCSColors.negative
                    : IBCSColors.labelText
                }
              />
            )}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Summary */}
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
        <Stack alignItems="center">
          <Typography sx={IBCSTypography.axisLabel}>Valor Inicial</Typography>
          <Typography sx={IBCSTypography.value}>
            {formatIBCSNumber(summary.startValue)} {unit}
          </Typography>
        </Stack>

        <Stack alignItems="center">
          <Typography sx={IBCSTypography.axisLabel}>Contribuições (+)</Typography>
          <Typography sx={{ ...IBCSTypography.value, color: IBCSColors.positive }}>
            +{formatIBCSNumber(summary.positiveSum)} {unit}
          </Typography>
        </Stack>

        <Stack alignItems="center">
          <Typography sx={IBCSTypography.axisLabel}>Contribuições (-)</Typography>
          <Typography sx={{ ...IBCSTypography.value, color: IBCSColors.negative }}>
            {formatIBCSNumber(summary.negativeSum)} {unit}
          </Typography>
        </Stack>

        <Stack alignItems="center">
          <Typography sx={IBCSTypography.axisLabel}>Valor Final</Typography>
          <Typography sx={IBCSTypography.value}>
            {formatIBCSNumber(summary.endValue)} {unit}
          </Typography>
        </Stack>

        <Stack alignItems="center">
          <Typography sx={IBCSTypography.axisLabel}>Variação</Typography>
          <Typography
            sx={{
              ...IBCSTypography.variance,
              color: getVarianceColor(summary.netChangePercent),
            }}
          >
            {formatVariance(summary.netChangePercent)}
          </Typography>
        </Stack>
      </Stack>

      {/* Legend */}
      <Stack
        direction="row"
        spacing={3}
        justifyContent="center"
        sx={{ mt: 2 }}
      >
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <Box
            sx={{
              width: 16,
              height: 12,
              bgcolor: IBCSColors.actual,
              borderRadius: 0.5,
            }}
          />
          <Typography sx={IBCSTypography.axisLabel}>Base/Total</Typography>
        </Stack>

        <Stack direction="row" alignItems="center" spacing={0.5}>
          <Box
            sx={{
              width: 16,
              height: 12,
              bgcolor: IBCSColors.positive,
              borderRadius: 0.5,
            }}
          />
          <Typography sx={IBCSTypography.axisLabel}>Aumento</Typography>
        </Stack>

        <Stack direction="row" alignItems="center" spacing={0.5}>
          <Box
            sx={{
              width: 16,
              height: 12,
              bgcolor: IBCSColors.negative,
              borderRadius: 0.5,
            }}
          />
          <Typography sx={IBCSTypography.axisLabel}>Redução</Typography>
        </Stack>
      </Stack>
    </Box>
  );
};

export default IBCSWaterfallChart;
