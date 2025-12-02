/**
 * 🏭 QualityIndicator - Industrial Data Quality Component
 * ========================================================
 *
 * Indicador visual de qualidade de dados industriais.
 * Inspirado em padrões PI Vision, Ignition e sistemas SCADA.
 *
 * Qualidades de dados:
 * - GOOD: Dados válidos e atualizados
 * - BAD: Falha de comunicação ou erro
 * - UNCERTAIN: Dados questionáveis
 * - STALE: Dados desatualizados (> threshold)
 * - NOT_CONNECTED: Dispositivo não conectado
 */

import React, { useMemo } from 'react';
import {
  Box,
  Tooltip,
  Typography,
  Stack,
  alpha,
  useTheme,
  keyframes,
} from '@mui/material';
import {
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  Schedule,
  LinkOff,
  HelpOutline,
  SignalWifiOff,
  Refresh,
} from '@mui/icons-material';

// ========================================
// Types
// ========================================

export type DataQuality = 'GOOD' | 'BAD' | 'UNCERTAIN' | 'STALE' | 'NOT_CONNECTED';

export interface QualityIndicatorProps {
  quality: DataQuality;
  timestamp?: Date | string;
  lastGoodTimestamp?: Date | string;
  lastGoodValue?: number | string;
  staleThreshold?: number; // seconds before data is considered stale
  showLabel?: boolean;
  showTimestamp?: boolean;
  size?: 'small' | 'medium' | 'large';
  variant?: 'icon' | 'badge' | 'border' | 'full';
  tooltipPlacement?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
}

export interface TagValueWithQualityProps {
  value: number | string;
  unit?: string;
  quality: DataQuality;
  timestamp?: Date | string;
  lastGoodTimestamp?: Date | string;
  lastGoodValue?: number | string;
  staleThreshold?: number;
  format?: 'number' | 'percent' | 'currency' | 'time' | 'auto';
  decimals?: number;
  showUnit?: boolean;
  showQuality?: boolean;
  size?: 'small' | 'medium' | 'large';
  className?: string;
}

// ========================================
// Constants
// ========================================

const QUALITY_CONFIG: Record<DataQuality, {
  color: string;
  icon: React.ReactElement;
  label: string;
  description: string;
}> = {
  GOOD: {
    color: '#4caf50',
    icon: <CheckCircle fontSize="inherit" />,
    label: 'Bom',
    description: 'Dados válidos e atualizados',
  },
  BAD: {
    color: '#f44336',
    icon: <ErrorIcon fontSize="inherit" />,
    label: 'Erro',
    description: 'Falha de comunicação ou erro no dispositivo',
  },
  UNCERTAIN: {
    color: '#ff9800',
    icon: <HelpOutline fontSize="inherit" />,
    label: 'Incerto',
    description: 'Dados questionáveis - verificar fonte',
  },
  STALE: {
    color: '#ffc107',
    icon: <Schedule fontSize="inherit" />,
    label: 'Desatualizado',
    description: 'Dados não atualizados dentro do limite',
  },
  NOT_CONNECTED: {
    color: '#9e9e9e',
    icon: <LinkOff fontSize="inherit" />,
    label: 'Desconectado',
    description: 'Dispositivo não conectado',
  },
};

const SIZE_CONFIG = {
  small: { iconSize: 14, fontSize: '0.75rem', padding: 0.5 },
  medium: { iconSize: 18, fontSize: '0.875rem', padding: 1 },
  large: { iconSize: 24, fontSize: '1rem', padding: 1.5 },
};

// Pulse animation for stale/bad data
const pulseAnimation = keyframes`
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
`;

// ========================================
// Helper Functions
// ========================================

const formatTimestamp = (timestamp?: Date | string): string => {
  if (!timestamp) return 'N/A';
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

const getTimeSince = (timestamp?: Date | string): string => {
  if (!timestamp) return 'N/A';
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (seconds < 60) return `${seconds}s atrás`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m atrás`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h atrás`;
  return `${Math.floor(seconds / 86400)}d atrás`;
};

const checkStale = (timestamp?: Date | string, threshold = 30): boolean => {
  if (!timestamp) return true;
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
  const secondsAgo = (Date.now() - date.getTime()) / 1000;
  return secondsAgo > threshold;
};

const formatValue = (
  value: number | string,
  format: string,
  decimals: number,
  unit?: string
): string => {
  if (typeof value === 'string') return value;

  let formatted: string;
  switch (format) {
    case 'percent':
      formatted = `${value.toFixed(decimals)}%`;
      break;
    case 'currency':
      formatted = new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
      }).format(value);
      break;
    case 'time':
      formatted = `${value.toFixed(decimals)}h`;
      break;
    default:
      formatted = value.toFixed(decimals);
  }

  return unit ? `${formatted} ${unit}` : formatted;
};

// ========================================
// QualityIndicator Component
// ========================================

export const QualityIndicator: React.FC<QualityIndicatorProps> = ({
  quality,
  timestamp,
  lastGoodTimestamp,
  lastGoodValue,
  staleThreshold = 30,
  showLabel = false,
  showTimestamp = false,
  size = 'medium',
  variant = 'icon',
  tooltipPlacement = 'top',
  className,
}) => {
  const theme = useTheme();
  const config = QUALITY_CONFIG[quality];
  const sizeConfig = SIZE_CONFIG[size];

  // Check if data is stale (override quality)
  const isStale = quality === 'GOOD' && checkStale(timestamp, staleThreshold);
  const effectiveQuality = isStale ? 'STALE' : quality;
  const effectiveConfig = QUALITY_CONFIG[effectiveQuality];

  // Determine if should animate
  const shouldPulse = effectiveQuality === 'BAD' || effectiveQuality === 'STALE';

  // Tooltip content
  const tooltipContent = (
    <Stack spacing={0.5}>
      <Typography variant="subtitle2">{effectiveConfig.label}</Typography>
      <Typography variant="caption" color="text.secondary">
        {effectiveConfig.description}
      </Typography>
      {timestamp && (
        <Typography variant="caption">
          Última atualização: {formatTimestamp(timestamp)}
        </Typography>
      )}
      {effectiveQuality !== 'GOOD' && lastGoodTimestamp && (
        <>
          <Typography variant="caption" color="text.secondary">
            Último valor válido: {lastGoodValue ?? 'N/A'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Em: {formatTimestamp(lastGoodTimestamp)}
          </Typography>
        </>
      )}
    </Stack>
  );

  // Render based on variant
  if (variant === 'icon') {
    return (
      <Tooltip title={tooltipContent} placement={tooltipPlacement} arrow>
        <Box
          className={className}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            color: effectiveConfig.color,
            fontSize: sizeConfig.iconSize,
            animation: shouldPulse ? `${pulseAnimation} 1.5s ease-in-out infinite` : undefined,
            cursor: 'help',
          }}
        >
          {effectiveConfig.icon}
          {showLabel && (
            <Typography
              variant="caption"
              sx={{ ml: 0.5, fontSize: sizeConfig.fontSize }}
            >
              {effectiveConfig.label}
            </Typography>
          )}
        </Box>
      </Tooltip>
    );
  }

  if (variant === 'badge') {
    return (
      <Tooltip title={tooltipContent} placement={tooltipPlacement} arrow>
        <Box
          className={className}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            bgcolor: alpha(effectiveConfig.color, 0.1),
            color: effectiveConfig.color,
            borderRadius: 1,
            px: sizeConfig.padding,
            py: 0.25,
            animation: shouldPulse ? `${pulseAnimation} 1.5s ease-in-out infinite` : undefined,
            cursor: 'help',
          }}
        >
          <Box sx={{ fontSize: sizeConfig.iconSize, display: 'flex', mr: 0.5 }}>
            {effectiveConfig.icon}
          </Box>
          <Typography variant="caption" sx={{ fontSize: sizeConfig.fontSize }}>
            {effectiveConfig.label}
          </Typography>
        </Box>
      </Tooltip>
    );
  }

  if (variant === 'full') {
    return (
      <Tooltip title={tooltipContent} placement={tooltipPlacement} arrow>
        <Box
          className={className}
          sx={{
            display: 'inline-flex',
            flexDirection: 'column',
            alignItems: 'flex-start',
            bgcolor: alpha(effectiveConfig.color, 0.05),
            border: `1px solid ${alpha(effectiveConfig.color, 0.3)}`,
            borderRadius: 1,
            p: 1,
            animation: shouldPulse ? `${pulseAnimation} 1.5s ease-in-out infinite` : undefined,
            cursor: 'help',
          }}
        >
          <Stack direction="row" alignItems="center" spacing={0.5}>
            <Box sx={{ fontSize: sizeConfig.iconSize, color: effectiveConfig.color, display: 'flex' }}>
              {effectiveConfig.icon}
            </Box>
            <Typography variant="caption" fontWeight={600} color={effectiveConfig.color}>
              {effectiveConfig.label}
            </Typography>
          </Stack>
          {showTimestamp && timestamp && (
            <Typography variant="caption" color="text.secondary">
              {getTimeSince(timestamp)}
            </Typography>
          )}
        </Box>
      </Tooltip>
    );
  }

  // Default: border variant (for wrapping content)
  return (
    <Box
      className={className}
      sx={{
        position: 'relative',
        borderLeft: `3px solid ${effectiveConfig.color}`,
        pl: 1,
        animation: shouldPulse ? `${pulseAnimation} 1.5s ease-in-out infinite` : undefined,
      }}
    />
  );
};

// ========================================
// TagValueWithQuality Component
// ========================================

export const TagValueWithQuality: React.FC<TagValueWithQualityProps> = ({
  value,
  unit,
  quality,
  timestamp,
  lastGoodTimestamp,
  lastGoodValue,
  staleThreshold = 30,
  format = 'auto',
  decimals = 2,
  showUnit = true,
  showQuality = true,
  size = 'medium',
  className,
}) => {
  const theme = useTheme();
  const sizeConfig = SIZE_CONFIG[size];

  // Check for stale data
  const isStale = quality === 'GOOD' && checkStale(timestamp, staleThreshold);
  const effectiveQuality = isStale ? 'STALE' : quality;
  const config = QUALITY_CONFIG[effectiveQuality];

  // Determine display value
  const displayValue = useMemo(() => {
    if (effectiveQuality === 'BAD' || effectiveQuality === 'NOT_CONNECTED') {
      return '---';
    }
    if (effectiveQuality === 'STALE' && lastGoodValue !== undefined) {
      return formatValue(lastGoodValue as number, format, decimals, showUnit ? unit : undefined);
    }
    return formatValue(value as number, format, decimals, showUnit ? unit : undefined);
  }, [effectiveQuality, value, lastGoodValue, format, decimals, unit, showUnit]);

  // Font size based on size prop
  const fontSizeMap = {
    small: 'body2',
    medium: 'h6',
    large: 'h4',
  };

  return (
    <Stack
      direction="row"
      alignItems="center"
      spacing={1}
      className={className}
      sx={{
        opacity: effectiveQuality !== 'GOOD' ? 0.8 : 1,
      }}
    >
      <Typography
        variant={fontSizeMap[size] as any}
        fontWeight={600}
        sx={{
          color: effectiveQuality === 'GOOD'
            ? theme.palette.text.primary
            : effectiveQuality === 'BAD' || effectiveQuality === 'NOT_CONNECTED'
            ? theme.palette.error.main
            : theme.palette.warning.main,
          fontFamily: 'monospace',
          textDecoration: effectiveQuality === 'STALE' ? 'line-through' : undefined,
        }}
      >
        {displayValue}
      </Typography>

      {showQuality && effectiveQuality !== 'GOOD' && (
        <QualityIndicator
          quality={effectiveQuality}
          timestamp={timestamp}
          lastGoodTimestamp={lastGoodTimestamp}
          lastGoodValue={lastGoodValue}
          staleThreshold={staleThreshold}
          size={size}
          variant="icon"
        />
      )}
    </Stack>
  );
};

// ========================================
// CommFailIndicator - Special component for communication failures
// ========================================

export const CommFailIndicator: React.FC<{
  isCommFail: boolean;
  deviceName?: string;
  lastSuccess?: Date | string;
  size?: 'small' | 'medium' | 'large';
}> = ({ isCommFail, deviceName, lastSuccess, size = 'medium' }) => {
  const theme = useTheme();

  if (!isCommFail) return null;

  return (
    <Tooltip
      title={
        <Stack spacing={0.5}>
          <Typography variant="subtitle2" color="error">
            Falha de Comunicação
          </Typography>
          {deviceName && (
            <Typography variant="caption">Dispositivo: {deviceName}</Typography>
          )}
          {lastSuccess && (
            <Typography variant="caption">
              Última comunicação: {formatTimestamp(lastSuccess)}
            </Typography>
          )}
          <Typography variant="caption" color="text.secondary">
            Verifique a conexão de rede e o status do dispositivo.
          </Typography>
        </Stack>
      }
      arrow
    >
      <Box
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          bgcolor: alpha(theme.palette.error.main, 0.1),
          color: theme.palette.error.main,
          borderRadius: 1,
          px: 1,
          py: 0.5,
          animation: `${pulseAnimation} 1s ease-in-out infinite`,
          cursor: 'help',
        }}
      >
        <SignalWifiOff fontSize={size} sx={{ mr: 0.5 }} />
        <Typography variant="caption" fontWeight={600}>
          COMM FAIL
        </Typography>
      </Box>
    </Tooltip>
  );
};

// ========================================
// StaleDataBanner - Banner for page-wide stale data warning
// ========================================

export const StaleDataBanner: React.FC<{
  staleCount: number;
  totalTags: number;
  onRefresh?: () => void;
}> = ({ staleCount, totalTags, onRefresh }) => {
  const theme = useTheme();

  if (staleCount === 0) return null;

  const percentage = ((staleCount / totalTags) * 100).toFixed(0);

  return (
    <Box
      sx={{
        bgcolor: alpha(theme.palette.warning.main, 0.1),
        border: `1px solid ${alpha(theme.palette.warning.main, 0.3)}`,
        borderRadius: 1,
        px: 2,
        py: 1,
        mb: 2,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      <Stack direction="row" alignItems="center" spacing={1}>
        <Warning color="warning" />
        <Typography variant="body2">
          <strong>{staleCount}</strong> de {totalTags} tags ({percentage}%) com dados
          desatualizados
        </Typography>
      </Stack>

      {onRefresh && (
        <Tooltip title="Forçar atualização">
          <Box
            component="button"
            onClick={onRefresh}
            sx={{
              display: 'flex',
              alignItems: 'center',
              bgcolor: 'transparent',
              border: 'none',
              color: theme.palette.warning.main,
              cursor: 'pointer',
              '&:hover': {
                color: theme.palette.warning.dark,
              },
            }}
          >
            <Refresh sx={{ mr: 0.5 }} />
            <Typography variant="caption">Atualizar</Typography>
          </Box>
        </Tooltip>
      )}
    </Box>
  );
};

export default QualityIndicator;
