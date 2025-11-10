/**
 * Toast Notification Utility
 * Provides user-friendly toast notifications for different error scenarios
 */
import toast from 'react-hot-toast';
import { getErrorMessage } from '../api/client';

/**
 * Show a success toast
 */
export const showSuccessToast = (message: string) => {
  toast.success(message, {
    duration: 3000,
    position: 'top-right',
  });
};

/**
 * Show an error toast with user-friendly message
 */
export const showErrorToast = (error: any, customMessage?: string) => {
  const message = customMessage || getErrorMessage(error);
  toast.error(message, {
    duration: 5000,
    position: 'top-right',
  });
};

/**
 * Show an info toast
 */
export const showInfoToast = (message: string) => {
  toast(message, {
    duration: 4000,
    position: 'top-right',
    icon: 'ℹ️',
  });
};

/**
 * Show a loading toast (returns toast id for dismissal)
 */
export const showLoadingToast = (message: string) => {
  return toast.loading(message, {
    position: 'top-right',
  });
};

/**
 * Dismiss a specific toast
 */
export const dismissToast = (toastId: string) => {
  toast.dismiss(toastId);
};

/**
 * Update an existing toast
 */
export const updateToast = (
  toastId: string,
  type: 'success' | 'error' | 'loading',
  message: string
) => {
  if (type === 'success') {
    toast.success(message, { id: toastId });
  } else if (type === 'error') {
    toast.error(message, { id: toastId });
  } else {
    toast.loading(message, { id: toastId });
  }
};

/**
 * Show a timeout error toast
 */
export const showTimeoutToast = () => {
  toast.error('Request timed out. Please check your connection and try again.', {
    duration: 5000,
    position: 'top-right',
  });
};

/**
 * Show a network error toast
 */
export const showNetworkErrorToast = () => {
  toast.error('Unable to connect to server. Please check your internet connection.', {
    duration: 5000,
    position: 'top-right',
  });
};

/**
 * Show a server error toast
 */
export const showServerErrorToast = () => {
  toast.error('Server is temporarily unavailable. Please try again in a moment.', {
    duration: 5000,
    position: 'top-right',
  });
};

/**
 * Show a retry toast with loading state
 */
export const showRetryToast = (attemptNumber: number, maxAttempts: number) => {
  return toast.loading(`Retrying... (${attemptNumber}/${maxAttempts})`, {
    position: 'top-right',
  });
};

/**
 * Show a warning toast
 */
export const showWarningToast = (message: string) => {
  toast(message, {
    duration: 4000,
    position: 'top-right',
    icon: '⚠️',
    style: {
      background: '#F59E0B',
      color: '#fff',
    },
  });
};

/**
 * Handle API errors with appropriate toast notifications
 */
export const handleApiError = (error: any, context?: string) => {
  const errorMessage = getErrorMessage(error);
  const contextMessage = context ? `${context}: ${errorMessage}` : errorMessage;
  showErrorToast(error, contextMessage);
};

// Legacy export for backward compatibility
export const showToast = {
  success: showSuccessToast,
  error: (message: string) => toast.error(message),
  loading: showLoadingToast,
  dismiss: dismissToast,
  promise: <T,>(
    promise: Promise<T>,
    msgs: {
      loading: string;
      success: string;
      error: string;
    }
  ) => {
    return toast.promise(promise, msgs);
  },
};

export default {
  success: showSuccessToast,
  error: showErrorToast,
  info: showInfoToast,
  loading: showLoadingToast,
  dismiss: dismissToast,
  update: updateToast,
  timeout: showTimeoutToast,
  networkError: showNetworkErrorToast,
  serverError: showServerErrorToast,
  retry: showRetryToast,
  warning: showWarningToast,
  handleApiError,
};
