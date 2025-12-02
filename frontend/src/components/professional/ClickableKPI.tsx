/**
 * 🎯 ClickableKPI - KPI Card com Cross-Filtering e Drill-Through
 * ===============================================================
 *
 * Componente de KPI interativo inspirado no Power BI.
 * Permite:
 * - Click para selecionar/filtrar
 * - Hover para tooltip com sparkline
 * - Drill-through para página de detalhes
 * - Visual de highlight quando selecionado
 */

import React, { useState, useRef, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tooltip,
  alpha,
  useTheme,
  Popover,
  Stack,
  Chip,
  Button,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  OpenInNew,
  FilterList,
  Compare,
  Info,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AreaChart,
  Area,
  ResponsiveContainer,
} from 'recharts';
import {
  useDashboardSelection,
  useSelectedKPI,
  useComparisonMode,
  KPIType,
  KPISelection,
} from '../../stores/dashboardSelectionStore';
import { useFilterStore } from '../../stores/filterStore';

// ========================================
// Types
// ========================================

interface ClickableKPIProps {
  type: KPIType;
  title: string;
  value: number;
  unit?: string;
  previousValue?: number;
  target?: number;
  trend?: 'up' | 'down' | 'stable';
  trendData?: number[]; // Sparkline data
  icon?: React.ReactNode;
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info';
  format?: 'number' | 'percent' | 'currency' | 'time';
  drillThroughPage?: string;
  relatedEquipments?: string[];
  relatedTags?: string[];
  onClick?: (kpi: KPISelection) => void;
  compact?: boolean;
  showSparkline?: boolean;
  showTrend?: boolean;
  showTarget?: boolean;
  className?: string;
}

// ========================================
// Helper Functions
// ========================================

const formatValue = (value: number, format: string, unit?: string): string => {
  switch (format) {
    case 'percent':
      return `${value.toFixed(1)}%`;
    case 'currency':
      return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
      }).format(value);
    case 'time':
      return `${value.toFixed(1)}h`;
    default:
      return `${value.toLocaleString('pt-BR')}${unit ? ` ${unit}` : ''}`;
  }
};

const getTrendIcon = (trend?: 'up' | 'down' | 'stable') => {
  switch (trend) {
    case 'up':
      return <TrendingUp fontSize="small" />;
    case 'down':
      return <TrendingDown fontSize="small" />;
    default:
      return <TrendingFlat fontSize="small" />;
  }
};

const getTrendColor = (trend?: 'up' | 'down' | 'stable', inverted = false) => {
  if (inverted) {
    return trend === 'up' ? 'error' : trend === 'down' ? 'success' : 'default';
  }
  return trend === 'up' ? 'success' : trend === 'down' ? 'error' : 'default';
};

const calculateVariance = (current: number, previous?: number): number | null => {
  if (previous === undefined || previous === 0) return null;
  return ((current - previous) / previous) * 100;
};

// ========================================
// Component
// ========================================

export const ClickableKPI: React.FC<ClickableKPIProps> = ({
  type,
  title,
  value,
  unit,
  previousValue,
  target,
  trend,
  trendData = [],
  icon,
  color = 'primary',
  format = 'number',
  drillThroughPage,
  relatedEquipments = [],
  relatedTags = [],
  onClick,
  compact = false,
  showSparkline = true,
  showTrend = true,
  showTarget = true,
  className,
}) => {
  const theme = useTheme();
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  // Store hooks
  const selectedKPI = useSelectedKPI();
  const { enabled: comparisonMode, kpis: comparisonKPIs } = useComparisonMode();
  const {
    selectKPI,
    clearKPISelection,
    startDrillThrough,
    addToComparison,
    removeFromComparison,
  } = useDashboardSelection();
  const { setEquipments, setTags } = useFilterStore();

  // Computed values
  const isSelected = selectedKPI?.type === type;
  const isInComparison = comparisonKPIs.some(k => k.type === type);
  const variance = calculateVariance(value, previousValue);
  const targetVariance = target ? ((value - target) / target) * 100 : null;

  // Create KPI selection object
  const kpiSelection: KPISelection = useMemo(() => ({
    type,
    value,
    label: title,
    unit,
    trend,
    metadata: {
      equipmentIds: relatedEquipments,
      tagIds: relatedTags,
      previousValue,
      target,
      variance,
    },
  }), [type, value, title, unit, trend, relatedEquipments, relatedTags, previousValue, target, variance]);

  // Handlers
  const handleClick = () => {
    if (comparisonMode) {
      if (isInComparison) {
        removeFromComparison(type);
      } else {
        addToComparison(kpiSelection);
      }
    } else {
      selectKPI(kpiSelection);

      // Apply cross-filter to equipment/tags
      if (relatedEquipments.length > 0) {
        setEquipments(relatedEquipments);
      }
      if (relatedTags.length > 0) {
        setTags(relatedTags);
      }

      onClick?.(kpiSelection);
    }
  };

  const handleDrillThrough = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (drillThroughPage) {
      startDrillThrough({
        sourceKPI: type,
        sourceValue: value,
        targetPage: drillThroughPage,
        filters: {
          equipments: relatedEquipments,
        },
      });
      // Navigate to drill-through page (handled by parent)
    }
  };

  const handlePopoverOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handlePopoverClose = () => {
    setAnchorEl(null);
  };

  const open = Boolean(anchorEl);

  // Color mapping
  const colorMap = {
    primary: theme.palette.primary.main,
    success: theme.palette.success.main,
    warning: theme.palette.warning.main,
    error: theme.palette.error.main,
    info: theme.palette.info.main,
  };

  const kpiColor = colorMap[color];

  return (
    <>
      <Paper
        ref={cardRef}
        component={motion.div}
        whileHover={{ scale: 1.02, y: -2 }}
        whileTap={{ scale: 0.98 }}
        onClick={handleClick}
        onMouseEnter={handlePopoverOpen}
        onMouseLeave={handlePopoverClose}
        elevation={isSelected ? 8 : 2}
        className={className}
        sx={{
          p: compact ? 1.5 : 2,
          cursor: 'pointer',
          position: 'relative',
          overflow: 'hidden',
          transition: 'all 0.2s ease-in-out',
          border: isSelected
            ? `2px solid ${kpiColor}`
            : isInComparison
            ? `2px dashed ${kpiColor}`
            : '2px solid transparent',
          bgcolor: isSelected
            ? alpha(kpiColor, 0.08)
            : theme.palette.background.paper,
          '&:hover': {
            bgcolor: alpha(kpiColor, 0.04),
          },
          // Selection indicator bar
          '&::before': isSelected
            ? {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                width: 4,
                height: '100%',
                bgcolor: kpiColor,
              }
            : undefined,
        }}
      >
        {/* Header */}
        <Stack direction="row" alignItems="center" justifyContent="space-between" mb={1}>
          <Stack direction="row" alignItems="center" spacing={1}>
            {icon && (
              <Box
                sx={{
                  color: kpiColor,
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                {icon}
              </Box>
            )}
            <Typography
              variant={compact ? 'caption' : 'body2'}
              color="text.secondary"
              fontWeight={500}
            >
              {title}
            </Typography>
          </Stack>

          {/* Action buttons */}
          <Stack direction="row" spacing={0.5}>
            {drillThroughPage && (
              <Tooltip title="Drill-through">
                <IconButton
                  size="small"
                  onClick={handleDrillThrough}
                  sx={{ opacity: 0.6, '&:hover': { opacity: 1 } }}
                >
                  <OpenInNew fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            {isSelected && (
              <Tooltip title="Limpar seleção">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    clearKPISelection();
                  }}
                  sx={{ opacity: 0.6, '&:hover': { opacity: 1 } }}
                >
                  <FilterList fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Stack>
        </Stack>

        {/* Value */}
        <Typography
          variant={compact ? 'h5' : 'h4'}
          fontWeight={700}
          color={kpiColor}
          sx={{ mb: 0.5 }}
        >
          {formatValue(value, format, unit)}
        </Typography>

        {/* Trend and variance */}
        {showTrend && (variance !== null || trend) && (
          <Stack direction="row" alignItems="center" spacing={1} mb={1}>
            {trend && (
              <Chip
                size="small"
                icon={getTrendIcon(trend)}
                label={variance !== null ? `${variance > 0 ? '+' : ''}${variance.toFixed(1)}%` : trend}
                color={getTrendColor(trend) as any}
                variant="outlined"
                sx={{ height: 24 }}
              />
            )}
            {previousValue !== undefined && (
              <Typography variant="caption" color="text.secondary">
                vs {formatValue(previousValue, format)}
              </Typography>
            )}
          </Stack>
        )}

        {/* Target indicator */}
        {showTarget && target && (
          <Stack direction="row" alignItems="center" spacing={1} mb={1}>
            <Typography variant="caption" color="text.secondary">
              Meta: {formatValue(target, format)}
            </Typography>
            {targetVariance !== null && (
              <Chip
                size="small"
                label={`${targetVariance > 0 ? '+' : ''}${targetVariance.toFixed(1)}%`}
                color={targetVariance >= 0 ? 'success' : 'error'}
                sx={{ height: 20, fontSize: '0.7rem' }}
              />
            )}
          </Stack>
        )}

        {/* Sparkline */}
        {showSparkline && trendData.length > 0 && (
          <Box sx={{ height: compact ? 30 : 40, mt: 1 }}>
            <ResponsiveContainer width="100%" height={compact ? 30 : 40}>
              <AreaChart data={trendData.map((v, i) => ({ value: v, index: i }))}>
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={kpiColor}
                  fill={kpiColor}
                  fillOpacity={0.2}
                  strokeWidth={1.5}
                  dot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Box>
        )}

        {/* Comparison mode indicator */}
        {comparisonMode && (
          <Box
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
            }}
          >
            <Tooltip title={isInComparison ? 'Remover da comparação' : 'Adicionar à comparação'}>
              <IconButton size="small">
                <Compare
                  fontSize="small"
                  color={isInComparison ? 'primary' : 'disabled'}
                />
              </IconButton>
            </Tooltip>
          </Box>
        )}
      </Paper>

      {/* Advanced Tooltip Popover */}
      <Popover
        sx={{
          pointerEvents: 'none',
        }}
        open={open && !isSelected}
        anchorEl={anchorEl}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'center',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'center',
        }}
        onClose={handlePopoverClose}
        disableRestoreFocus
      >
        <Paper sx={{ p: 2, maxWidth: 300 }}>
          <Typography variant="subtitle2" gutterBottom>
            {title}
          </Typography>

          <Divider sx={{ my: 1 }} />

          {/* Mini trend chart */}
          {trendData.length > 0 && (
            <Box sx={{ height: 60, mb: 1 }}>
              <ResponsiveContainer width="100%" height={60}>
                <AreaChart data={trendData.map((v, i) => ({ value: v, index: i }))}>
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke={kpiColor}
                    fill={kpiColor}
                    fillOpacity={0.2}
                    strokeWidth={1.5}
                    dot={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Box>
          )}

          {/* Stats */}
          <Stack spacing={0.5}>
            <Stack direction="row" justifyContent="space-between">
              <Typography variant="caption" color="text.secondary">
                Valor atual:
              </Typography>
              <Typography variant="caption" fontWeight={600}>
                {formatValue(value, format, unit)}
              </Typography>
            </Stack>

            {previousValue !== undefined && (
              <Stack direction="row" justifyContent="space-between">
                <Typography variant="caption" color="text.secondary">
                  Período anterior:
                </Typography>
                <Typography variant="caption">
                  {formatValue(previousValue, format, unit)}
                </Typography>
              </Stack>
            )}

            {target && (
              <Stack direction="row" justifyContent="space-between">
                <Typography variant="caption" color="text.secondary">
                  Meta:
                </Typography>
                <Typography variant="caption">
                  {formatValue(target, format, unit)}
                </Typography>
              </Stack>
            )}

            {trendData.length > 0 && (
              <>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption" color="text.secondary">
                    Mínimo:
                  </Typography>
                  <Typography variant="caption">
                    {formatValue(Math.min(...trendData), format)}
                  </Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between">
                  <Typography variant="caption" color="text.secondary">
                    Máximo:
                  </Typography>
                  <Typography variant="caption">
                    {formatValue(Math.max(...trendData), format)}
                  </Typography>
                </Stack>
              </>
            )}
          </Stack>

          <Divider sx={{ my: 1 }} />

          <Typography variant="caption" color="text.secondary">
            <Info fontSize="inherit" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
            Clique para filtrar ou {drillThroughPage ? 'use ↗ para detalhes' : 'ver detalhes'}
          </Typography>
        </Paper>
      </Popover>
    </>
  );
};

export default ClickableKPI;
