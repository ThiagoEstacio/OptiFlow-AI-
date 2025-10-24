/**
 * Badge component - SmartPort UI
 */
import { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'default' | 'purple';
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
}

export function Badge({
  className,
  variant = 'default',
  size = 'md',
  dot = false,
  children,
  ...props
}: BadgeProps) {
  const baseStyles = 'inline-flex items-center font-medium rounded-full';

  const variants = {
    success: 'bg-success-500/10 text-success-500 border border-success-500/20',
    warning: 'bg-warning-500/10 text-warning-500 border border-warning-500/20',
    danger: 'bg-danger-500/10 text-danger-500 border border-danger-500/20',
    info: 'bg-info-500/10 text-info-500 border border-info-500/20',
    purple: 'bg-purple-500/10 text-purple-500 border border-purple-500/20',
    default: 'bg-dark-700 text-dark-300 border border-dark-600',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs gap-1',
    md: 'px-2.5 py-1 text-sm gap-1.5',
    lg: 'px-3 py-1.5 text-base gap-2',
  };

  const dotColors = {
    success: 'bg-success-500',
    warning: 'bg-warning-500',
    danger: 'bg-danger-500',
    info: 'bg-info-500',
    purple: 'bg-purple-500',
    default: 'bg-dark-400',
  };

  const dotSizes = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-2.5 h-2.5',
  };

  return (
    <span
      className={cn(baseStyles, variants[variant], sizes[size], className)}
      {...props}
    >
      {dot && (
        <span
          className={cn(
            'rounded-full animate-pulse-slow',
            dotColors[variant],
            dotSizes[size]
          )}
        />
      )}
      {children}
    </span>
  );
}
