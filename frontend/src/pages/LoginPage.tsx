/**
 * Login Page
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useAppSelector } from '../store';
import { showErrorToast, showSuccessToast } from '../utils/toast';

export const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState('');
  const [retryCount, setRetryCount] = useState(0);
  const { login, loading } = useAuth();
  const { error, isTimeout, isNetworkError } = useAppSelector((state) => state.auth);
  const navigate = useNavigate();

  // Clear local error when user starts typing
  useEffect(() => {
    if (username || password) {
      setLocalError('');
    }
  }, [username, password]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError('');

    // Validate inputs
    if (!username.trim()) {
      setLocalError('Please enter your email');
      return;
    }

    if (!password.trim()) {
      setLocalError('Please enter your password');
      return;
    }

    try {
      const success = await login({ username, password });
      if (success) {
        showSuccessToast('Login successful!');
        navigate('/');
      } else {
        // Error will be handled by useEffect below
        setRetryCount((prev) => prev + 1);
      }
    } catch (err) {
      console.error('Login error:', err);
      setRetryCount((prev) => prev + 1);
    }
  };

  // Handle errors from auth state
  useEffect(() => {
    if (error) {
      setLocalError(error);

      // Show appropriate toast based on error type
      if (isTimeout) {
        showErrorToast(null, 'Login timed out. Please check your connection and try again.');
      } else if (isNetworkError) {
        showErrorToast(null, 'Unable to connect to server. Please check your internet connection.');
      }
    }
  }, [error, isTimeout, isNetworkError]);

  const handleRetry = () => {
    setLocalError('');
    setRetryCount(0);
    // Form will be submitted again when user clicks Sign In
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-2xl p-8">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-blue-600">OptiFlow AI</h1>
          <p className="text-gray-600 mt-2">Industrial IoT Platform</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Error Display with Retry Option */}
          {localError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start">
                <svg
                  className="h-5 w-5 text-red-500 mt-0.5 mr-3 flex-shrink-0"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <div className="flex-1">
                  <p className="text-sm text-red-700">{localError}</p>
                  {(isTimeout || isNetworkError) && retryCount > 0 && (
                    <button
                      type="button"
                      onClick={handleRetry}
                      className="mt-2 text-sm text-red-600 hover:text-red-800 underline focus:outline-none"
                    >
                      Clear error and try again
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Connection Status Indicator */}
          {isNetworkError && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <div className="flex items-center">
                <svg
                  className="h-5 w-5 text-yellow-500 mr-2"
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
                <p className="text-sm text-yellow-700">
                  Connection issue detected. Please check your internet.
                </p>
              </div>
            </div>
          )}

          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                placeholder="admin@smartport.com"
                autoComplete="username"
                required
                disabled={loading}
              />
            </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                placeholder="••••••••"
                autoComplete="current-password"
                required
                disabled={loading}
              />
            </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center"
          >
            {loading ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>

          {/* Retry hint for timeout/network errors */}
          {(isTimeout || isNetworkError) && !loading && (
            <div className="text-center">
              <p className="text-sm text-gray-600">
                Having trouble? The system will automatically retry the connection.
              </p>
            </div>
          )}
        </form>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-600">
          <p>Demo credentials:</p>
          <p className="font-mono mt-1">admin@smartport.com / Admin@123456</p>
        </div>
      </div>
    </div>
  );
};
