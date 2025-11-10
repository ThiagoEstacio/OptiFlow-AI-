/**
 * Auth Redux Slice
 */
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { apiClient, getErrorMessage } from '../../api/client';
import type { User, LoginRequest } from '../../types';
import axios from 'axios';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  isTimeout: boolean;
  isNetworkError: boolean;
}

const initialState: AuthState = {
  user: null,
  token: apiClient.getToken(),
  isAuthenticated: !!apiClient.getToken(),
  loading: false,
  error: null,
  isTimeout: false,
  isNetworkError: false,
};

// Async thunks
export const login = createAsyncThunk(
  'auth/login',
  async (credentials: LoginRequest, { rejectWithValue }) => {
    try {
      const response = await apiClient.login(credentials);
      const user = await apiClient.getCurrentUser();
      return { token: response.access_token, user };
    } catch (error: any) {
      // Determine error type for better handling
      const isTimeout = axios.isAxiosError(error) && (
        error.code === 'ECONNABORTED' ||
        error.response?.status === 408 ||
        error.response?.status === 504
      );

      const isNetworkError = axios.isAxiosError(error) && (
        !error.response ||
        error.code === 'ERR_NETWORK'
      );

      return rejectWithValue({
        message: getErrorMessage(error),
        isTimeout,
        isNetworkError,
      });
    }
  }
);

export const getCurrentUser = createAsyncThunk(
  'auth/getCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      const user = await apiClient.getCurrentUser();
      return user;
    } catch (error: any) {
      const isTimeout = axios.isAxiosError(error) && (
        error.code === 'ECONNABORTED' ||
        error.response?.status === 408 ||
        error.response?.status === 504
      );

      const isNetworkError = axios.isAxiosError(error) && (
        !error.response ||
        error.code === 'ERR_NETWORK'
      );

      return rejectWithValue({
        message: getErrorMessage(error),
        isTimeout,
        isNetworkError,
      });
    }
  }
);

export const logout = createAsyncThunk('auth/logout', async () => {
  await apiClient.logout();
});

// Slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
      state.isTimeout = false;
      state.isNetworkError = false;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.isTimeout = false;
        state.isNetworkError = false;
      })
      .addCase(login.fulfilled, (state, action: PayloadAction<{ token: string; user: User }>) => {
        state.loading = false;
        state.token = action.payload.token;
        state.user = action.payload.user;
        state.isAuthenticated = true;
        state.error = null;
        state.isTimeout = false;
        state.isNetworkError = false;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        const payload = action.payload as { message: string; isTimeout: boolean; isNetworkError: boolean };
        state.error = payload?.message || 'Login failed';
        state.isTimeout = payload?.isTimeout || false;
        state.isNetworkError = payload?.isNetworkError || false;
        state.isAuthenticated = false;
      })
      // Get current user
      .addCase(getCurrentUser.pending, (state) => {
        state.loading = true;
      })
      .addCase(getCurrentUser.fulfilled, (state, action: PayloadAction<User>) => {
        state.loading = false;
        state.user = action.payload;
        state.isAuthenticated = true;
        state.error = null;
        state.isTimeout = false;
        state.isNetworkError = false;
      })
      .addCase(getCurrentUser.rejected, (state, action) => {
        state.loading = false;
        state.isAuthenticated = false;
        state.user = null;
        state.token = null;
        const payload = action.payload as { message: string; isTimeout: boolean; isNetworkError: boolean };
        state.error = payload?.message || 'Failed to get user';
        state.isTimeout = payload?.isTimeout || false;
        state.isNetworkError = payload?.isNetworkError || false;
      })
      // Logout
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.token = null;
        state.isAuthenticated = false;
        state.error = null;
        state.isTimeout = false;
        state.isNetworkError = false;
      });
  },
});

export const { clearError } = authSlice.actions;
export default authSlice.reducer;
