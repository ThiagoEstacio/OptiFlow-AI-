/**
 * Theme Toggle Component
 * Button to switch between light/dark/auto themes
 */

import React from 'react';
import { Sun, Moon, Monitor } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

interface ThemeToggleProps {
  variant?: 'icon' | 'full';
  size?: 'sm' | 'md' | 'lg';
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({
  variant = 'icon',
  size = 'md',
}) => {
  const { theme, effectiveTheme, setTheme } = useTheme();

  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12',
  };

  const iconSizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  if (variant === 'icon') {
    const handleClick = () => {
      if (theme === 'light') setTheme('dark');
      else if (theme === 'dark') setTheme('auto');
      else setTheme('light');
    };

    return (
      <button
        onClick={handleClick}
        className={`
          ${sizeClasses[size]}
          flex items-center justify-center
          rounded-lg
          bg-gray-200 dark:bg-gray-700
          hover:bg-gray-300 dark:hover:bg-gray-600
          text-gray-700 dark:text-gray-200
          transition-colors
        `}
        title={`Theme: ${theme} (${effectiveTheme})`}
      >
        {theme === 'light' && <Sun className={iconSizeClasses[size]} />}
        {theme === 'dark' && <Moon className={iconSizeClasses[size]} />}
        {theme === 'auto' && <Monitor className={iconSizeClasses[size]} />}
      </button>
    );
  }

  // Full variant with all options
  return (
    <div className="flex items-center space-x-1 bg-gray-200 dark:bg-gray-700 rounded-lg p-1">
      <button
        onClick={() => setTheme('light')}
        className={`
          ${sizeClasses[size]}
          flex items-center justify-center rounded-md transition-colors
          ${
            theme === 'light'
              ? 'bg-white dark:bg-gray-800 text-yellow-500 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
          }
        `}
        title="Light mode"
      >
        <Sun className={iconSizeClasses[size]} />
      </button>

      <button
        onClick={() => setTheme('dark')}
        className={`
          ${sizeClasses[size]}
          flex items-center justify-center rounded-md transition-colors
          ${
            theme === 'dark'
              ? 'bg-white dark:bg-gray-800 text-blue-500 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
          }
        `}
        title="Dark mode"
      >
        <Moon className={iconSizeClasses[size]} />
      </button>

      <button
        onClick={() => setTheme('auto')}
        className={`
          ${sizeClasses[size]}
          flex items-center justify-center rounded-md transition-colors
          ${
            theme === 'auto'
              ? 'bg-white dark:bg-gray-800 text-purple-500 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
          }
        `}
        title="Auto (system)"
      >
        <Monitor className={iconSizeClasses[size]} />
      </button>
    </div>
  );
};
