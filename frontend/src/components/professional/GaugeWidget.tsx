/**
 * Professional Gauge Widget - Industrial Metrics Display
 * Circular gauge for OEE, temperature, speed, pressure, etc.
 */
import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Stack,
  Chip,
  alpha,
  useTheme
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Remove
} from '@mui/icons-material';

interface GaugeWidgetProps {
  title: string;
  value: number;
  min?: number;
  max?: number;
  unit?: string;
  thresholds?: {
    low: number;      // Below this is red
    medium: number;   // Below this is yellow
    high: number;     // Above this is green
  };
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  subtitle?: string;
  size?: 'small' | 'medium' | 'large';
}

export const GaugeWidget: React.FC<GaugeWidgetProps> = ({
  title,
  value,
  min = 0,
  max = 100,
  unit = '%',
  thresholds = { low: 60, medium: 80, high: 95 },
  trend,
  trendValue,
  subtitle,
  size = 'medium'
}) => {
  const theme = useTheme();

  // Calculate percentage
  const percentage = ((value - min) / (max - min)) * 100;
  const clampedPercentage = Math.max(0, Math.min(100, percentage));

  // Determine color based on value and thresholds
  const getColor = () => {
    if (value >= thresholds.high) return theme.palette.success.main;
    if (value >= thresholds.medium) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  const color = getColor();

  // Size configurations
  const sizeConfig = {
    small: { diameter: 120, strokeWidth: 8, fontSize: '1.5rem' },
    medium: { diameter: 160, strokeWidth: 10, fontSize: '2rem' },
    large: { diameter: 200, strokeWidth: 12, fontSize: '2.5rem' }
  };

  const { diameter, strokeWidth, fontSize } = sizeConfig[size];
  const radius = (diameter - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clampedPercentage / 100) * circumference;

  const getTrendIcon = () => {
    if (trend === 'up') return <TrendingUp fontSize="small" />;
    if (trend === 'down') return <TrendingDown fontSize="small" />;
    if (trend === 'neutral') return <Remove fontSize="small" />;
    return null;
  };

  const getTrendColor = () => {
    if (trend === 'up') return theme.palette.success.main;
    if (trend === 'down') return theme.palette.error.main;
    return theme.palette.text.secondary;
  };

  return (
    <Card
      sx={{
        borderRadius: 2,
        transition: 'all 0.3s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: theme.shadows[4]
        }
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Stack spacing={2} alignItems="center">
          {/* Title */}
          <Typography
            variant="h6"
            fontWeight={600}
            textAlign="center"
            sx={{ width: '100%' }}
          >
            {title}
          </Typography>

          {/* Gauge SVG */}
          <Box sx={{ position: 'relative', display: 'inline-flex' }}>
            <svg width={diameter} height={diameter}>
              {/* Background circle */}
              <circle
                cx={diameter / 2}
                cy={diameter / 2}
                r={radius}
                fill="none"
                stroke={alpha(theme.palette.divider, 0.2)}
                strokeWidth={strokeWidth}
              />

              {/* Progress circle */}
              <circle
                cx={diameter / 2}
                cy={diameter / 2}
                r={radius}
                fill="none"
                stroke={color}
                strokeWidth={strokeWidth}
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                strokeLinecap="round"
                transform={`rotate(-90 ${diameter / 2} ${diameter / 2})`}
                style={{
                  transition: 'stroke-dashoffset 0.5s ease-in-out'
                }}
              />
            </svg>

            {/* Center value */}
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Typography
                variant="h3"
                fontWeight={700}
                sx={{
                  fontSize,
                  color,
                  lineHeight: 1
                }}
              >
                {value.toFixed(1)}
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  fontSize: '0.75rem',
                  mt: 0.5
                }}
              >
                {unit}
              </Typography>
            </Box>
          </Box>

          {/* Trend and subtitle */}
          {(trend || subtitle) && (
            <Stack direction="row" spacing={1} alignItems="center">
              {trend && trendValue && (
                <Chip
                  icon={getTrendIcon() || undefined}
                  label={trendValue}
                  size="small"
                  sx={{
                    bgcolor: alpha(getTrendColor(), 0.1),
                    color: getTrendColor(),
                    fontWeight: 600,
                    fontSize: '0.75rem'
                  }}
                />
              )}
              {subtitle && (
                <Typography
                  variant="caption"
                  color="text.secondary"
                  textAlign="center"
                >
                  {subtitle}
                </Typography>
              )}
            </Stack>
          )}

          {/* Threshold indicators */}
          <Stack direction="row" spacing={1} sx={{ width: '100%', justifyContent: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: theme.palette.error.main
                }}
              />
              <Typography variant="caption" color="text.secondary">
                &lt;{thresholds.low}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: theme.palette.warning.main
                }}
              />
              <Typography variant="caption" color="text.secondary">
                {thresholds.low}-{thresholds.medium}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: theme.palette.success.main
                }}
              />
              <Typography variant="caption" color="text.secondary">
                &gt;{thresholds.medium}
              </Typography>
            </Box>
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
};
