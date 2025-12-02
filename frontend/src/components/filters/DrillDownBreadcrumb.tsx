/**
 * 🧭 DrillDownBreadcrumb - Dynamic Navigation Breadcrumb
 * ======================================================
 *
 * Shows the current drill-down path and allows navigation back.
 * Integrates with the global filter store.
 *
 * Features:
 * - Shows asset hierarchy path
 * - Click to navigate back to any level
 * - Animated transitions
 * - Responsive design
 */

import React from 'react';
import {
  Box,
  Breadcrumbs,
  Link,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  Stack,
  alpha,
  useTheme,
} from '@mui/material';
import {
  Home,
  NavigateNext,
  Domain,
  PrecisionManufacturing,
  Sensors,
  ArrowBack,
  Close,
} from '@mui/icons-material';
import { useDrillDownPath, useFilterStore } from '../../stores/filterStore';

interface DrillDownBreadcrumbProps {
  // Base/home label
  homeLabel?: string;

  // Show back button
  showBackButton?: boolean;

  // Show clear button
  showClearButton?: boolean;

  // Custom icons for types
  icons?: {
    site?: React.ReactNode;
    area?: React.ReactNode;
    equipment?: React.ReactNode;
    tag?: React.ReactNode;
  };

  // Callback when item is clicked
  onNavigate?: (level: number) => void;

  // Custom class
  className?: string;
}

const DEFAULT_ICONS = {
  site: <Home fontSize="small" />,
  area: <Domain fontSize="small" />,
  equipment: <PrecisionManufacturing fontSize="small" />,
  tag: <Sensors fontSize="small" />,
};

export const DrillDownBreadcrumb: React.FC<DrillDownBreadcrumbProps> = ({
  homeLabel = 'Visão Geral',
  showBackButton = true,
  showClearButton = true,
  icons = DEFAULT_ICONS,
  onNavigate,
  className,
}) => {
  const theme = useTheme();
  const drillDownPath = useDrillDownPath();
  const { drillUp, resetDrillDown } = useFilterStore();

  // Don't render if no path
  if (drillDownPath.length === 0) {
    return null;
  }

  const handleNavigate = (index: number) => {
    if (index === -1) {
      // Go to home
      resetDrillDown();
    } else {
      // Go to specific level (drill up to that point)
      const stepsToGoUp = drillDownPath.length - index - 1;
      if (stepsToGoUp > 0) {
        drillUp(stepsToGoUp);
      }
    }
    onNavigate?.(index);
  };

  const handleBack = () => {
    drillUp(1);
    onNavigate?.(drillDownPath.length - 2);
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'site':
        return icons.site || DEFAULT_ICONS.site;
      case 'area':
        return icons.area || DEFAULT_ICONS.area;
      case 'equipment':
        return icons.equipment || DEFAULT_ICONS.equipment;
      case 'tag':
        return icons.tag || DEFAULT_ICONS.tag;
      default:
        return null;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'site':
        return 'Site';
      case 'area':
        return 'Área';
      case 'equipment':
        return 'Equipamento';
      case 'tag':
        return 'Tag';
      default:
        return type;
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        p: 1.5,
        mb: 2,
        bgcolor: alpha(theme.palette.info.main, 0.05),
        borderRadius: 2,
        border: `1px solid ${alpha(theme.palette.info.main, 0.15)}`,
      }}
      className={className}
    >
      {/* Back Button */}
      {showBackButton && drillDownPath.length > 0 && (
        <Tooltip title="Voltar um nível">
          <IconButton
            size="small"
            onClick={handleBack}
            sx={{
              bgcolor: alpha(theme.palette.primary.main, 0.1),
              '&:hover': {
                bgcolor: alpha(theme.palette.primary.main, 0.2),
              },
            }}
          >
            <ArrowBack fontSize="small" />
          </IconButton>
        </Tooltip>
      )}

      {/* Breadcrumbs */}
      <Breadcrumbs
        separator={<NavigateNext fontSize="small" />}
        sx={{ flex: 1 }}
      >
        {/* Home */}
        <Link
          component="button"
          variant="body2"
          underline="hover"
          onClick={() => handleNavigate(-1)}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            color: 'text.secondary',
            cursor: 'pointer',
            '&:hover': {
              color: 'primary.main',
            },
          }}
        >
          <Home fontSize="small" />
          {homeLabel}
        </Link>

        {/* Path Items */}
        {drillDownPath.map((item, index) => {
          const isLast = index === drillDownPath.length - 1;

          if (isLast) {
            // Current item (not clickable)
            return (
              <Chip
                key={`${item.type}-${item.id}`}
                icon={getIcon(item.type) as React.ReactElement}
                label={
                  <Stack direction="row" alignItems="center" spacing={0.5}>
                    <Typography variant="caption" color="text.secondary">
                      {getTypeLabel(item.type)}:
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {item.name}
                    </Typography>
                  </Stack>
                }
                size="small"
                color="primary"
                variant="filled"
                sx={{ fontWeight: 500 }}
              />
            );
          }

          // Previous items (clickable)
          return (
            <Link
              key={`${item.type}-${item.id}`}
              component="button"
              variant="body2"
              underline="hover"
              onClick={() => handleNavigate(index)}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 0.5,
                color: 'text.secondary',
                cursor: 'pointer',
                '&:hover': {
                  color: 'primary.main',
                },
              }}
            >
              {getIcon(item.type)}
              {item.name}
            </Link>
          );
        })}
      </Breadcrumbs>

      {/* Clear Button */}
      {showClearButton && (
        <Tooltip title="Limpar navegação">
          <IconButton size="small" onClick={resetDrillDown} color="default">
            <Close fontSize="small" />
          </IconButton>
        </Tooltip>
      )}
    </Box>
  );
};

export default DrillDownBreadcrumb;
