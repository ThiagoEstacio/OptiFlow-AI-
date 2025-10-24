/**
 * ProgressBar component - SmartPort UI
 */
import { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface ProgressBarProps extends HTMLAttributes<HTMLDivElement> {
  value: number; // 0-100
  max?: number;
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  label?: string;
  animated?: boolean;
}

export function ProgressBar({
  className,
  value,
  max = 100,
  variant = 'primary',
  size = 'md',
  showLabel = false,
  label,
  animated = false,
  ...props
}: ProgressBarProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  const containerStyles = 'w-full overflow-hidden rounded-full bg-dark-700';

  const sizes = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  const variants = {
    primary: 'bg-primary-500',
    success: 'bg-success-500',
    warning: 'bg-warning-500',
    danger: 'bg-danger-500',
    info: 'bg-info-500',
  };

  const barStyles = cn(
    'h-full rounded-full transition-all duration-300',
    variants[variant],
    animated && 'animate-pulse-slow'
  );

  return (
    <div className={cn('w-full', className)} {...props}>
      {(showLabel || label) && (
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="font-medium text-dark-300">
            {label || 'Progress'}
          </span>
          <span className="text-dark-400">{percentage.toFixed(0)}%</span>
        </div>
      )}

      <div className={cn(containerStyles, sizes[size])}>
        <div
          className={barStyles}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
    </div>
  );
}

/**
 * Multi-segment progress bar for complex operations
 */
export interface ProgressSegment {
  value: number;
  variant: ProgressBarProps['variant'];
  label?: string;
}

export interface MultiProgressBarProps extends HTMLAttributes<HTMLDivElement> {
  segments: ProgressSegment[];
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  showLabels?: boolean;
}

export function MultiProgressBar({
  className,
  segments,
  max = 100,
  size = 'md',
  showLabels = false,
  ...props
}: MultiProgressBarProps) {
  const containerStyles = 'w-full overflow-hidden rounded-full bg-dark-700';

  const sizes = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  const variants = {
    primary: 'bg-primary-500',
    success: 'bg-success-500',
    warning: 'bg-warning-500',
    danger: 'bg-danger-500',
    info: 'bg-info-500',
  };

  const total = segments.reduce((sum, seg) => sum + seg.value, 0);
  const percentages = segments.map((seg) => (seg.value / max) * 100);

  return (
    <div className={cn('w-full', className)} {...props}>
      {showLabels && (
        <div className="mb-2 flex items-center gap-4 text-xs">
          {segments.map((segment, index) => (
            <div key={index} className="flex items-center gap-2">
              <div
                className={cn('h-2 w-2 rounded-full', variants[segment.variant!])}
              />
              <span className="text-dark-400">
                {segment.label}: {percentages[index].toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      )}

      <div className={cn(containerStyles, sizes[size])}>
        <div className="flex h-full">
          {segments.map((segment, index) => (
            <div
              key={index}
              className={cn(
                'h-full transition-all duration-300',
                variants[segment.variant!]
              )}
              style={{ width: `${percentages[index]}%` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
