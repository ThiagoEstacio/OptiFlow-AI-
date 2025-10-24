/**
 * Input component - SmartPort UI
 */
import { InputHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      fullWidth = false,
      disabled,
      type = 'text',
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'w-full rounded-lg border bg-dark-800 px-4 py-2.5 text-sm text-dark-100 placeholder:text-dark-500 transition-colors';

    const stateStyles = error
      ? 'border-danger-500 focus:border-danger-500 focus:ring-2 focus:ring-danger-500/20'
      : 'border-dark-600 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 hover:border-dark-500';

    const disabledStyles = disabled
      ? 'opacity-50 cursor-not-allowed'
      : '';

    const paddingStyles = leftIcon && rightIcon
      ? 'pl-11 pr-11'
      : leftIcon
      ? 'pl-11'
      : rightIcon
      ? 'pr-11'
      : '';

    return (
      <div className={cn('flex flex-col gap-1.5', fullWidth ? 'w-full' : '')}>
        {label && (
          <label className="text-sm font-medium text-dark-300">
            {label}
          </label>
        )}

        <div className="relative">
          {leftIcon && (
            <div className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-dark-400">
              {leftIcon}
            </div>
          )}

          <input
            ref={ref}
            type={type}
            disabled={disabled}
            className={cn(
              baseStyles,
              stateStyles,
              disabledStyles,
              paddingStyles,
              className
            )}
            {...props}
          />

          {rightIcon && (
            <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-dark-400">
              {rightIcon}
            </div>
          )}
        </div>

        {(error || helperText) && (
          <p
            className={cn(
              'text-xs',
              error ? 'text-danger-500' : 'text-dark-400'
            )}
          >
            {error || helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
