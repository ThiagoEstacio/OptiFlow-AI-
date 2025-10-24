/**
 * Authentication Hook
 */
import { useState, useEffect, useCallback } from 'react';
import api from '../api/client';
import { API_ENDPOINTS } from '../api/config';
import type { LoginCredentials, AuthTokens, User } from '../types';

interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

export const useAuth = (): UseAuthReturn => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAuthenticated = !!user;

  // Load user from localStorage on mount
  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          // TODO: Fetch user profile
          // For now, just set authenticated
          setIsLoading(false);
        } catch (err) {
          console.error('Failed to load user:', err);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setIsLoading(false);
        }
      } else {
        setIsLoading(false);
      }
    };

    loadUser();
  }, []);

  // Login
  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);

      const response = await api.post<AuthTokens>(API_ENDPOINTS.LOGIN, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const { access_token, refresh_token } = response.data;

      // Store tokens
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      // TODO: Fetch user profile
      // For now, set a mock user
      setUser({
        id: '1',
        email: credentials.username,
        username: credentials.username,
        is_active: true,
        is_superuser: false,
        created_at: new Date().toISOString(),
      });

      setIsLoading(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
      setIsLoading(false);
      throw err;
    }
  }, []);

  // Logout
  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  }, []);

  // Refresh token
  const refreshToken = useCallback(async () => {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) {
      throw new Error('No refresh token');
    }

    try {
      const response = await api.post<AuthTokens>(API_ENDPOINTS.REFRESH, {
        refresh_token: refresh,
      });

      const { access_token } = response.data;
      localStorage.setItem('access_token', access_token);
    } catch (err) {
      logout();
      throw err;
    }
  }, [logout]);

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    refreshToken,
  };
};
