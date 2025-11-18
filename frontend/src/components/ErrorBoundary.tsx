/**
 * ErrorBoundary Component
 * Catches React errors and displays user-friendly error messages with recovery options
 */
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console (in production, send to monitoring service)
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    this.setState(prev => ({
      error,
      errorInfo,
      errorCount: prev.errorCount + 1,
    }));

    // Store error for debugging
    this.logErrorToStorage(error, errorInfo);
  }

  private logErrorToStorage(error: Error, errorInfo: ErrorInfo) {
    try {
      const errorData = {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        url: window.location.href,
      };

      const errors = JSON.parse(localStorage.getItem('optiflow_errors') || '[]');
      errors.push(errorData);
      // Keep only last 20 errors
      while (errors.length > 20) errors.shift();
      localStorage.setItem('optiflow_errors', JSON.stringify(errors));
    } catch (e) {
      console.warn('Failed to log error to storage:', e);
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
          <div className="max-w-2xl w-full bg-white rounded-lg shadow-xl p-8">
            <div className="flex items-center mb-6">
              <div className="flex-shrink-0">
                <svg
                  className="h-12 w-12 text-red-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
              <div className="ml-4">
                <h1 className="text-2xl font-bold text-gray-900">
                  Something went wrong
                </h1>
                <p className="text-gray-600 mt-1">
                  We encountered an unexpected error. Please try one of the options below.
                </p>
              </div>
            </div>

            {/* Error details (only show in development) */}
            {import.meta.env.DEV && this.state.error && (
              <div className="mb-6 bg-gray-100 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                  Error Details (Development Only):
                </h3>
                <pre className="text-xs text-gray-600 overflow-auto max-h-40">
                  {this.state.error.toString()}
                  {this.state.errorInfo && this.state.errorInfo.componentStack}
                </pre>
              </div>
            )}

            {/* Action buttons */}
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={this.handleReset}
                className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors font-medium"
              >
                Try Again
              </button>
              <button
                onClick={this.handleReload}
                className="flex-1 bg-gray-200 text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors font-medium"
              >
                Reload Page
              </button>
              <button
                onClick={() => (window.location.href = '/')}
                className="flex-1 bg-gray-200 text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors font-medium"
              >
                Go to Home
              </button>
            </div>

            {/* Help text */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <p className="text-sm text-gray-600">
                If this problem persists, please contact support or try:
              </p>
              <ul className="mt-2 text-sm text-gray-600 list-disc list-inside space-y-1">
                <li>Clearing your browser cache</li>
                <li>Using a different browser</li>
                <li>Checking your internet connection</li>
              </ul>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Widget-specific Error Boundary
 * Smaller fallback UI for individual widget failures
 */
export class WidgetErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
    errorCount: 0,
  };

  public static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Widget error:', error.message);
    this.setState({ errorInfo });
  }

  private resetError = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="h-full w-full flex items-center justify-center bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
          <div className="text-center">
            <svg
              className="w-8 h-8 text-red-500 mx-auto mb-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <p className="text-sm font-medium text-red-700 dark:text-red-400 mb-2">
              Widget Error
            </p>
            <button
              onClick={this.resetError}
              className="text-xs px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
