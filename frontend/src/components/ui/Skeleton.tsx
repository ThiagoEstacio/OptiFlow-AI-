/**
 * Skeleton component - SmartPort UI
 * Loading placeholder with pulse animation
 */
import { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  count?: number;
}

export function Skeleton({
  className,
  variant = 'rectangular',
  width,
  height,
  count = 1,
  ...props
}: SkeletonProps) {
  const baseStyles = 'animate-pulse bg-dark-700';

  const variantStyles = {
    text: 'rounded h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  const style = {
    width: width || (variant === 'text' ? '100%' : undefined),
    height: height || (variant === 'text' ? '1rem' : undefined),
  };

  if (count > 1) {
    return (
      <div className="flex flex-col gap-2">
        {Array.from({ length: count }).map((_, index) => (
          <div
            key={index}
            className={cn(baseStyles, variantStyles[variant], className)}
            style={style}
            {...props}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={cn(baseStyles, variantStyles[variant], className)}
      style={style}
      {...props}
    />
  );
}

/**
 * Pre-built skeleton layouts for common use cases
 */
export function SkeletonCard() {
  return (
    <div className="rounded-lg border border-dark-700 bg-dark-800 p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <Skeleton variant="text" width="60%" className="mb-2" />
          <Skeleton variant="text" width="40%" height="0.875rem" />
        </div>
        <Skeleton variant="circular" width={40} height={40} />
      </div>
      <div className="mt-6">
        <Skeleton variant="rectangular" height={120} />
      </div>
    </div>
  );
}

export function SkeletonTable({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      <Skeleton variant="rectangular" height={40} />
      {Array.from({ length: rows }).map((_, index) => (
        <Skeleton key={index} variant="rectangular" height={60} />
      ))}
    </div>
  );
}

export function SkeletonKPICard() {
  return (
    <div className="rounded-lg border border-dark-700 bg-dark-800 p-6">
      <div className="flex items-center justify-between">
        <Skeleton variant="text" width="50%" className="mb-2" />
        <Skeleton variant="circular" width={36} height={36} />
      </div>
      <Skeleton variant="text" width="40%" height="2rem" className="mt-2" />
      <div className="mt-4 flex items-center gap-2">
        <Skeleton variant="text" width="30%" height="0.875rem" />
        <Skeleton variant="text" width="20%" height="0.875rem" />
      </div>
    </div>
  );
}
