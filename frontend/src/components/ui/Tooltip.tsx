/**
 * Tooltip component - SmartPort UI
 * Built on Radix UI Tooltip primitive
 */
import * as TooltipPrimitive from '@radix-ui/react-tooltip';
import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

export interface TooltipProps {
  children: ReactNode;
  content: ReactNode;
  side?: 'top' | 'right' | 'bottom' | 'left';
  align?: 'start' | 'center' | 'end';
  delayDuration?: number;
  className?: string;
}

export function Tooltip({
  children,
  content,
  side = 'top',
  align = 'center',
  delayDuration = 200,
  className,
}: TooltipProps) {
  return (
    <TooltipPrimitive.Provider delayDuration={delayDuration}>
      <TooltipPrimitive.Root>
        <TooltipPrimitive.Trigger asChild>
          {children}
        </TooltipPrimitive.Trigger>

        <TooltipPrimitive.Portal>
          <TooltipPrimitive.Content
            side={side}
            align={align}
            className={cn(
              'z-50 overflow-hidden rounded-lg border border-dark-600 bg-dark-800 px-3 py-2 text-sm text-dark-100 shadow-lg',
              'animate-fade-in',
              className
            )}
            sideOffset={5}
          >
            {content}
            <TooltipPrimitive.Arrow className="fill-dark-800" />
          </TooltipPrimitive.Content>
        </TooltipPrimitive.Portal>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  );
}

/**
 * Simple tooltip wrapper for common use case
 */
export function SimpleTooltip({
  children,
  text,
  ...props
}: Omit<TooltipProps, 'content'> & { text: string }) {
  return (
    <Tooltip content={<span>{text}</span>} {...props}>
      {children}
    </Tooltip>
  );
}
