/**
 * Global Error Handler
 * Catches unhandled errors and promise rejections
 */

interface ErrorLog {
  message: string;
  stack?: string;
  timestamp: string;
  type: 'error' | 'unhandledrejection' | 'react';
  url: string;
}

const MAX_ERROR_LOGS = 50;

/**
 * Store error in localStorage for debugging
 */
const logError = (errorData: ErrorLog): void => {
  try {
    const errors = JSON.parse(localStorage.getItem('optiflow_global_errors') || '[]');
    errors.push(errorData);

    // Keep only recent errors
    while (errors.length > MAX_ERROR_LOGS) {
      errors.shift();
    }

    localStorage.setItem('optiflow_global_errors', JSON.stringify(errors));
  } catch (e) {
    console.warn('Failed to log error to localStorage:', e);
  }
};

/**
 * Get all stored errors
 */
export const getStoredErrors = (): ErrorLog[] => {
  try {
    return JSON.parse(localStorage.getItem('optiflow_global_errors') || '[]');
  } catch {
    return [];
  }
};

/**
 * Clear all stored errors
 */
export const clearStoredErrors = (): void => {
  localStorage.removeItem('optiflow_global_errors');
  localStorage.removeItem('optiflow_errors');
};

/**
 * Initialize global error handlers
 */
export const initGlobalErrorHandlers = (): void => {
  // Handle uncaught errors
  window.onerror = (message, source, lineno, colno, error) => {
    console.error('Global error:', { message, source, lineno, colno, error });

    logError({
      message: typeof message === 'string' ? message : 'Unknown error',
      stack: error?.stack,
      timestamp: new Date().toISOString(),
      type: 'error',
      url: window.location.href,
    });

    // Don't suppress the error, let it bubble up
    return false;
  };

  // Handle unhandled promise rejections
  window.onunhandledrejection = (event) => {
    console.error('Unhandled promise rejection:', event.reason);

    const error = event.reason;
    logError({
      message: error?.message || String(error) || 'Unhandled promise rejection',
      stack: error?.stack,
      timestamp: new Date().toISOString(),
      type: 'unhandledrejection',
      url: window.location.href,
    });

    // Prevent the browser from logging to console (we already did)
    event.preventDefault();
  };

  // Monitor for memory issues
  if ('memory' in performance) {
    setInterval(() => {
      const memory = (performance as any).memory;
      const usedMB = Math.round(memory.usedJSHeapSize / 1024 / 1024);
      const limitMB = Math.round(memory.jsHeapSizeLimit / 1024 / 1024);
      const percentUsed = Math.round((memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100);

      if (percentUsed > 90) {
        console.warn(`High memory usage: ${usedMB}MB / ${limitMB}MB (${percentUsed}%)`);
      }
    }, 60000); // Check every minute
  }

  console.info('Global error handlers initialized');
};

/**
 * Safe wrapper for async functions
 * Catches errors and logs them
 */
export const safeAsync = <T>(
  fn: () => Promise<T>,
  fallback?: T,
  onError?: (error: Error) => void
): Promise<T | undefined> => {
  return fn().catch((error) => {
    console.error('safeAsync caught error:', error);

    logError({
      message: error?.message || 'Async error',
      stack: error?.stack,
      timestamp: new Date().toISOString(),
      type: 'error',
      url: window.location.href,
    });

    onError?.(error);
    return fallback;
  });
};

/**
 * Safe wrapper for functions that might throw
 */
export const safeCall = <T>(
  fn: () => T,
  fallback?: T,
  onError?: (error: Error) => void
): T | undefined => {
  try {
    return fn();
  } catch (error) {
    console.error('safeCall caught error:', error);

    if (error instanceof Error) {
      logError({
        message: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString(),
        type: 'error',
        url: window.location.href,
      });

      onError?.(error);
    }

    return fallback;
  }
};

export default initGlobalErrorHandlers;
