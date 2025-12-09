/**
 * Test Utilities
 * ==============
 *
 * Provides wrappers and utilities for testing React components
 * that require Redux, Router, and other providers.
 */
import React, { ReactElement, ReactNode } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { Provider } from 'react-redux'
import { BrowserRouter } from 'react-router-dom'
import { configureStore } from '@reduxjs/toolkit'

// Import reducers
import authReducer from '../store/slices/authSlice'
import alarmsReducer from '../store/slices/alarmsSlice'
import uiReducer from '../store/slices/uiSlice'
import tagsReducer from '../store/slices/tagsSlice'
import devicesReducer from '../store/slices/devicesSlice'
import sitesReducer from '../store/slices/sitesSlice'
import organizationsReducer from '../store/slices/organizationsSlice'

import type { RootState } from '../store'

// Type for the test store reducers
const rootReducer = {
  auth: authReducer,
  alarms: alarmsReducer,
  ui: uiReducer,
  tags: tagsReducer,
  devices: devicesReducer,
  sites: sitesReducer,
  organizations: organizationsReducer,
}

// Create a test store with optional preloaded state
export function createTestStore(preloadedState?: Partial<RootState>) {
  return configureStore({
    reducer: rootReducer,
    preloadedState: preloadedState as RootState,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: false,
      }),
  })
}

// Default initial state for testing
export const defaultTestState: Partial<RootState> = {
  auth: {
    user: null,
    isAuthenticated: false,
    loading: false,
    error: null,
    token: null,
    isTimeout: false,
    isNetworkError: false,
  },
  alarms: {
    activeAlarms: [],
    loading: false,
    error: null,
  },
  ui: {
    sidebarOpen: true,
    theme: 'light',
    notifications: [],
  },
}

interface WrapperProps {
  children: ReactNode
}

// All Providers wrapper
interface AllProvidersProps {
  children: ReactNode
  preloadedState?: Partial<RootState>
  store?: ReturnType<typeof createTestStore>
}

export function AllProviders({
  children,
  preloadedState,
  store: providedStore,
}: AllProvidersProps) {
  const store = providedStore || createTestStore(preloadedState)

  return (
    <Provider store={store}>
      <BrowserRouter>{children}</BrowserRouter>
    </Provider>
  )
}

// Custom render function with all providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  preloadedState?: Partial<RootState>
  store?: ReturnType<typeof createTestStore>
}

export function renderWithProviders(
  ui: ReactElement,
  {
    preloadedState,
    store,
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  const Wrapper = ({ children }: WrapperProps) => (
    <AllProviders preloadedState={preloadedState} store={store}>
      {children}
    </AllProviders>
  )

  return {
    store: store || createTestStore(preloadedState),
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  }
}

// Render with just Router (no Redux)
export function renderWithRouter(ui: ReactElement, options?: RenderOptions) {
  const Wrapper = ({ children }: WrapperProps) => (
    <BrowserRouter>{children}</BrowserRouter>
  )

  return render(ui, { wrapper: Wrapper, ...options })
}

// Mock user for authenticated tests
export const mockAuthenticatedUser = {
  id: 'test-user-id',
  email: 'admin@optiflow.com',
  full_name: 'Admin User',
  role: 'admin' as const,
  is_active: true,
  is_superuser: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

// Mock state for authenticated user
export const authenticatedState: Partial<RootState> = {
  ...defaultTestState,
  auth: {
    user: mockAuthenticatedUser,
    isAuthenticated: true,
    loading: false,
    error: null,
    token: 'mock-token',
    isTimeout: false,
    isNetworkError: false,
  },
}

// Re-export everything from testing-library
export * from '@testing-library/react'
export { default as userEvent } from '@testing-library/user-event'
