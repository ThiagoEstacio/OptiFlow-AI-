/**
 * Card component - SmartPort UI
 */
import { HTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/utils';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  noPadding?: boolean;
  hover?: boolean;
}

export function Card({
  className,
  title,
  subtitle,
  actions,
  noPadding = false,
  hover = false,
  children,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        'bg-dark-800 border border-dark-700 rounded-lg shadow-sm',
        hover && 'transition-all duration-200 hover:bg-dark-750 hover:border-dark-600 hover:shadow-md',
        !noPadding && 'p-6',
        className
      )}
      {...props}
    >
      {(title || subtitle || actions) && (
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            {title && (
              <h3 className="text-lg font-semibold text-white">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-sm text-dark-400 mt-1">
                {subtitle}
              </p>
            )}
          </div>
          {actions && (
            <div className="flex items-center gap-2 ml-4">
              {actions}
            </div>
          )}
        </div>
      )}
      {children}
    </div>
  );
}

export function CardHeader({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('px-6 py-4 border-b border-dark-700', className)} {...props}>
      {children}
    </div>
  );
}

export function CardBody({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('p-6', className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('px-6 py-4 border-t border-dark-700', className)} {...props}>
      {children}
    </div>
  );
}
