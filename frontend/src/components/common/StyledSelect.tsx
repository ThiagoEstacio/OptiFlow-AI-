/**
 * StyledSelect - Custom styled select component
 *
 * Provides consistent select styling across the application with:
 * - Larger, more visible dropdown arrow
 * - Better padding and spacing
 * - Clean, professional look
 */
import React from 'react';

// Base styles for select inputs
export const selectStyles = {
  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236b7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
  backgroundRepeat: 'no-repeat',
  backgroundPosition: 'right 12px center',
  backgroundSize: '20px',
  paddingRight: '44px'
} as const;

// Smaller variant for headers
export const selectStylesSmall = {
  ...selectStyles,
  backgroundPosition: 'right 10px center',
  backgroundSize: '18px',
  paddingRight: '40px'
} as const;

interface StyledSelectProps {
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  placeholder?: string;
  label?: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  minWidth?: string;
}

export function StyledSelect({
  value,
  onChange,
  options,
  placeholder,
  label,
  className = '',
  size = 'md',
  minWidth = '180px'
}: StyledSelectProps) {
  const sizeClasses = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-2.5 text-base',
    lg: 'px-4 py-3 text-base'
  };

  const baseClasses = `w-full ${sizeClasses[size]} font-medium border border-gray-300 rounded-lg bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 cursor-pointer appearance-none`;

  return (
    <div style={{ minWidth }}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
        </label>
      )}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`${baseClasses} ${className}`}
        style={size === 'sm' ? selectStylesSmall : selectStyles}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

// Quick helper component for time range selects
interface TimeRangeSelectProps {
  value: string;
  onChange: (value: string) => void;
  options?: { value: string; label: string }[];
  size?: 'sm' | 'md' | 'lg';
}

export function TimeRangeSelect({
  value,
  onChange,
  options,
  size = 'sm'
}: TimeRangeSelectProps) {
  const defaultOptions = [
    { value: '1h', label: '1 hora' },
    { value: '6h', label: '6 horas' },
    { value: '24h', label: '24 horas' },
    { value: '7d', label: '7 dias' },
    { value: '30d', label: '30 dias' },
  ];

  return (
    <StyledSelect
      value={value}
      onChange={onChange}
      options={options || defaultOptions}
      size={size}
      minWidth="160px"
    />
  );
}

export default StyledSelect;
