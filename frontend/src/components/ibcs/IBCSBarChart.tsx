/**
 * 📊 IBCS Bar Chart - Professional Bar Chart Component
 * =====================================================
 *
 * Gráfico de barras seguindo padrões IBCS:
 * - Barras sólidas para Actual (AC)
 * - Barras outline para Previous Year (PY)
 * - Barras hachuradas para Plan (PL)
 * - Indicadores de variação integrados
 * - Suporte a variance waterfall
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
import { Box, Typography, Stack, useTheme } from '@mui/material';
import {
  IBCSColors,
  IBCSTypography,
  IBCSChartDefaults,
  IBCSDataPoint,
  getVarianceColor,
  formatVariance,
  formatIBCSNumber,
} from './theme';

// ========================================
// Types
// ========================================

interface IBCSBarChartProps {
  data: IBCSDataPoint[];
  title?: string;
  subtitle?: string;
  unit?: string;
  height?: number;
  showVariance?: boolean;
  showPlan?: boolean;
  showPreviousYear?: boolean;
  orientation?: 'vertical' | 'horizontal';
  highlightNegative?: boolean;
  compactNumbers?: boolean;
  showDataLabels?: boolean;
  targetLine?: number;
  targetLabel?: string;
}

// ========================================
// Custom Tooltip
// ========================================

const IBCSTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{ value: number; name: string; dataKey: string; payload?: IBCSDataPoint }>;
  label?: string;
  unit?: string;
}> = ({ active, payload, label, unit = '' }) => {
  if (!active || !payload || payload.length === 0) return null;

  const data = payload[0]?.payload as IBCSDataPoint;

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
        {label}
      </Typography>

      <Stack spacing={0.5}>
        {data.actual !== undefined && (
          <Stack direction="row" justifyContent="space-between">
            <Typography sx={IBCSTypography.valueSmall}>Atual:</Typography>
            <Typography sx={{ ...IBCSTypography.value, fontSize: 12 }}>
              {formatIBCSNumber(data.actual)} {unit}
            </Typography>
          </Stack>
        )}

        {data.plan !== undefined && (
          <Stack direction="row" justifyContent="space-between">
            <Typography sx={IBCSTypography.valueSmall}>Plano:</Typography>
            <Typography sx={{ ...IBCSTypography.valueSmall }}>
              {formatIBCSNumber(data.plan)} {unit}
            </Typography>
          </Stack>
        )}

        {data.previousYear !== undefined && (
          <Stack direction="row" justifyContent="space-between">
            <Typography sx={IBCSTypography.valueSmall}>Ano Ant.:</Typography>
            <Typography sx={{ ...IBCSTypography.valueSmall }}>
              {formatIBCSNumber(data.previousYear)} {unit}
            </Typography>
          </Stack>
        )}

        {data.variancePercent !== undefined && (
          <Stack
            direction="row"
            justifyContent="space-between"
            sx={{
              mt: 0.5,
              pt: 0.5,
              borderTop: `1px solid ${IBCSColors.gridLine}`,
            }}
          >
            <Typography sx={IBCSTypography.valueSmall}>Variação:</Typography>
            <Typography
              sx={{
                ...IBCSTypography.variance,
                color: getVarianceColor(data.variancePercent),
              }}
            >
              {formatVariance(data.variancePercent)}
            </Typography>
          </Stack>
        )}
      </Stack>
    </Box>
  );
};

// ========================================
// Variance Indicator Component
// ========================================

const VarianceIndicator: React.FC<{
  x: number;
  y: number;
  width: number;
  value: number;
}> = ({ x, y, width, value }) => {
  const color = getVarianceColor(value);
  const isPositive = value > 0;

  return (
    <g>
      {/* Triângulo indicador */}
      <polygon
        points={
          isPositive
            ? `${x + width / 2 - 4},${y - 2} ${x + width / 2 + 4},${y - 2} ${x + width / 2},${y - 8}`
            : `${x + width / 2 - 4},${y - 8} ${x + width / 2 + 4},${y - 8} ${x + width / 2},${y - 2}`
        }
        fill={color}
      />
      {/* Valor da variação */}
      <text
        x={x + width / 2}
        y={y - 12}
        textAnchor="middle"
        fill={color}
        fontSize={10}
        fontWeight={600}
        fontFamily={IBCSTypography.variance.fontFamily}
      >
        {formatVariance(value)}
      </text>
    </g>
  );
};

// ========================================
// Main Component
// ========================================

export const IBCSBarChart: React.FC<IBCSBarChartProps> = ({
  data,
  title,
  subtitle,
  unit = '',
  height = 300,
  showVariance = true,
  showPlan = false,
  showPreviousYear = false,
  orientation = 'vertical',
  highlightNegative = true,
  compactNumbers = true,
  showDataLabels = true,
  targetLine,
  targetLabel,
}) => {
  const theme = useTheme();

  // Calcular variações se não fornecidas
  const processedData = useMemo(() => {
    return data.map((item) => {
      const variance =
        item.variance ??
        (item.plan ? item.actual - item.plan : undefined);
      const variancePercent =
        item.variancePercent ??
        (item.plan && item.plan !== 0
          ? ((item.actual - item.plan) / item.plan) * 100
          : undefined);

      return {
        ...item,
        variance,
        variancePercent,
      };
    });
  }, [data]);

  // Calcular domínio do eixo Y
  const yDomain = useMemo(() => {
    const values = processedData.flatMap((d) => [
      d.actual,
      d.plan ?? 0,
      d.previousYear ?? 0,
    ]);
    const max = Math.max(...values);
    const min = Math.min(...values, 0);
    return [min < 0 ? min * 1.1 : 0, max * 1.15]; // Espaço para labels
  }, [processedData]);

  // Custom bar shape para contorno (Previous Year)
  const OutlineBar: React.FC<{
    x?: number;
    y?: number;
    width?: number;
    height?: number;
  }> = ({ x = 0, y = 0, width = 0, height = 0 }) => (
    <rect
      x={x}
      y={y}
      width={width}
      height={height}
      fill="none"
      stroke={IBCSColors.previousYearOutline}
      strokeWidth={2}
    />
  );

  // Custom bar shape para hachurado (Plan)
  const HatchedBar: React.FC<{
    x?: number;
    y?: number;
    width?: number;
    height?: number;
  }> = ({ x = 0, y = 0, width = 0, height = 0 }) => (
    <g>
      <defs>
        <pattern
          id="ibcs-hatch"
          patternUnits="userSpaceOnUse"
          width="4"
          height="4"
        >
          <path
            d="M-1,1 l2,-2 M0,4 l4,-4 M3,5 l2,-2"
            style={{ stroke: IBCSColors.plan, strokeWidth: 1 }}
          />
        </pattern>
      </defs>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill="url(#ibcs-hatch)"
        stroke={IBCSColors.plan}
        strokeWidth={1}
      />
    </g>
  );

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
          margin={IBCSChartDefaults.margin}
          layout={orientation === 'horizontal' ? 'vertical' : 'horizontal'}
        >
          <CartesianGrid
            {...IBCSChartDefaults.grid}
            vertical={orientation === 'horizontal'}
            horizontal={orientation === 'vertical'}
          />

          {orientation === 'vertical' ? (
            <>
              <XAxis
                dataKey="label"
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
            </>
          ) : (
            <>
              <YAxis
                dataKey="label"
                type="category"
                tick={{ ...IBCSTypography.axisLabel }}
                axisLine={{ stroke: IBCSColors.axisLine }}
                tickLine={false}
                width={100}
              />
              <XAxis
                type="number"
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
            </>
          )}

          <Tooltip content={<IBCSTooltip unit={unit} />} />

          {/* Target/Reference Line */}
          {targetLine !== undefined && (
            <ReferenceLine
              y={orientation === 'vertical' ? targetLine : undefined}
              x={orientation === 'horizontal' ? targetLine : undefined}
              stroke={IBCSColors.negative}
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{
                value: targetLabel || `Meta: ${formatIBCSNumber(targetLine)}`,
                position: 'insideTopRight',
                fill: IBCSColors.negative,
                fontSize: 11,
              }}
            />
          )}

          {/* Previous Year Bar (Outline) */}
          {showPreviousYear && (
            <Bar
              dataKey="previousYear"
              shape={<OutlineBar />}
              name="Ano Anterior"
            />
          )}

          {/* Plan Bar (Hatched) */}
          {showPlan && (
            <Bar dataKey="plan" shape={<HatchedBar />} name="Plano" />
          )}

          {/* Actual Bar */}
          <Bar
            dataKey="actual"
            fill={IBCSColors.actual}
            name="Atual"
            radius={[2, 2, 0, 0]}
          >
            {processedData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={
                  highlightNegative && entry.actual < 0
                    ? IBCSColors.negative
                    : IBCSColors.actual
                }
              />
            ))}

            {/* Data Labels */}
            {showDataLabels && (
              <LabelList
                dataKey="actual"
                position="top"
                formatter={(value: number) =>
                  compactNumbers
                    ? formatIBCSNumber(value)
                    : value.toLocaleString('pt-BR')
                }
                style={{
                  ...IBCSTypography.valueSmall,
                  fill: IBCSColors.labelText,
                }}
              />
            )}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Variance Summary (optional) */}
      {showVariance && processedData.some((d) => d.variancePercent !== undefined) && (
        <Stack
          direction="row"
          spacing={3}
          justifyContent="center"
          sx={{ mt: 2, pt: 1, borderTop: `1px solid ${IBCSColors.gridLine}` }}
        >
          {processedData.slice(0, 5).map((item, idx) => (
            <Stack key={idx} alignItems="center" spacing={0.5}>
              <Typography sx={IBCSTypography.axisLabel}>{item.label}</Typography>
              {item.variancePercent !== undefined && (
                <Typography
                  sx={{
                    ...IBCSTypography.variance,
                    color: getVarianceColor(item.variancePercent),
                  }}
                >
                  {formatVariance(item.variancePercent)}
                </Typography>
              )}
            </Stack>
          ))}
        </Stack>
      )}

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
          <Typography sx={IBCSTypography.axisLabel}>Atual (AC)</Typography>
        </Stack>

        {showPlan && (
          <Stack direction="row" alignItems="center" spacing={0.5}>
            <Box
              sx={{
                width: 16,
                height: 12,
                background: `repeating-linear-gradient(
                  45deg,
                  ${IBCSColors.plan},
                  ${IBCSColors.plan} 1px,
                  transparent 1px,
                  transparent 3px
                )`,
                border: `1px solid ${IBCSColors.plan}`,
              }}
            />
            <Typography sx={IBCSTypography.axisLabel}>Plano (PL)</Typography>
          </Stack>
        )}

        {showPreviousYear && (
          <Stack direction="row" alignItems="center" spacing={0.5}>
            <Box
              sx={{
                width: 16,
                height: 12,
                border: `2px solid ${IBCSColors.previousYearOutline}`,
                bgcolor: 'transparent',
              }}
            />
            <Typography sx={IBCSTypography.axisLabel}>Ano Ant. (PY)</Typography>
          </Stack>
        )}
      </Stack>
    </Box>
  );
};

export default IBCSBarChart;
