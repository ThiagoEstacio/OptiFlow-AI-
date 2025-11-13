/**
 * Professional Analytics Card - MUI Enterprise Style
 * Inspired by Material Dashboard Pro templates
 */
import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Avatar,
  Chip,
  IconButton,
  alpha,
  useTheme
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  MoreVert,
  ArrowUpward,
  ArrowDownward
} from '@mui/icons-material';

interface AnalyticsCardProps {
  title: string;
  value: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'neutral';
  subtitle?: string;
  icon?: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  loading?: boolean;
  progress?: number;
  actionMenu?: React.ReactNode;
}

export const AnalyticsCard: React.FC<AnalyticsCardProps> = ({
  title,
  value,
  change,
  trend = 'neutral',
  subtitle,
  icon,
  color = 'primary',
  loading = false,
  progress,
  actionMenu
}) => {
  const theme = useTheme();

  const getTrendColor = () => {
    if (trend === 'up') return theme.palette.success.main;
    if (trend === 'down') return theme.palette.error.main;
    return theme.palette.text.secondary;
  };

  const getTrendIcon = () => {
    if (trend === 'up') return <ArrowUpward fontSize="small" />;
    if (trend === 'down') return <ArrowDownward fontSize="small" />;
    return null;
  };

  return (
    <Card
      sx={{
        position: 'relative',
        overflow: 'visible',
        borderRadius: 2,
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: theme.shadows[8],
        }
      }}
    >
      {loading && (
        <LinearProgress
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            borderTopLeftRadius: 8,
            borderTopRightRadius: 8
          }}
        />
      )}

      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography
              variant="overline"
              sx={{
                color: 'text.secondary',
                fontWeight: 600,
                letterSpacing: 1,
                fontSize: '0.75rem'
              }}
            >
              {title}
            </Typography>
          </Box>

          {icon && (
            <Avatar
              sx={{
                bgcolor: alpha(theme.palette[color].main, 0.1),
                color: theme.palette[color].main,
                width: 48,
                height: 48
              }}
            >
              {icon}
            </Avatar>
          )}

          {actionMenu && (
            <IconButton size="small" sx={{ ml: 1 }}>
              <MoreVert fontSize="small" />
            </IconButton>
          )}
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 2, mb: 1 }}>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              fontSize: '2rem',
              color: 'text.primary',
              lineHeight: 1.2
            }}
          >
            {value}
          </Typography>

          {change !== undefined && (
            <Chip
              icon={getTrendIcon() || undefined}
              label={`${change > 0 ? '+' : ''}${change}%`}
              size="small"
              sx={{
                bgcolor: alpha(getTrendColor(), 0.1),
                color: getTrendColor(),
                fontWeight: 600,
                fontSize: '0.75rem',
                height: 24
              }}
            />
          )}
        </Box>

        {subtitle && (
          <Typography
            variant="body2"
            sx={{
              color: 'text.secondary',
              fontSize: '0.875rem',
              mb: progress !== undefined ? 2 : 0
            }}
          >
            {subtitle}
          </Typography>
        )}

        {progress !== undefined && (
          <Box sx={{ mt: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                Progress
              </Typography>
              <Typography variant="caption" fontWeight={600}>
                {progress}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{
                height: 6,
                borderRadius: 3,
                bgcolor: alpha(theme.palette[color].main, 0.1),
                '& .MuiLinearProgress-bar': {
                  borderRadius: 3,
                  bgcolor: theme.palette[color].main
                }
              }}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
};
