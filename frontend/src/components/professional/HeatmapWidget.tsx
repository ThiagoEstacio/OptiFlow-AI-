/**
 * Professional Heatmap Widget - Pattern Analysis Display
 * 2D heatmap for production patterns, hourly metrics, correlation analysis
 */
import React from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Typography,
  Box,
  Stack,
  Tooltip,
  IconButton,
  useTheme,
  alpha
} from '@mui/material';
import {
  MoreVert,
  Info
} from '@mui/icons-material';

export interface HeatmapDataPoint {
  x: string | number;
  y: string | number;
  value: number;
  label?: string;
}

interface HeatmapWidgetProps {
  title: string;
  data: HeatmapDataPoint[];
  xLabels: string[];
  yLabels: string[];
  colorScale?: 'blue' | 'green' | 'red' | 'purple' | 'gradient';
  minValue?: number;
  maxValue?: number;
  showValues?: boolean;
  unit?: string;
  subtitle?: string;
}

export const HeatmapWidget: React.FC<HeatmapWidgetProps> = ({
  title,
  data,
  xLabels,
  yLabels,
  colorScale = 'blue',
  minValue,
  maxValue,
  showValues = true,
  unit = '',
  subtitle
}) => {
  const theme = useTheme();

  // Calculate min/max if not provided
  const values = data.map(d => d.value);
  const min = minValue ?? Math.min(...values);
  const max = maxValue ?? Math.max(...values);

  // Get color for a value
  const getColor = (value: number): string => {
    const normalized = (value - min) / (max - min);

    const colorScales = {
      blue: {
        light: theme.palette.info.light,
        main: theme.palette.info.main,
        dark: theme.palette.info.dark
      },
      green: {
        light: theme.palette.success.light,
        main: theme.palette.success.main,
        dark: theme.palette.success.dark
      },
      red: {
        light: theme.palette.error.light,
        main: theme.palette.error.main,
        dark: theme.palette.error.dark
      },
      purple: {
        light: theme.palette.secondary.light,
        main: theme.palette.secondary.main,
        dark: theme.palette.secondary.dark
      },
      gradient: {
        light: theme.palette.info.light,
        main: theme.palette.warning.main,
        dark: theme.palette.error.dark
      }
    };

    const scale = colorScales[colorScale];

    // Interpolate between light, main, and dark
    if (normalized < 0.5) {
      // Light to main
      const t = normalized * 2;
      return alpha(scale.light, 0.3 + t * 0.4);
    } else {
      // Main to dark
      const t = (normalized - 0.5) * 2;
      return alpha(scale.main, 0.7 + t * 0.3);
    }
  };

  // Get contrasting text color
  const getTextColor = (value: number): string => {
    const normalized = (value - min) / (max - min);
    return normalized > 0.6 ? '#ffffff' : theme.palette.text.primary;
  };

  // Find data point for coordinates
  const getDataPoint = (x: string, y: string): HeatmapDataPoint | undefined => {
    return data.find(d => d.x === x && d.y === y);
  };

  const cellSize = 60;
  const labelWidth = 80;
  const labelHeight = 40;

  return (
    <Card
      sx={{
        borderRadius: 2,
        height: '100%',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <CardHeader
        title={
          <Typography variant="h6" fontWeight={600}>
            {title}
          </Typography>
        }
        subheader={subtitle}
        action={
          <IconButton size="small">
            <MoreVert />
          </IconButton>
        }
        sx={{ pb: 1 }}
      />

      <CardContent sx={{ flex: 1, overflow: 'auto' }}>
        {data.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              py: 6,
              color: 'text.secondary'
            }}
          >
            <Info sx={{ fontSize: 48, mb: 2, opacity: 0.3 }} />
            <Typography variant="body2">No data to display</Typography>
          </Box>
        ) : (
          <Box sx={{ overflowX: 'auto', overflowY: 'auto' }}>
            <Box sx={{ minWidth: xLabels.length * cellSize + labelWidth }}>
              {/* X-axis labels */}
              <Stack direction="row" spacing={0} mb={0.5}>
                <Box sx={{ width: labelWidth }} />
                {xLabels.map((label) => (
                  <Box
                    key={label}
                    sx={{
                      width: cellSize,
                      textAlign: 'center',
                      px: 0.5
                    }}
                  >
                    <Typography
                      variant="caption"
                      fontWeight={600}
                      sx={{
                        color: 'text.secondary',
                        fontSize: '0.7rem',
                        display: 'block',
                        transform: 'rotate(-45deg)',
                        transformOrigin: 'center',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {label}
                    </Typography>
                  </Box>
                ))}
              </Stack>

              {/* Heatmap grid */}
              <Stack spacing={0.5}>
                {yLabels.map((yLabel) => (
                  <Stack key={yLabel} direction="row" spacing={0.5} alignItems="center">
                    {/* Y-axis label */}
                    <Box
                      sx={{
                        width: labelWidth,
                        pr: 1,
                        textAlign: 'right'
                      }}
                    >
                      <Typography
                        variant="caption"
                        fontWeight={600}
                        sx={{
                          color: 'text.secondary',
                          fontSize: '0.75rem'
                        }}
                      >
                        {yLabel}
                      </Typography>
                    </Box>

                    {/* Cells */}
                    {xLabels.map((xLabel) => {
                      const dataPoint = getDataPoint(xLabel, yLabel);
                      const value = dataPoint?.value ?? 0;

                      return (
                        <Tooltip
                          key={`${xLabel}-${yLabel}`}
                          title={
                            <Box>
                              <Typography variant="caption" display="block">
                                <strong>{xLabel} × {yLabel}</strong>
                              </Typography>
                              <Typography variant="caption">
                                {value.toFixed(1)}{unit}
                              </Typography>
                              {dataPoint?.label && (
                                <Typography variant="caption" display="block">
                                  {dataPoint.label}
                                </Typography>
                              )}
                            </Box>
                          }
                          arrow
                        >
                          <Box
                            sx={{
                              width: cellSize,
                              height: cellSize,
                              bgcolor: getColor(value),
                              borderRadius: 1,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              cursor: 'pointer',
                              transition: 'all 0.2s',
                              border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
                              '&:hover': {
                                transform: 'scale(1.05)',
                                boxShadow: theme.shadows[4],
                                zIndex: 1
                              }
                            }}
                          >
                            {showValues && (
                              <Typography
                                variant="caption"
                                fontWeight={600}
                                sx={{
                                  color: getTextColor(value),
                                  fontSize: '0.7rem'
                                }}
                              >
                                {value.toFixed(0)}
                              </Typography>
                            )}
                          </Box>
                        </Tooltip>
                      );
                    })}
                  </Stack>
                ))}
              </Stack>

              {/* Legend */}
              <Box sx={{ mt: 3, mb: 1 }}>
                <Stack direction="row" spacing={1} alignItems="center" justifyContent="center">
                  <Typography variant="caption" color="text.secondary">
                    {min.toFixed(0)}{unit}
                  </Typography>

                  <Box
                    sx={{
                      width: 200,
                      height: 16,
                      borderRadius: 1,
                      background: `linear-gradient(to right,
                        ${getColor(min)},
                        ${getColor((min + max) / 2)},
                        ${getColor(max)})`,
                      border: `1px solid ${theme.palette.divider}`
                    }}
                  />

                  <Typography variant="caption" color="text.secondary">
                    {max.toFixed(0)}{unit}
                  </Typography>
                </Stack>
              </Box>
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};
