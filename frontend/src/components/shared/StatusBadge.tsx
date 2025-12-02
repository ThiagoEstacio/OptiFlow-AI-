/**
 * StatusBadge Component
 * =====================
 * Reusable badge component for displaying status/severity information.
 * Consolidates 5+ duplicate implementations across the codebase.
 */

import React from 'react';
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  AlertCircle,
  HelpCircle,
  TrendingUp,
  TrendingDown,
  Minus,
  LucideIcon,
} from 'lucide-react';
import { getSeverityColor, getHealthColor, getTrendColor } from '../../utils/colors';
import { SeverityLevel, HealthStatus, TrendDirection } from '../../utils/constants';

// Icon mappings
const HEALTH_ICONS: Record<HealthStatus, LucideIcon> = {
  healthy: CheckCircle,
  warning: AlertTriangle,
  critical: XCircle,
  unknown: HelpCircle,
  degraded: AlertCircle,
};

const SEVERITY_ICONS: Record<SeverityLevel, LucideIcon> = {
  critical: XCircle,
  high: AlertCircle,
  medium: AlertTriangle,
  low: CheckCircle,
  info: HelpCircle,
};

const TREND_ICONS: Record<TrendDirection, LucideIcon> = {
  up: TrendingUp,
  down: TrendingDown,
  stable: Minus,
};

// Size variants
const SIZE_CLASSES = {
  xs: {
    badge: 'px-1.5 py-0.5 text-xs',
    icon: 'w-3 h-3',
    dot: 'w-1.5 h-1.5',
  },
  sm: {
    badge: 'px-2 py-0.5 text-xs',
    icon: 'w-3.5 h-3.5',
    dot: 'w-2 h-2',
  },
  md: {
    badge: 'px-2.5 py-1 text-sm',
    icon: 'w-4 h-4',
    dot: 'w-2.5 h-2.5',
  },
  lg: {
    badge: 'px-3 py-1.5 text-base',
    icon: 'w-5 h-5',
    dot: 'w-3 h-3',
  },
} as const;

type BadgeSize = keyof typeof SIZE_CLASSES;
type BadgeVariant = 'solid' | 'soft' | 'outline' | 'dot';
type BadgeType = 'severity' | 'health' | 'trend';

interface StatusBadgeProps {
  /** The status value (depends on type) */
  status: SeverityLevel | HealthStatus | TrendDirection | string;
  /** Type of status badge */
  type?: BadgeType;
  /** Size variant */
  size?: BadgeSize;
  /** Visual variant */
  variant?: BadgeVariant;
  /** Custom label (overrides default) */
  label?: string;
  /** Whether to show icon */
  showIcon?: boolean;
  /** Whether to show label */
  showLabel?: boolean;
  /** Whether to animate (pulse for critical) */
  animate?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Custom icon component */
  icon?: LucideIcon;
}

// Default labels
const HEALTH_LABELS: Record<HealthStatus, string> = {
  healthy: 'Saudável',
  warning: 'Atenção',
  critical: 'Crítico',
  unknown: 'Desconhecido',
  degraded: 'Degradado',
};

const SEVERITY_LABELS: Record<SeverityLevel, string> = {
  critical: 'Crítico',
  high: 'Alto',
  medium: 'Médio',
  low: 'Baixo',
  info: 'Info',
};

const TREND_LABELS: Record<TrendDirection, string> = {
  up: 'Subindo',
  down: 'Descendo',
  stable: 'Estável',
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  type = 'health',
  size = 'md',
  variant = 'soft',
  label,
  showIcon = true,
  showLabel = true,
  animate = false,
  className = '',
  icon: CustomIcon,
}) => {
  // Get colors based on type
  const getColors = () => {
    switch (type) {
      case 'severity':
        return getSeverityColor(status as SeverityLevel);
      case 'trend':
        return getTrendColor(status as TrendDirection);
      case 'health':
      default:
        return getHealthColor(status as HealthStatus);
    }
  };

  // Get icon based on type
  const getIcon = (): LucideIcon => {
    if (CustomIcon) return CustomIcon;
    switch (type) {
      case 'severity':
        return SEVERITY_ICONS[status as SeverityLevel] || HelpCircle;
      case 'trend':
        return TREND_ICONS[status as TrendDirection] || Minus;
      case 'health':
      default:
        return HEALTH_ICONS[status as HealthStatus] || HelpCircle;
    }
  };

  // Get default label based on type
  const getDefaultLabel = (): string => {
    switch (type) {
      case 'severity':
        return SEVERITY_LABELS[status as SeverityLevel] || status;
      case 'trend':
        return TREND_LABELS[status as TrendDirection] || status;
      case 'health':
      default:
        return HEALTH_LABELS[status as HealthStatus] || status;
    }
  };

  const colors = getColors();
  const Icon = getIcon();
  const sizeClasses = SIZE_CLASSES[size];
  const displayLabel = label || getDefaultLabel();

  // Safely access color properties with fallbacks
  const bgDark = 'bgDark' in colors ? colors.bgDark : colors.bg;
  const textLight = 'textLight' in colors ? colors.textLight : 'text-white';
  const border = 'border' in colors ? colors.border : 'border-gray-300';

  // Build variant classes
  const getVariantClasses = () => {
    switch (variant) {
      case 'solid':
        return `${bgDark} ${textLight}`;
      case 'outline':
        return `bg-transparent ${colors.text} border ${border}`;
      case 'dot':
        return `bg-transparent ${colors.text}`;
      case 'soft':
      default:
        return `${colors.bg} ${colors.text}`;
    }
  };

  const variantClasses = getVariantClasses();
  const animationClass = animate && (status === 'critical' || status === 'high')
    ? 'animate-pulse'
    : '';

  if (variant === 'dot') {
    return (
      <span
        className={`inline-flex items-center gap-1.5 ${sizeClasses.badge} ${className}`}
      >
        <span
          className={`${sizeClasses.dot} rounded-full ${bgDark} ${animationClass}`}
        />
        {showLabel && <span className={colors.text}>{displayLabel}</span>}
      </span>
    );
  }

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 rounded-full font-medium
        ${sizeClasses.badge}
        ${variantClasses}
        ${animationClass}
        ${className}
      `.trim()}
    >
      {showIcon && <Icon className={sizeClasses.icon} />}
      {showLabel && <span>{displayLabel}</span>}
    </span>
  );
};

// Convenience components for common use cases
export const SeverityBadge: React.FC<Omit<StatusBadgeProps, 'type'> & { severity: SeverityLevel | string }> = ({
  severity,
  ...props
}) => <StatusBadge status={severity} type="severity" {...props} />;

export const HealthBadge: React.FC<Omit<StatusBadgeProps, 'type'> & { health: HealthStatus | string }> = ({
  health,
  ...props
}) => <StatusBadge status={health} type="health" {...props} />;

export const TrendBadge: React.FC<Omit<StatusBadgeProps, 'type'> & { trend: TrendDirection | string }> = ({
  trend,
  ...props
}) => <StatusBadge status={trend} type="trend" {...props} />;

export default StatusBadge;
