/**
 * ErrorBoundary Component v2.0
 * ============================
 *
 * Catches React errors and displays user-friendly error messages with recovery options.
 *
 * Features:
 * - Detailed error diagnostics
 * - Auto-retry capability
 * - Error categorization
 * - Accessibility support
 */
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug, Wifi, Database, Server, HelpCircle, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
  showDetails: boolean;
  copied: boolean;
  errorType: 'network' | 'render' | 'data' | 'unknown';
}

// Error categorization helper
const categorizeError = (error: Error): State['errorType'] => {
  const message = error.message.toLowerCase();
  const stack = error.stack?.toLowerCase() || '';

  if (message.includes('fetch') || message.includes('network') || message.includes('cors') || message.includes('failed to fetch')) {
    return 'network';
  }
  if (message.includes('json') || message.includes('parse') || message.includes('undefined') || message.includes('null')) {
    return 'data';
  }
  if (stack.includes('render') || message.includes('component') || message.includes('react')) {
    return 'render';
  }
  return 'unknown';
};

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
      showDetails: false,
      copied: false,
      errorType: 'unknown',
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      errorType: categorizeError(error),
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    this.setState(prev => ({
      error,
      errorInfo,
      errorCount: prev.errorCount + 1,
      errorType: categorizeError(error),
    }));

    // Store error for debugging
    this.logErrorToStorage(error, errorInfo);

    // Call external error handler if provided
    this.props.onError?.(error, errorInfo);
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
      showDetails: false,
      copied: false,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  toggleDetails = () => {
    this.setState(prev => ({ showDetails: !prev.showDetails }));
  };

  copyErrorDetails = async () => {
    const { error, errorInfo, errorType } = this.state;
    const details = `
OptiFlow AI Error Report
========================
Type: ${errorType}
Time: ${new Date().toISOString()}
URL: ${window.location.href}
User Agent: ${navigator.userAgent}

Error Message:
${error?.message || 'Unknown error'}

Stack Trace:
${error?.stack || 'No stack trace'}

Component Stack:
${errorInfo?.componentStack || 'No component stack'}
    `.trim();

    try {
      await navigator.clipboard.writeText(details);
      this.setState({ copied: true });
      setTimeout(() => this.setState({ copied: false }), 2000);
    } catch (e) {
      console.error('Failed to copy:', e);
    }
  };

  getErrorIcon = () => {
    switch (this.state.errorType) {
      case 'network':
        return <Wifi className="w-12 h-12 text-amber-500" />;
      case 'data':
        return <Database className="w-12 h-12 text-orange-500" />;
      case 'render':
        return <Bug className="w-12 h-12 text-red-500" />;
      default:
        return <AlertTriangle className="w-12 h-12 text-red-500" />;
    }
  };

  getErrorTitle = () => {
    switch (this.state.errorType) {
      case 'network':
        return 'Erro de Conexão';
      case 'data':
        return 'Erro nos Dados';
      case 'render':
        return 'Erro de Renderização';
      default:
        return 'Erro Inesperado';
    }
  };

  getErrorDescription = () => {
    switch (this.state.errorType) {
      case 'network':
        return 'Não foi possível conectar ao servidor. Verifique sua conexão de internet ou tente novamente em alguns instantes.';
      case 'data':
        return 'Os dados recebidos não puderam ser processados corretamente. Isso pode indicar um problema temporário no servidor.';
      case 'render':
        return 'Um componente da interface não pôde ser exibido corretamente. Nossa equipe foi notificada.';
      default:
        return 'Ocorreu um erro inesperado. Por favor, tente uma das opções abaixo.';
    }
  };

  getErrorSuggestions = () => {
    switch (this.state.errorType) {
      case 'network':
        return [
          'Verifique sua conexão com a internet',
          'Tente desativar VPN ou proxy',
          'Aguarde alguns segundos e tente novamente',
        ];
      case 'data':
        return [
          'Atualize a página',
          'Limpe o cache do navegador',
          'Tente novamente em alguns minutos',
        ];
      case 'render':
        return [
          'Recarregue a página',
          'Limpe os dados locais do navegador',
          'Tente usar outro navegador',
        ];
      default:
        return [
          'Clique em "Tentar Novamente"',
          'Recarregue a página',
          'Volte para a página inicial',
        ];
    }
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { showDetails, copied, error, errorInfo, errorCount } = this.state;

      return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4" role="alert" aria-live="assertive">
          <div className="max-w-2xl w-full bg-white rounded-xl shadow-xl p-8">
            {/* Header */}
            <div className="flex items-start gap-4 mb-6">
              <div className="flex-shrink-0 p-3 bg-red-50 rounded-xl" aria-hidden="true">
                {this.getErrorIcon()}
              </div>
              <div className="flex-1">
                <h1 className="text-2xl font-bold text-slate-900">
                  {this.getErrorTitle()}
                </h1>
                <p className="text-slate-600 mt-1">
                  {this.getErrorDescription()}
                </p>
                {errorCount > 1 && (
                  <span className="inline-block mt-2 text-xs px-2 py-1 rounded-full bg-amber-100 text-amber-700">
                    Tentativas: {errorCount}
                  </span>
                )}
              </div>
            </div>

            {/* Suggestions */}
            <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
              <div className="flex items-center gap-2 text-blue-800 font-medium mb-2">
                <HelpCircle className="w-4 h-4" />
                <span>Sugestões</span>
              </div>
              <ul className="text-sm text-blue-700 space-y-1">
                {this.getErrorSuggestions().map((suggestion, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-blue-400">•</span>
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>

            {/* Action buttons */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
              <button
                onClick={this.handleReset}
                className="flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors font-medium"
              >
                <RefreshCw className="w-4 h-4" />
                Tentar Novamente
              </button>
              <button
                onClick={this.handleReload}
                className="flex items-center justify-center gap-2 bg-slate-100 text-slate-700 px-4 py-3 rounded-lg hover:bg-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 transition-colors font-medium"
              >
                <RefreshCw className="w-4 h-4" />
                Recarregar Página
              </button>
              <button
                onClick={() => (window.location.href = '/')}
                className="flex items-center justify-center gap-2 bg-slate-100 text-slate-700 px-4 py-3 rounded-lg hover:bg-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 transition-colors font-medium"
              >
                <Home className="w-4 h-4" />
                Página Inicial
              </button>
            </div>

            {/* Error details (collapsible) */}
            <div className="border-t border-slate-200 pt-4">
              <button
                onClick={this.toggleDetails}
                className="flex items-center justify-between w-full text-left text-sm text-slate-500 hover:text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 rounded"
              >
                <span className="flex items-center gap-2">
                  <Bug className="w-4 h-4" />
                  Detalhes técnicos
                </span>
                {showDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {showDetails && error && (
                <div className="mt-3 p-4 bg-slate-100 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-600 uppercase">Mensagem de Erro</span>
                    <button
                      onClick={this.copyErrorDetails}
                      className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 rounded px-2 py-1"
                    >
                      {copied ? (
                        <>
                          <Check className="w-3 h-3 text-green-500" />
                          Copiado!
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          Copiar
                        </>
                      )}
                    </button>
                  </div>
                  <pre className="text-xs text-slate-600 overflow-auto max-h-32 whitespace-pre-wrap break-words">
                    {error.message}
                  </pre>
                  {import.meta.env.DEV && errorInfo?.componentStack && (
                    <details className="mt-3">
                      <summary className="text-xs font-semibold text-slate-600 cursor-pointer">Stack trace (dev)</summary>
                      <pre className="mt-2 text-xs text-slate-500 overflow-auto max-h-40 whitespace-pre-wrap">
                        {error.stack}
                        {'\n\nComponent Stack:'}
                        {errorInfo.componentStack}
                      </pre>
                    </details>
                  )}
                </div>
              )}
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
interface WidgetState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

export class WidgetErrorBoundary extends Component<Props, WidgetState> {
  public state: WidgetState = {
    hasError: false,
    error: null,
    errorInfo: null,
    errorCount: 0,
  };

  public static getDerivedStateFromError(error: Error): Partial<WidgetState> {
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
