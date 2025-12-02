/**
 * 🔗 CrossFilterPanel - Painel de Cross-Filtering Visual
 * =======================================================
 *
 * Mostra visualmente os filtros ativos e permite gerenciá-los.
 * Inspirado no Power BI Filter Pane.
 */

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Stack,
  Chip,
  IconButton,
  Tooltip,
  Divider,
  Button,
  alpha,
  useTheme,
  Collapse,
  Badge,
} from '@mui/material';
import {
  FilterList,
  Clear,
  Tune,
  ArrowBack,
  Link as LinkIcon,
  LinkOff,
  Visibility,
  VisibilityOff,
  KeyboardArrowDown,
  KeyboardArrowUp,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import {
  useFilterStore,
  useHasActiveFilters,
  useDrillDownPath,
} from '../../stores/filterStore';
import {
  useDashboardSelection,
  useSelectedKPI,
  useDrillThroughContext,
  useComparisonMode,
} from '../../stores/dashboardSelectionStore';

interface CrossFilterPanelProps {
  showWhenEmpty?: boolean;
  position?: 'top' | 'side';
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export const CrossFilterPanel: React.FC<CrossFilterPanelProps> = ({
  showWhenEmpty = false,
  position = 'top',
  collapsible = true,
  defaultExpanded = true,
}) => {
  const theme = useTheme();
  const [expanded, setExpanded] = React.useState(defaultExpanded);

  // Filter store
  const {
    timeRange,
    selectedEquipments,
    selectedAreas,
    selectedTags,
    selectedStatuses,
    crossFilterEnabled,
    setCrossFilterEnabled,
    resetFilters,
    resetDrillDown,
  } = useFilterStore();

  const hasActiveFilters = useHasActiveFilters();
  const drillDownPath = useDrillDownPath();

  // Dashboard selection store
  const selectedKPI = useSelectedKPI();
  const drillThroughContext = useDrillThroughContext();
  const { enabled: comparisonMode, kpis: comparisonKPIs } = useComparisonMode();
  const {
    clearKPISelection,
    exitDrillThrough,
    goBackDrillThrough,
    clearComparison,
  } = useDashboardSelection();

  // Compute total active filters
  const totalFilters =
    (selectedKPI ? 1 : 0) +
    selectedEquipments.length +
    selectedAreas.length +
    selectedTags.length +
    selectedStatuses.length +
    drillDownPath.length +
    comparisonKPIs.length;

  // Don't render if no filters and showWhenEmpty is false
  if (!showWhenEmpty && totalFilters === 0 && !drillThroughContext) {
    return null;
  }

  const handleClearAll = () => {
    resetFilters();
    clearKPISelection();
    exitDrillThrough();
    clearComparison();
  };

  const isHorizontal = position === 'top';

  return (
    <Paper
      component={motion.div}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      elevation={1}
      sx={{
        p: 1.5,
        mb: isHorizontal ? 2 : 0,
        mr: isHorizontal ? 0 : 2,
        bgcolor: alpha(theme.palette.primary.main, 0.02),
        border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
        width: isHorizontal ? '100%' : 280,
      }}
    >
      {/* Header */}
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
        onClick={() => collapsible && setExpanded(!expanded)}
        sx={{ cursor: collapsible ? 'pointer' : 'default' }}
      >
        <Stack direction="row" alignItems="center" spacing={1}>
          <Badge badgeContent={totalFilters} color="primary" max={99}>
            <FilterList color="primary" />
          </Badge>
          <Typography variant="subtitle2" color="primary">
            Filtros Ativos
          </Typography>
        </Stack>

        <Stack direction="row" alignItems="center" spacing={0.5}>
          {/* Cross-filter toggle */}
          <Tooltip title={crossFilterEnabled ? 'Desativar cross-filter' : 'Ativar cross-filter'}>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                setCrossFilterEnabled(!crossFilterEnabled);
              }}
            >
              {crossFilterEnabled ? (
                <LinkIcon fontSize="small" color="primary" />
              ) : (
                <LinkOff fontSize="small" color="disabled" />
              )}
            </IconButton>
          </Tooltip>

          {/* Clear all */}
          {totalFilters > 0 && (
            <Tooltip title="Limpar todos os filtros">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleClearAll();
                }}
              >
                <Clear fontSize="small" />
              </IconButton>
            </Tooltip>
          )}

          {/* Expand/collapse */}
          {collapsible && (
            <IconButton size="small">
              {expanded ? <KeyboardArrowUp /> : <KeyboardArrowDown />}
            </IconButton>
          )}
        </Stack>
      </Stack>

      {/* Collapsible content */}
      <Collapse in={expanded}>
        <Box sx={{ mt: 1.5 }}>
          {/* Drill-through context */}
          {drillThroughContext && (
            <>
              <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                <Typography variant="caption" color="text.secondary">
                  Drill-through:
                </Typography>
                <Chip
                  size="small"
                  label={`${drillThroughContext.sourceKPI}: ${drillThroughContext.sourceValue}`}
                  color="secondary"
                  onDelete={exitDrillThrough}
                  icon={<ArrowBack />}
                  onClick={goBackDrillThrough}
                />
              </Stack>
              <Divider sx={{ my: 1 }} />
            </>
          )}

          {/* Selected KPI */}
          {selectedKPI && (
            <Stack direction="row" alignItems="center" spacing={1} mb={1} flexWrap="wrap">
              <Typography variant="caption" color="text.secondary">
                KPI Selecionado:
              </Typography>
              <Chip
                size="small"
                label={`${selectedKPI.label}: ${selectedKPI.value}${selectedKPI.unit || ''}`}
                color="primary"
                variant="filled"
                onDelete={clearKPISelection}
              />
            </Stack>
          )}

          {/* Comparison mode */}
          {comparisonMode && comparisonKPIs.length > 0 && (
            <Stack direction="row" alignItems="center" spacing={1} mb={1} flexWrap="wrap">
              <Typography variant="caption" color="text.secondary">
                Comparando:
              </Typography>
              {comparisonKPIs.map((kpi) => (
                <Chip
                  key={kpi.type}
                  size="small"
                  label={`${kpi.label}: ${kpi.value}`}
                  variant="outlined"
                  color="secondary"
                />
              ))}
              <Button size="small" onClick={clearComparison}>
                Limpar
              </Button>
            </Stack>
          )}

          {/* Drill-down path */}
          {drillDownPath.length > 0 && (
            <Stack direction="row" alignItems="center" spacing={1} mb={1} flexWrap="wrap">
              <Typography variant="caption" color="text.secondary">
                Drill-down:
              </Typography>
              {drillDownPath.map((item, index) => (
                <React.Fragment key={`${item.type}-${item.id}`}>
                  {index > 0 && (
                    <Typography variant="caption" color="text.disabled">
                      →
                    </Typography>
                  )}
                  <Chip
                    size="small"
                    label={item.name}
                    variant="outlined"
                    onClick={() => {
                      // Drill up to this level
                      const stepsBack = drillDownPath.length - index - 1;
                      if (stepsBack > 0) {
                        useFilterStore.getState().drillUp(stepsBack);
                      }
                    }}
                  />
                </React.Fragment>
              ))}
              <IconButton size="small" onClick={resetDrillDown}>
                <Clear fontSize="small" />
              </IconButton>
            </Stack>
          )}

          {/* Equipment filters */}
          {selectedEquipments.length > 0 && (
            <Stack direction="row" alignItems="center" spacing={1} mb={1} flexWrap="wrap" useFlexGap>
              <Typography variant="caption" color="text.secondary">
                Equipamentos:
              </Typography>
              {selectedEquipments.slice(0, 5).map((eq) => (
                <Chip
                  key={eq}
                  size="small"
                  label={eq}
                  variant="outlined"
                  onDelete={() => {
                    useFilterStore.getState().toggleEquipment(eq);
                  }}
                />
              ))}
              {selectedEquipments.length > 5 && (
                <Chip
                  size="small"
                  label={`+${selectedEquipments.length - 5}`}
                  variant="outlined"
                />
              )}
            </Stack>
          )}

          {/* Area filters */}
          {selectedAreas.length > 0 && (
            <Stack direction="row" alignItems="center" spacing={1} mb={1} flexWrap="wrap" useFlexGap>
              <Typography variant="caption" color="text.secondary">
                Áreas:
              </Typography>
              {selectedAreas.map((area) => (
                <Chip
                  key={area}
                  size="small"
                  label={area}
                  variant="outlined"
                  color="info"
                  onDelete={() => {
                    useFilterStore.getState().toggleArea(area);
                  }}
                />
              ))}
            </Stack>
          )}

          {/* Status filters */}
          {selectedStatuses.length > 0 && (
            <Stack direction="row" alignItems="center" spacing={1} mb={1} flexWrap="wrap" useFlexGap>
              <Typography variant="caption" color="text.secondary">
                Status:
              </Typography>
              {selectedStatuses.map((status) => (
                <Chip
                  key={status}
                  size="small"
                  label={status}
                  variant="outlined"
                  color={
                    status === 'running'
                      ? 'success'
                      : status === 'stopped' || status === 'alarm'
                      ? 'error'
                      : 'warning'
                  }
                  onDelete={() => {
                    useFilterStore.getState().toggleStatus(status);
                  }}
                />
              ))}
            </Stack>
          )}

          {/* Time range */}
          <Stack direction="row" alignItems="center" spacing={1}>
            <Typography variant="caption" color="text.secondary">
              Período:
            </Typography>
            <Chip
              size="small"
              label={timeRange.preset === 'custom' ? 'Personalizado' : timeRange.preset}
              variant="outlined"
            />
          </Stack>

          {/* Empty state */}
          {totalFilters === 0 && (
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: 'block', textAlign: 'center', py: 2 }}
            >
              Clique em KPIs ou gráficos para aplicar filtros
            </Typography>
          )}
        </Box>
      </Collapse>
    </Paper>
  );
};

export default CrossFilterPanel;
