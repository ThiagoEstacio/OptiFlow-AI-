/**
 * KPICard - Key Performance Indicator display card
 * Used in dashboards to show important metrics
 */
import { ReactNode } from 'react';
import { Card } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { cn } from '@/lib/utils';
import { formatNumber, formatPercent } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface KPICardProps {
  title: string;
  value: number | string;
  unit?: string;
  icon?: ReactNode;
  trend?: {
    value: number; // Percentage change
    period?: string; // e.g., "vs last week"
  };
  format?: 'number' | 'percent' | 'currency' | 'custom';
  decimals?: number;
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger';
  loading?: boolean;
  className?: string;
}

export function KPICard({
  title,
  value,
  unit,
  icon,
  trend,
  format = 'number',
  decimals = 0,
  variant = 'default',
  loading = false,
  className,
}: KPICardProps) {
  // Format the value based on format type
  const formattedValue = (() => {
    if (typeof value === 'string') return value;

    switch (format) {
      case 'number':
        return formatNumber(value, decimals);
      case 'percent':
        return formatPercent(value, decimals);
      case 'currency':
        return `R$ ${formatNumber(value, decimals)}`;
      default:
        return value;
    }
  })();

  // Determine trend direction
  const trendDirection = trend
    ? trend.value > 0
      ? 'up'
      : trend.value < 0
      ? 'down'
      : 'neutral'
    : null;

  // Icon colors based on variant
  const iconColors = {
    default: 'text-dark-400',
    primary: 'text-primary-500',
    success: 'text-success-500',
    warning: 'text-warning-500',
    danger: 'text-danger-500',
  };

  // Trend colors (up is good for most metrics)
  const trendColors = {
    up: 'text-success-500',
    down: 'text-danger-500',
    neutral: 'text-dark-400',
  };

  if (loading) {
    return (
      <Card className={className} noPadding>
        <div className="p-6">
          <div className="flex items-center justify-between">
            <Skeleton variant="text" width="50%" className="mb-2" />
            <Skeleton variant="circular" width={36} height={36} />
          </div>
          <Skeleton variant="text" width="40%" height="2rem" className="mt-2" />
          <div className="mt-4 flex items-center gap-2">
            <Skeleton variant="text" width="30%" height="0.875rem" />
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className={className} noPadding hover>
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-dark-400">{title}</p>
            <div className="mt-2 flex items-baseline gap-2">
              <p className="text-3xl font-bold text-dark-100">{formattedValue}</p>
              {unit && <span className="text-sm text-dark-400">{unit}</span>}
            </div>
          </div>

          {icon && (
            <div
              className={cn(
                'flex h-12 w-12 items-center justify-center rounded-lg bg-dark-700',
                iconColors[variant]
              )}
            >
              {icon}
            </div>
          )}
        </div>

        {trend && trendDirection && (
          <div className="mt-4 flex items-center gap-1.5">
            {trendDirection === 'up' && (
              <TrendingUp className="h-4 w-4 text-success-500" />
            )}
            {trendDirection === 'down' && (
              <TrendingDown className="h-4 w-4 text-danger-500" />
            )}
            {trendDirection === 'neutral' && (
              <Minus className="h-4 w-4 text-dark-400" />
            )}

            <span
              className={cn('text-sm font-medium', trendColors[trendDirection])}
            >
              {Math.abs(trend.value)}%
            </span>

            {trend.period && (
              <span className="text-sm text-dark-400">{trend.period}</span>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}

/**
 * Compact KPI card for dense layouts
 */
export function KPICardCompact({
  title,
  value,
  unit,
  icon,
  variant = 'default',
  loading = false,
  className,
}: Pick<
  KPICardProps,
  'title' | 'value' | 'unit' | 'icon' | 'variant' | 'loading' | 'className'
>) {
  const iconColors = {
    default: 'text-dark-400',
    primary: 'text-primary-500',
    success: 'text-success-500',
    warning: 'text-warning-500',
    danger: 'text-danger-500',
  };

  if (loading) {
    return (
      <div className={cn('flex items-center gap-3', className)}>
        <Skeleton variant="circular" width={40} height={40} />
        <div className="flex-1">
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="text" width="40%" className="mt-1" />
        </div>
      </div>
    );
  }

  return (
    <div className={cn('flex items-center gap-3', className)}>
      {icon && (
        <div
          className={cn(
            'flex h-10 w-10 items-center justify-center rounded-lg bg-dark-700',
            iconColors[variant]
          )}
        >
          {icon}
        </div>
      )}
      <div className="flex-1">
        <p className="text-xs text-dark-400">{title}</p>
        <div className="flex items-baseline gap-1">
          <p className="text-lg font-bold text-dark-100">{value}</p>
          {unit && <span className="text-xs text-dark-400">{unit}</span>}
        </div>
      </div>
    </div>
  );
}
