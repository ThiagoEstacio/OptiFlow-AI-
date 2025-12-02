/**
 * 📊 IBCS KPI Card - Professional KPI Display Component
 * ======================================================
 *
 * Card de KPI seguindo padrões IBCS:
 * - Valor grande e legível
 * - Indicador de variação claro (triângulo + percentual)
 * - Barra de progresso até meta
 * - Sparkline opcional
 * - Status visual (verde/amarelo/vermelho)
 */

import React from 'react';
import { Box, Typography, Stack, alpha, Tooltip } from '@mui/material';
import { TrendingUp, TrendingDown, TrendingFlat } from '@mui/icons-material';
import {
  Sparklines,
  SparklinesLine,
  SparklinesReferenceLine,
} from 'react-sparklines';
import {
  IBCSColors,
  IBCSTypography,
  formatIBCSNumber,
  getVarianceColor,
  formatVariance,
} from './theme';

// ========================================
// Types
// ========================================

type KPIStatus = 'good' | 'warning' | 'critical';
type TrendDirection = 'up' | 'down' | 'stable';

interface IBCSKPICardProps {
  title: string;
  value: number;
  unit?: string;
  target?: number;
  previousValue?: number;
  variance?: number;
  variancePercent?: number;
  status?: KPIStatus;
  trend?: TrendDirection;
  sparklineData?: number[];
  showSparkline?: boolean;
  showTarget?: boolean;
  showVariance?: boolean;
  format?: 'number' | 'percent' | 'currency';
  compact?: boolean;
  onClick?: () => void;
}

// ========================================
// Helper Components
// ========================================

const StatusIndicator: React.FC<{ status: KPIStatus }> = ({ status }) => {
  const colors = {
    good: IBCSColors.good,
    warning: IBCSColors.warning,
    critical: IBCSColors.critical,
  };

  return (
    <Box
      sx={{
        width: 8,
        height: 8,
        borderRadius: '50%',
        bgcolor: colors[status],
        boxShadow: `0 0 0 2px ${alpha(colors[status], 0.3)}`,
      }}
    />
  );
};

const TrendIndicator: React.FC<{
  direction: TrendDirection;
  value?: number;
}> = ({ direction, value }) => {
  const icons = {
    up: TrendingUp,
    down: TrendingDown,
    stable: TrendingFlat,
  };

  const Icon = icons[direction];
  const color =
    direction === 'up'
      ? IBCSColors.positive
      : direction === 'down'
      ? IBCSColors.negative
      : IBCSColors.neutral;

  return (
    <Stack direction="row" alignItems="center" spacing={0.5}>
      <Icon sx={{ fontSize: 16, color }} />
      {value !== undefined && (
        <Typography
          sx={{
            ...IBCSTypography.variance,
            color,
          }}
        >
          {formatVariance(value)}
        </Typography>
      )}
    </Stack>
  );
};

const ProgressBar: React.FC<{
  value: number;
  target: number;
  status: KPIStatus;
}> = ({ value, target, status }) => {
  const progress = Math.min((value / target) * 100, 100);
  const colors = {
    good: IBCSColors.good,
    warning: IBCSColors.warning,
    critical: IBCSColors.critical,
  };

  return (
    <Box sx={{ width: '100%', mt: 1 }}>
      <Stack direction="row" justifyContent="space-between" mb={0.5}>
        <Typography sx={IBCSTypography.axisLabel}>Progresso</Typography>
        <Typography sx={IBCSTypography.axisLabel}>
          Meta: {formatIBCSNumber(target)}
        </Typography>
      </Stack>
      <Box
        sx={{
          width: '100%',
          height: 6,
          bgcolor: alpha(colors[status], 0.2),
          borderRadius: 3,
          overflow: 'hidden',
        }}
      >
        <Box
          sx={{
            width: `${progress}%`,
            height: '100%',
            bgcolor: colors[status],
            borderRadius: 3,
            transition: 'width 0.5s ease-out',
          }}
        />
      </Box>
    </Box>
  );
};

// ========================================
// Simple Sparkline (no external dependency)
// ========================================

const SimpleSparkline: React.FC<{
  data: number[];
  width?: number;
  height?: number;
  color?: string;
}> = ({ data, width = 80, height = 30, color = IBCSColors.actual }) => {
  if (!data || data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data
    .map((value, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <svg width={width} height={height} style={{ overflow: 'visible' }}>
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Last point dot */}
      <circle
        cx={width}
        cy={height - ((data[data.length - 1] - min) / range) * height}
        r={2.5}
        fill={color}
      />
    </svg>
  );
};

// ========================================
// Main Component
// ========================================

export const IBCSKPICard: React.FC<IBCSKPICardProps> = ({
  title,
  value,
  unit = '',
  target,
  previousValue,
  variance,
  variancePercent,
  status = 'good',
  trend = 'stable',
  sparklineData,
  showSparkline = true,
  showTarget = true,
  showVariance = true,
  format = 'number',
  compact = false,
  onClick,
}) => {
  // Calculate variance if not provided
  const calculatedVariance =
    variance ?? (previousValue ? value - previousValue : undefined);
  const calculatedVariancePercent =
    variancePercent ??
    (previousValue && previousValue !== 0
      ? ((value - previousValue) / previousValue) * 100
      : undefined);

  // Determine status from variance if not provided
  const calculatedStatus = status;

  // Format value based on format prop
  const formatValue = (v: number): string => {
    switch (format) {
      case 'percent':
        return `${v.toFixed(1)}%`;
      case 'currency':
        return v.toLocaleString('pt-BR', {
          style: 'currency',
          currency: 'BRL',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        });
      default:
        return formatIBCSNumber(v);
    }
  };

  const statusColors = {
    good: IBCSColors.good,
    warning: IBCSColors.warning,
    critical: IBCSColors.critical,
  };

  return (
    <Box
      onClick={onClick}
      sx={{
        p: compact ? 2 : 2.5,
        bgcolor: IBCSColors.background,
        border: `1px solid ${IBCSColors.gridLine}`,
        borderRadius: 2,
        borderLeft: `4px solid ${statusColors[calculatedStatus]}`,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.2s ease',
        '&:hover': onClick
          ? {
              boxShadow: `0 4px 12px ${alpha(IBCSColors.actual, 0.15)}`,
              transform: 'translateY(-2px)',
            }
          : {},
      }}
    >
      {/* Header */}
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        mb={1.5}
      >
        <Stack direction="row" alignItems="center" spacing={1}>
          <StatusIndicator status={calculatedStatus} />
          <Typography
            sx={{
              ...IBCSTypography.subtitle,
              textTransform: 'uppercase',
              letterSpacing: 0.5,
            }}
          >
            {title}
          </Typography>
        </Stack>

        {showVariance && calculatedVariancePercent !== undefined && (
          <TrendIndicator direction={trend} value={calculatedVariancePercent} />
        )}
      </Stack>

      {/* Main Value */}
      <Stack direction="row" alignItems="baseline" spacing={1}>
        <Typography
          sx={{
            fontFamily: IBCSTypography.value.fontFamily,
            fontSize: compact ? 28 : 36,
            fontWeight: 700,
            color: statusColors[calculatedStatus],
            lineHeight: 1,
          }}
        >
          {formatValue(value)}
        </Typography>
        {unit && format === 'number' && (
          <Typography
            sx={{
              ...IBCSTypography.subtitle,
              fontSize: compact ? 12 : 14,
            }}
          >
            {unit}
          </Typography>
        )}
      </Stack>

      {/* Sparkline */}
      {showSparkline && sparklineData && sparklineData.length > 1 && (
        <Box sx={{ mt: 1.5, mb: 1 }}>
          <SimpleSparkline
            data={sparklineData}
            width={compact ? 60 : 80}
            height={compact ? 20 : 30}
            color={statusColors[calculatedStatus]}
          />
        </Box>
      )}

      {/* Target Progress */}
      {showTarget && target !== undefined && (
        <ProgressBar
          value={value}
          target={target}
          status={calculatedStatus}
        />
      )}

      {/* Previous Value Comparison */}
      {previousValue !== undefined && (
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          sx={{
            mt: 1.5,
            pt: 1,
            borderTop: `1px solid ${IBCSColors.gridLine}`,
          }}
        >
          <Typography sx={IBCSTypography.axisLabel}>
            Anterior: {formatValue(previousValue)}
          </Typography>
          {calculatedVariance !== undefined && (
            <Tooltip title="Variação absoluta">
              <Typography
                sx={{
                  ...IBCSTypography.variance,
                  color: getVarianceColor(calculatedVariance),
                }}
              >
                {calculatedVariance > 0 ? '+' : ''}
                {format === 'percent'
                  ? `${calculatedVariance.toFixed(1)}pp`
                  : formatIBCSNumber(calculatedVariance)}
              </Typography>
            </Tooltip>
          )}
        </Stack>
      )}
    </Box>
  );
};

// ========================================
// Grid of KPI Cards
// ========================================

interface IBCSKPIGridProps {
  kpis: Array<IBCSKPICardProps>;
  columns?: number;
  gap?: number;
}

export const IBCSKPIGrid: React.FC<IBCSKPIGridProps> = ({
  kpis,
  columns = 4,
  gap = 2,
}) => {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: {
          xs: '1fr',
          sm: 'repeat(2, 1fr)',
          md: `repeat(${Math.min(columns, 3)}, 1fr)`,
          lg: `repeat(${columns}, 1fr)`,
        },
        gap,
      }}
    >
      {kpis.map((kpi, index) => (
        <IBCSKPICard key={index} {...kpi} />
      ))}
    </Box>
  );
};

export default IBCSKPICard;
