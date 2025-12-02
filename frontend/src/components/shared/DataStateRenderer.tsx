/**
 * DataStateRenderer Component
 * ============================
 * Reusable component for rendering loading, error, and empty states.
 * Consolidates 10+ duplicate implementations across the codebase.
 */

import React from 'react';
import {
  Loader2,
  AlertCircle,
  RefreshCw,
  Inbox,
  SearchX,
  FileQuestion,
  ServerCrash,
  WifiOff,
} from 'lucide-react';

// ============================================================================
// Loading State
// ============================================================================

interface LoadingStateProps {
  /** Loading message */
  message?: string;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Whether to show as inline or full container */
  inline?: boolean;
  /** Additional CSS classes */
  className?: string;
}

const LOADING_SIZES = {
  sm: { spinner: 'w-4 h-4', text: 'text-sm' },
  md: { spinner: 'w-8 h-8', text: 'text-base' },
  lg: { spinner: 'w-12 h-12', text: 'text-lg' },
};

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Carregando...',
  size = 'md',
  inline = false,
  className = '',
}) => {
  const sizeClasses = LOADING_SIZES[size];

  if (inline) {
    return (
      <span className={`inline-flex items-center gap-2 text-gray-500 ${className}`}>
        <Loader2 className={`${sizeClasses.spinner} animate-spin`} />
        <span className={sizeClasses.text}>{message}</span>
      </span>
    );
  }

  return (
    <div className={`flex flex-col items-center justify-center py-12 ${className}`}>
      <Loader2 className={`${sizeClasses.spinner} animate-spin text-blue-500`} />
      <p className={`mt-4 text-gray-500 ${sizeClasses.text}`}>{message}</p>
    </div>
  );
};

// ============================================================================
// Error State
// ============================================================================

type ErrorType = 'generic' | 'network' | 'server' | 'notFound';

interface ErrorStateProps {
  /** Error message to display */
  message?: string;
  /** Error type for icon selection */
  type?: ErrorType;
  /** Retry callback */
  onRetry?: () => void;
  /** Whether retry is in progress */
  isRetrying?: boolean;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Additional CSS classes */
  className?: string;
}

const ERROR_ICONS: Record<ErrorType, React.FC<{ className?: string }>> = {
  generic: AlertCircle,
  network: WifiOff,
  server: ServerCrash,
  notFound: FileQuestion,
};

const ERROR_SIZES = {
  sm: { icon: 'w-6 h-6', text: 'text-sm', button: 'text-sm px-3 py-1' },
  md: { icon: 'w-10 h-10', text: 'text-base', button: 'text-base px-4 py-2' },
  lg: { icon: 'w-14 h-14', text: 'text-lg', button: 'text-lg px-5 py-2.5' },
};

export const ErrorState: React.FC<ErrorStateProps> = ({
  message = 'Ocorreu um erro ao carregar os dados.',
  type = 'generic',
  onRetry,
  isRetrying = false,
  size = 'md',
  className = '',
}) => {
  const Icon = ERROR_ICONS[type];
  const sizeClasses = ERROR_SIZES[size];

  return (
    <div className={`flex flex-col items-center justify-center py-12 ${className}`}>
      <div className="rounded-full bg-red-100 p-4">
        <Icon className={`${sizeClasses.icon} text-red-500`} />
      </div>
      <p className={`mt-4 text-gray-700 ${sizeClasses.text} text-center max-w-md`}>
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          disabled={isRetrying}
          className={`
            mt-4 inline-flex items-center gap-2 rounded-lg
            bg-blue-500 text-white hover:bg-blue-600
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-colors ${sizeClasses.button}
          `}
        >
          <RefreshCw className={`w-4 h-4 ${isRetrying ? 'animate-spin' : ''}`} />
          {isRetrying ? 'Tentando...' : 'Tentar novamente'}
        </button>
      )}
    </div>
  );
};

// ============================================================================
// Empty State
// ============================================================================

type EmptyType = 'noData' | 'noResults' | 'noItems';

interface EmptyStateProps {
  /** Title for the empty state */
  title?: string;
  /** Description message */
  message?: string;
  /** Empty state type for icon selection */
  type?: EmptyType;
  /** Action button label */
  actionLabel?: string;
  /** Action callback */
  onAction?: () => void;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Additional CSS classes */
  className?: string;
  /** Custom icon */
  icon?: React.ReactNode;
}

const EMPTY_ICONS: Record<EmptyType, React.FC<{ className?: string }>> = {
  noData: Inbox,
  noResults: SearchX,
  noItems: FileQuestion,
};

const EMPTY_TITLES: Record<EmptyType, string> = {
  noData: 'Nenhum dado disponível',
  noResults: 'Nenhum resultado encontrado',
  noItems: 'Nenhum item encontrado',
};

const EMPTY_MESSAGES: Record<EmptyType, string> = {
  noData: 'Os dados ainda não foram carregados ou não há informações para exibir.',
  noResults: 'Tente ajustar os filtros ou a busca para encontrar o que procura.',
  noItems: 'Não há itens para exibir no momento.',
};

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  message,
  type = 'noData',
  actionLabel,
  onAction,
  size = 'md',
  className = '',
  icon,
}) => {
  const Icon = EMPTY_ICONS[type];
  const sizeClasses = ERROR_SIZES[size]; // Reuse error sizes

  return (
    <div className={`flex flex-col items-center justify-center py-12 ${className}`}>
      <div className="rounded-full bg-gray-100 p-4">
        {icon || <Icon className={`${sizeClasses.icon} text-gray-400`} />}
      </div>
      <h3 className={`mt-4 font-medium text-gray-700 ${sizeClasses.text}`}>
        {title || EMPTY_TITLES[type]}
      </h3>
      <p className={`mt-2 text-gray-500 text-center max-w-md ${size === 'sm' ? 'text-xs' : 'text-sm'}`}>
        {message || EMPTY_MESSAGES[type]}
      </p>
      {onAction && actionLabel && (
        <button
          onClick={onAction}
          className={`
            mt-4 inline-flex items-center gap-2 rounded-lg
            bg-blue-500 text-white hover:bg-blue-600
            transition-colors ${sizeClasses.button}
          `}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};

// ============================================================================
// Combined Data State Renderer
// ============================================================================

interface DataStateRendererProps<T> {
  /** Data to check */
  data: T | null | undefined;
  /** Loading state */
  loading: boolean;
  /** Error message */
  error: string | null;
  /** Content to render when data is available */
  children: React.ReactNode | ((data: T) => React.ReactNode);
  /** Custom loading component */
  loadingComponent?: React.ReactNode;
  /** Custom error component */
  errorComponent?: React.ReactNode;
  /** Custom empty component */
  emptyComponent?: React.ReactNode;
  /** Retry callback for error state */
  onRetry?: () => void;
  /** Whether retry is in progress */
  isRetrying?: boolean;
  /** Function to check if data is empty */
  isEmpty?: (data: T) => boolean;
  /** Loading message */
  loadingMessage?: string;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Additional CSS classes */
  className?: string;
}

export function DataStateRenderer<T>({
  data,
  loading,
  error,
  children,
  loadingComponent,
  errorComponent,
  emptyComponent,
  onRetry,
  isRetrying,
  isEmpty,
  loadingMessage,
  size = 'md',
  className = '',
}: DataStateRendererProps<T>) {
  // Loading state
  if (loading && !data) {
    return loadingComponent || (
      <LoadingState message={loadingMessage} size={size} className={className} />
    );
  }

  // Error state
  if (error) {
    return errorComponent || (
      <ErrorState
        message={error}
        onRetry={onRetry}
        isRetrying={isRetrying}
        size={size}
        className={className}
      />
    );
  }

  // Empty state
  const isDataEmpty = isEmpty
    ? isEmpty(data as T)
    : !data || (Array.isArray(data) && data.length === 0);

  if (isDataEmpty) {
    return emptyComponent || (
      <EmptyState size={size} className={className} />
    );
  }

  // Render children with data
  if (typeof children === 'function') {
    return <>{children(data as T)}</>;
  }

  return <>{children}</>;
}

export default DataStateRenderer;
