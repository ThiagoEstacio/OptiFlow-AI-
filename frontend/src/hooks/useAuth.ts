/**
 * Authentication Hook
 */
import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import { login as loginAction, logout as logoutAction, getCurrentUser } from '../store/slices/authSlice';
import type { LoginRequest } from '../types';

export const useAuth = () => {
  const dispatch = useAppDispatch();
  const { user, isAuthenticated, loading, error } = useAppSelector((state) => state.auth);

  useEffect(() => {
    if (isAuthenticated && !user) {
      dispatch(getCurrentUser());
    }
  }, [isAuthenticated, user, dispatch]);

  const login = async (credentials: LoginRequest) => {
    const result = await dispatch(loginAction(credentials));
    return !result.type.endsWith('/rejected');
  };

  const logout = () => {
    dispatch(logoutAction());
  };

  return {
    user,
    isAuthenticated,
    loading,
    error,
    login,
    logout,
  };
};
