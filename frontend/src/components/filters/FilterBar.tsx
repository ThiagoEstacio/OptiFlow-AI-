/**
 * 🎛️ FilterBar Component - Sprint 6: Cross-Filtering
 * ===================================================
 *
 * Global filter bar that appears at the top of dashboards.
 * Provides consistent filtering across all views.
 *
 * Features:
 * - Time range selector
 * - Equipment multi-select
 * - Area filter
 * - Status filter chips
 * - Clear filters button
 * - Share URL button
 */

import React, { useState, useMemo } from 'react';
import {
  Box,
  Paper,
  Stack,
  Chip,
  Button,
  IconButton,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Badge,
  FormControlLabel,
  Switch,
  Typography,
  Popover,
  Checkbox,
  TextField,
  InputAdornment,
  alpha,
  useTheme,
} from '@mui/material';
import {
  AccessTime,
  FilterList,
  Clear,
  Share,
  ExpandMore,
  Check,
  Search,
  PrecisionManufacturing,
  Domain,
  PlayArrow,
  Stop,
  Pause,
  Build,
  Warning,
  ContentCopy,
  Link as LinkIcon,
} from '@mui/icons-material';
import { useFilterStore, useHasActiveFilters, TimeRangePreset } from '../../stores/filterStore';
import { useURLFilters } from '../../hooks/useURLFilters';

// Time range options
const TIME_RANGE_OPTIONS: { value: TimeRangePreset; label: string }[] = [
  { value: '1h', label: '1 Hora' },
  { value: '4h', label: '4 Horas' },
  { value: '8h', label: '8 Horas (Turno)' },
  { value: '24h', label: '24 Horas' },
  { value: '7d', label: '7 Dias' },
  { value: '30d', label: '30 Dias' },
];

// Status options with icons
const STATUS_OPTIONS = [
  { value: 'running' as const, label: 'Rodando', icon: <PlayArrow fontSize="small" />, color: 'success' },
  { value: 'stopped' as const, label: 'Parado', icon: <Stop fontSize="small" />, color: 'error' },
  { value: 'idle' as const, label: 'Ocioso', icon: <Pause fontSize="small" />, color: 'warning' },
  { value: 'maintenance' as const, label: 'Manutenção', icon: <Build fontSize="small" />, color: 'info' },
  { value: 'alarm' as const, label: 'Alarme', icon: <Warning fontSize="small" />, color: 'error' },
];

interface Equipment {
  id: string;
  name: string;
  area?: string;
}

interface Area {
  id: string;
  name: string;
}

interface FilterBarProps {
  // Available options
  equipments?: Equipment[];
  areas?: Area[];

  // Visibility options
  showTimeRange?: boolean;
  showEquipments?: boolean;
  showAreas?: boolean;
  showStatuses?: boolean;
  showCrossFilterToggle?: boolean;
  showShareButton?: boolean;

  // Compact mode for smaller spaces
  compact?: boolean;

  // Custom class
  className?: string;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  equipments = [],
  areas = [],
  showTimeRange = true,
  showEquipments = true,
  showAreas = true,
  showStatuses = true,
  showCrossFilterToggle = true,
  showShareButton = true,
  compact = false,
  className,
}) => {
  const theme = useTheme();
  const hasActiveFilters = useHasActiveFilters();
  const { copyShareableURL } = useURLFilters();

  // Local state for menus/popovers
  const [timeAnchor, setTimeAnchor] = useState<null | HTMLElement>(null);
  const [equipmentAnchor, setEquipmentAnchor] = useState<null | HTMLElement>(null);
  const [areaAnchor, setAreaAnchor] = useState<null | HTMLElement>(null);
  const [equipmentSearch, setEquipmentSearch] = useState('');
  const [copied, setCopied] = useState(false);

  // Get filter state and actions
  const {
    timeRange,
    selectedEquipments,
    selectedAreas,
    selectedStatuses,
    crossFilterEnabled,
    setTimeRangePreset,
    setEquipments,
    setAreas,
    toggleEquipment,
    toggleArea,
    toggleStatus,
    setCrossFilterEnabled,
    resetFilters,
  } = useFilterStore();

  // Filter equipments by search
  const filteredEquipments = useMemo(() => {
    if (!equipmentSearch) return equipments;
    const search = equipmentSearch.toLowerCase();
    return equipments.filter(
      (e) =>
        e.name.toLowerCase().includes(search) ||
        e.id.toLowerCase().includes(search) ||
        e.area?.toLowerCase().includes(search)
    );
  }, [equipments, equipmentSearch]);

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (timeRange.preset !== '24h') count++;
    if (selectedEquipments.length > 0) count++;
    if (selectedAreas.length > 0) count++;
    if (selectedStatuses.length > 0) count++;
    return count;
  }, [timeRange.preset, selectedEquipments, selectedAreas, selectedStatuses]);

  // Handle share URL
  const handleShare = async () => {
    const success = await copyShareableURL();
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Get current time range label
  const currentTimeLabel = TIME_RANGE_OPTIONS.find((o) => o.value === timeRange.preset)?.label || '24 Horas';

  return (
    <Paper
      elevation={0}
      sx={{
        p: compact ? 1 : 1.5,
        mb: 2,
        bgcolor: alpha(theme.palette.primary.main, 0.02),
        border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
        borderRadius: 2,
      }}
      className={className}
    >
      <Stack
        direction={{ xs: 'column', md: 'row' }}
        spacing={compact ? 1 : 2}
        alignItems={{ xs: 'stretch', md: 'center' }}
        justifyContent="space-between"
      >
        {/* Left: Filter Controls */}
        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
          {/* Filter Icon */}
          <Badge badgeContent={activeFilterCount} color="primary" invisible={activeFilterCount === 0}>
            <FilterList color="action" />
          </Badge>

          {/* Time Range Selector */}
          {showTimeRange && (
            <>
              <Chip
                icon={<AccessTime />}
                label={currentTimeLabel}
                onClick={(e) => setTimeAnchor(e.currentTarget)}
                onDelete={timeRange.preset !== '24h' ? () => setTimeRangePreset('24h') : undefined}
                deleteIcon={timeRange.preset !== '24h' ? <Clear /> : undefined}
                variant={timeRange.preset !== '24h' ? 'filled' : 'outlined'}
                color={timeRange.preset !== '24h' ? 'primary' : 'default'}
                sx={{ fontWeight: 500 }}
              />
              <Menu
                anchorEl={timeAnchor}
                open={Boolean(timeAnchor)}
                onClose={() => setTimeAnchor(null)}
              >
                {TIME_RANGE_OPTIONS.map((option) => (
                  <MenuItem
                    key={option.value}
                    onClick={() => {
                      setTimeRangePreset(option.value);
                      setTimeAnchor(null);
                    }}
                    selected={timeRange.preset === option.value}
                  >
                    <ListItemIcon>
                      {timeRange.preset === option.value && <Check fontSize="small" />}
                    </ListItemIcon>
                    <ListItemText>{option.label}</ListItemText>
                  </MenuItem>
                ))}
              </Menu>
            </>
          )}

          {/* Area Filter */}
          {showAreas && areas.length > 0 && (
            <>
              <Chip
                icon={<Domain />}
                label={
                  selectedAreas.length > 0
                    ? `${selectedAreas.length} área${selectedAreas.length > 1 ? 's' : ''}`
                    : 'Áreas'
                }
                onClick={(e) => setAreaAnchor(e.currentTarget)}
                onDelete={selectedAreas.length > 0 ? () => setAreas([]) : undefined}
                deleteIcon={selectedAreas.length > 0 ? <Clear /> : undefined}
                variant={selectedAreas.length > 0 ? 'filled' : 'outlined'}
                color={selectedAreas.length > 0 ? 'primary' : 'default'}
              />
              <Popover
                open={Boolean(areaAnchor)}
                anchorEl={areaAnchor}
                onClose={() => setAreaAnchor(null)}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
              >
                <Box sx={{ p: 1, minWidth: 200 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ px: 1 }}>
                    Selecione as áreas
                  </Typography>
                  {areas.map((area) => (
                    <MenuItem
                      key={area.id}
                      onClick={() => toggleArea(area.id)}
                      dense
                    >
                      <Checkbox
                        checked={selectedAreas.includes(area.id)}
                        size="small"
                        sx={{ p: 0.5, mr: 1 }}
                      />
                      <ListItemText primary={area.name} />
                    </MenuItem>
                  ))}
                </Box>
              </Popover>
            </>
          )}

          {/* Equipment Filter */}
          {showEquipments && equipments.length > 0 && (
            <>
              <Chip
                icon={<PrecisionManufacturing />}
                label={
                  selectedEquipments.length > 0
                    ? `${selectedEquipments.length} equip.`
                    : 'Equipamentos'
                }
                onClick={(e) => setEquipmentAnchor(e.currentTarget)}
                onDelete={selectedEquipments.length > 0 ? () => setEquipments([]) : undefined}
                deleteIcon={selectedEquipments.length > 0 ? <Clear /> : undefined}
                variant={selectedEquipments.length > 0 ? 'filled' : 'outlined'}
                color={selectedEquipments.length > 0 ? 'primary' : 'default'}
              />
              <Popover
                open={Boolean(equipmentAnchor)}
                anchorEl={equipmentAnchor}
                onClose={() => {
                  setEquipmentAnchor(null);
                  setEquipmentSearch('');
                }}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
              >
                <Box sx={{ p: 1, minWidth: 280, maxHeight: 400 }}>
                  <TextField
                    size="small"
                    placeholder="Buscar equipamento..."
                    value={equipmentSearch}
                    onChange={(e) => setEquipmentSearch(e.target.value)}
                    fullWidth
                    sx={{ mb: 1 }}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Search fontSize="small" />
                        </InputAdornment>
                      ),
                    }}
                  />
                  <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                    {filteredEquipments.map((eq) => (
                      <MenuItem
                        key={eq.id}
                        onClick={() => toggleEquipment(eq.id)}
                        dense
                      >
                        <Checkbox
                          checked={selectedEquipments.includes(eq.id)}
                          size="small"
                          sx={{ p: 0.5, mr: 1 }}
                        />
                        <ListItemText
                          primary={eq.name}
                          secondary={eq.area}
                          primaryTypographyProps={{ variant: 'body2' }}
                          secondaryTypographyProps={{ variant: 'caption' }}
                        />
                      </MenuItem>
                    ))}
                    {filteredEquipments.length === 0 && (
                      <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>
                        Nenhum equipamento encontrado
                      </Typography>
                    )}
                  </Box>
                </Box>
              </Popover>
            </>
          )}

          {/* Status Chips */}
          {showStatuses && (
            <Stack direction="row" spacing={0.5}>
              {STATUS_OPTIONS.map((status) => (
                <Chip
                  key={status.value}
                  icon={status.icon}
                  label={compact ? undefined : status.label}
                  size="small"
                  onClick={() => toggleStatus(status.value)}
                  variant={selectedStatuses.includes(status.value) ? 'filled' : 'outlined'}
                  color={selectedStatuses.includes(status.value) ? (status.color as any) : 'default'}
                  sx={{
                    '& .MuiChip-icon': { ml: compact ? 0.5 : undefined },
                  }}
                />
              ))}
            </Stack>
          )}

          {/* Clear Filters */}
          {hasActiveFilters && (
            <Tooltip title="Limpar filtros">
              <IconButton size="small" onClick={resetFilters} color="error">
                <Clear fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Stack>

        {/* Right: Options */}
        <Stack direction="row" spacing={1} alignItems="center">
          {/* Cross-filter Toggle */}
          {showCrossFilterToggle && (
            <Tooltip title="Cross-filtering: clique em um gráfico para filtrar outros">
              <FormControlLabel
                control={
                  <Switch
                    size="small"
                    checked={crossFilterEnabled}
                    onChange={(e) => setCrossFilterEnabled(e.target.checked)}
                  />
                }
                label={
                  <Typography variant="caption" color="text.secondary">
                    Cross-filter
                  </Typography>
                }
                sx={{ mr: 0 }}
              />
            </Tooltip>
          )}

          {/* Share Button */}
          {showShareButton && (
            <Tooltip title={copied ? 'Link copiado!' : 'Copiar link com filtros'}>
              <IconButton size="small" onClick={handleShare} color={copied ? 'success' : 'default'}>
                {copied ? <Check fontSize="small" /> : <LinkIcon fontSize="small" />}
              </IconButton>
            </Tooltip>
          )}
        </Stack>
      </Stack>
    </Paper>
  );
};

export default FilterBar;
