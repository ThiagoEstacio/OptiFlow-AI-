/**
 * Professional Stat Widget - Enterprise Grade
 * Modern, animated, and highly visual
 */
import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Avatar,
  Stack,
  Skeleton,
  alpha,
  useTheme,
  Tooltip
} from '@mui/material';
import { keyframes } from '@mui/system';

const pulse = keyframes`
  0% {
    box-shadow: 0 0 0 0 currentColor;
  }
  70% {
    box-shadow: 0 0 0 10px transparent;
  }
  100% {
    box-shadow: 0 0 0 0 transparent;
  }
`;

interface StatWidgetProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  gradient?: boolean;
  subtitle?: string;
  footer?: string;
  loading?: boolean;
  animate?: boolean;
  onClick?: () => void;
}

export const StatWidget: React.FC<StatWidgetProps> = ({
  title,
  value,
  icon,
  color = 'primary',
  gradient = false,
  subtitle,
  footer,
  loading = false,
  animate = false,
  onClick
}) => {
  const theme = useTheme();

  const gradientColors = {
    primary: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
    secondary: `linear-gradient(135deg, ${theme.palette.secondary.main} 0%, ${theme.palette.secondary.dark} 100%)`,
    success: `linear-gradient(135deg, ${theme.palette.success.main} 0%, ${theme.palette.success.dark} 100%)`,
    error: `linear-gradient(135deg, ${theme.palette.error.main} 0%, ${theme.palette.error.dark} 100%)`,
    warning: `linear-gradient(135deg, ${theme.palette.warning.main} 0%, ${theme.palette.warning.dark} 100%)`,
    info: `linear-gradient(135deg, ${theme.palette.info.main} 0%, ${theme.palette.info.dark} 100%)`
  };

  return (
    <Card
      onClick={onClick}
      sx={{
        position: 'relative',
        overflow: 'hidden',
        borderRadius: 3,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        background: gradient ? gradientColors[color] : 'background.paper',
        color: gradient ? 'white' : 'text.primary',
        '&:hover': onClick
          ? {
              transform: 'translateY(-8px)',
              boxShadow: theme.shadows[12]
            }
          : {},
        '&::before': gradient
          ? {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(255, 255, 255, 0.1)',
              opacity: 0,
              transition: 'opacity 0.3s',
            }
          : {},
        '&:hover::before': {
          opacity: 1
        }
      }}
    >
      {/* Decorative background pattern */}
      <Box
        sx={{
          position: 'absolute',
          top: -50,
          right: -50,
          width: 150,
          height: 150,
          borderRadius: '50%',
          bgcolor: gradient ? 'rgba(255, 255, 255, 0.1)' : alpha(theme.palette[color].main, 0.05),
          pointerEvents: 'none'
        }}
      />

      <CardContent sx={{ p: 3, position: 'relative', zIndex: 1 }}>
        <Stack spacing={2}>
          {/* Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography
              variant="subtitle2"
              sx={{
                textTransform: 'uppercase',
                letterSpacing: 1.2,
                fontWeight: 600,
                fontSize: '0.75rem',
                opacity: gradient ? 0.9 : 0.7,
                color: gradient ? 'inherit' : 'text.secondary'
              }}
            >
              {title}
            </Typography>

            <Tooltip title={title} arrow>
              <Avatar
                sx={{
                  width: 48,
                  height: 48,
                  bgcolor: gradient
                    ? 'rgba(255, 255, 255, 0.2)'
                    : alpha(theme.palette[color].main, 0.1),
                  color: gradient ? 'white' : theme.palette[color].main,
                  backdropFilter: 'blur(10px)',
                  animation: animate ? `${pulse} 2s ease-in-out infinite` : 'none',
                  boxShadow: gradient ? '0 4px 20px 0 rgba(0,0,0,0.14)' : 'none'
                }}
              >
                {icon}
              </Avatar>
            </Tooltip>
          </Box>

          {/* Value */}
          <Box>
            {loading ? (
              <Skeleton variant="text" width="60%" height={48} sx={{ bgcolor: gradient ? 'rgba(255, 255, 255, 0.1)' : undefined }} />
            ) : (
              <Typography
                variant="h3"
                sx={{
                  fontWeight: 700,
                  fontSize: { xs: '1.75rem', sm: '2rem', md: '2.25rem' },
                  lineHeight: 1.2,
                  letterSpacing: '-0.02em',
                  color: 'inherit'
                }}
              >
                {value}
              </Typography>
            )}

            {subtitle && (
              <Typography
                variant="body2"
                sx={{
                  mt: 0.5,
                  opacity: gradient ? 0.85 : 0.7,
                  fontSize: '0.875rem',
                  color: 'inherit'
                }}
              >
                {subtitle}
              </Typography>
            )}
          </Box>

          {/* Footer */}
          {footer && (
            <Box
              sx={{
                pt: 2,
                borderTop: `1px solid ${gradient ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.08)'}`
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  display: 'block',
                  opacity: gradient ? 0.8 : 0.6,
                  fontSize: '0.75rem',
                  color: 'inherit'
                }}
              >
                {footer}
              </Typography>
            </Box>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
};
