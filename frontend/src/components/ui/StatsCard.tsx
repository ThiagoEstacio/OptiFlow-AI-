import React from 'react';
import { Card, CardContent, Box, Typography, Avatar, Chip, LinearProgress } from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    direction: 'up' | 'down';
    label?: string;
  };
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  subtitle?: string;
  progress?: number;
  gradient?: string;
}

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  icon,
  trend,
  color = 'primary',
  subtitle,
  progress,
  gradient,
}) => {
  return (
    <Card
      sx={{
        height: '100%',
        background: gradient || 'white',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 4,
        },
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography
              variant="body2"
              color={gradient ? 'white' : 'text.secondary'}
              gutterBottom
              sx={{ fontWeight: 500 }}
            >
              {title}
            </Typography>
            <Typography
              variant="h4"
              fontWeight="bold"
              color={gradient ? 'white' : 'text.primary'}
              sx={{ mb: 0.5 }}
            >
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color={gradient ? 'rgba(255,255,255,0.8)' : 'text.secondary'}>
                {subtitle}
              </Typography>
            )}
          </Box>

          {icon && (
            <Avatar
              sx={{
                bgcolor: gradient ? 'rgba(255,255,255,0.2)' : `${color}.light`,
                color: gradient ? 'white' : `${color}.main`,
                width: 56,
                height: 56,
              }}
            >
              {icon}
            </Avatar>
          )}
        </Box>

        {trend && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              icon={trend.direction === 'up' ? <TrendingUp /> : <TrendingDown />}
              label={`${trend.value > 0 ? '+' : ''}${trend.value}%`}
              size="small"
              color={trend.direction === 'up' ? 'success' : 'error'}
              sx={{ height: 24 }}
            />
            {trend.label && (
              <Typography variant="caption" color={gradient ? 'rgba(255,255,255,0.8)' : 'text.secondary'}>
                {trend.label}
              </Typography>
            )}
          </Box>
        )}

        {progress !== undefined && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress
              variant="determinate"
              value={progress}
              color={color}
              sx={{
                height: 6,
                borderRadius: 3,
                bgcolor: gradient ? 'rgba(255,255,255,0.2)' : 'grey.200',
              }}
            />
            <Typography
              variant="caption"
              color={gradient ? 'rgba(255,255,255,0.8)' : 'text.secondary'}
              sx={{ mt: 0.5, display: 'block' }}
            >
              {progress}% de capacidade
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

interface MiniStatsCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color?: string;
}

export const MiniStatsCard: React.FC<MiniStatsCardProps> = ({ title, value, icon, color = '#2196F3' }) => {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        p: 2,
        borderRadius: 2,
        bgcolor: 'white',
        border: '1px solid',
        borderColor: 'grey.200',
        transition: 'all 0.2s',
        '&:hover': {
          borderColor: color,
          boxShadow: `0 0 0 2px ${color}20`,
        },
      }}
    >
      <Box
        sx={{
          width: 48,
          height: 48,
          borderRadius: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: `${color}20`,
          color: color,
          mr: 2,
        }}
      >
        {icon}
      </Box>
      <Box>
        <Typography variant="h5" fontWeight="bold">
          {value}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {title}
        </Typography>
      </Box>
    </Box>
  );
};
